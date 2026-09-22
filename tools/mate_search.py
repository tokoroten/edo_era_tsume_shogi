#!/usr/bin/env python3
"""mate_search.py — memory-bounded tsume mate search (stdlib only, MIT).

Tsume rule: sente (attacker, side to move 'b') must give check every move.
Gote (defender) tries any legal reply. A mating line exists when every
gote reply subtree ends in mate within the ply budget.

Memory safety (32GB box, 16C/32T shared with other work):
  - Transposition table is a plain dict capped at --max-table entries.
    When full, the search stops adding (no eviction churn) and reports
    table_full=true instead of growing without bound.
  - Node counter capped at --max-nodes; timeout enforced via deadline.
  - No engine, no external binary, no large hash allocation up front.
  - Parallel driver uses processes with small per-worker caps so total
    RSS stays far below 32GB (each worker holds only its own table).

Usage:
    python3 tools/mate_search.py <record.json> [--max-plies 15 --timeout 60
        --max-nodes 2000000 --max-table 200000]
    python3 tools/mate_search.py --batch collections/edo/gyokuzu/drafts/008.json ...
    python3 tools/mate_search.py --batch-all-free  # auto-picks ?-free drafts

Exit code 0 when the run finished (any result). Results are printed as
one JSON object per record on stdout and NOT written into the records
(the solver never rewrites sfen; record updates follow
docs/validation.md solver template by a human).
"""
import concurrent.futures
import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import validate  # noqa: E402


def board_key(bd):
    return (tuple(sorted((f, r, c, k, p) for (f, r), (c, k, p) in bd.sq.items())),
            tuple(sorted((k, n) for k, n in bd.hand["b"].items())),
            tuple(sorted((k, n) for k, n in bd.hand["w"].items())),
            bd.side)


class Search:
    def __init__(self, max_plies, timeout, max_nodes, max_table):
        self.max_plies = max_plies
        self.deadline = time.monotonic() + timeout
        self.max_nodes = max_nodes
        self.max_table = max_table
        self.nodes = 0
        self.table = {}
        self.table_full = False
        self.timed_out = False
        self.peak_table = 0

    def out_of_budget(self):
        if self.timed_out:
            return True
        if self.nodes >= self.max_nodes:
            return True
        if time.monotonic() > self.deadline:
            self.timed_out = True
            return True
        return False

    def memo_put(self, key, depth, value):
        if len(self.table) >= self.max_table:
            self.table_full = True
            return
        self.table[key] = (depth, value)
        if len(self.table) > self.peak_table:
            self.peak_table = len(self.table)

    def sente_checks(self, bd):
        """Legal sente moves that give check (tsume first-move rule)."""
        out = []
        for u in validate.gen_replies(bd):
            t = bd.clone()
            if validate.apply_usi(t, u) is not None:
                continue
            ksq = validate.find_king(t, t.side)
            if ksq is not None and validate.is_attacked(t, ksq, validate.opp(t.side)):
                out.append(u)
        return out

    def dfs(self, bd, depth):
        """Returns (status, pv): status True = sente mates within `depth`
        plies covering EVERY gote reply; False = proven nomate in budget;
        None = unknown (timeout/node cap/table-full skip or internal
        inconsistency — never claimed as a result).
        bd.side: 'b' (OR node, sente checks) or 'w' (AND node, all replies).
        """
        self.nodes += 1
        if self.out_of_budget():
            return None, None
        if bd.side == "b":
            if depth <= 0:
                return False, None
            key = (board_key(bd), depth)
            hit = self.table.get(key)
            if hit is not None and hit[0] >= depth:
                return hit[1]
            unknown = self.timed_out or self.nodes >= self.max_nodes
            for u in self.sente_checks(bd):
                t = bd.clone()
                if validate.apply_usi(t, u) is not None:
                    continue  # generated move failed to apply; skip it
                if validate.is_mate(t):
                    self.memo_put(key, depth, (True, [u]))
                    return True, [u]
                st, sub = self.dfs(t, depth - 1)
                if st is True:
                    self.memo_put(key, depth, (True, [u] + sub))
                    return True, [u] + sub
                if st is None:
                    unknown = True
            if unknown:
                return None, None
            self.memo_put(key, depth, (False, None))
            return False, None
        else:
            replies = validate.gen_replies(bd)
            if not replies:
                # gote to move with no replies: mate iff in check
                ksq = validate.find_king(bd, bd.side)
                if ksq is not None and validate.is_attacked(bd, ksq, validate.opp(bd.side)):
                    return True, []
                return False, None
            pv_line = None
            for u in replies:
                t = bd.clone()
                err = validate.apply_usi(t, u)
                if err is not None:
                    # gen_replies emitted a move that does not apply:
                    # internal inconsistency -> unknown, never success.
                    return None, None
                st, sub = self.dfs(t, depth - 1)
                if st is None:
                    return None, None
                if st is False:
                    return False, None
                if pv_line is None:
                    pv_line = [u] + sub
            return True, (pv_line if pv_line is not None else [])


def solve_file(path, max_plies=15, timeout=60, max_nodes=2000000, max_table=200000):
    rec = json.load(open(path, encoding="utf-8"))
    sfen = rec.get("sfen", "")
    res = {"id": rec.get("id"), "file": os.path.basename(path),
           "sfen": sfen, "q": sfen.count("?")}
    if "?" in sfen:
        res.update({"result": "skip", "reason": "sfen has ? (untranscribed)"})
        return res
    bd, errs = validate.parse_sfen(sfen)
    if errs:
        res.update({"result": "skip", "reason": "; ".join(errs)})
        return res
    if bd.side != "b":
        res.update({"result": "skip", "reason": "side to move is not b"})
        return res
    t0 = time.monotonic()
    best_pv = None
    outcome = "nomate"
    stats = {}
    # iterative deepening over odd plies (sente mates on odd ply)
    for depth in range(1, max_plies + 1, 2):
        s = Search(depth, max(timeout, 0.1), max_nodes, max_table)
        # share nothing between depths (bounded); report deepest stats
        st, pv = s.dfs(bd.clone(), depth)
        stats = {"depth": depth, "nodes": s.nodes,
                 "peak_table": s.peak_table, "table_full": s.table_full,
                 "timed_out": s.timed_out,
                 "elapsed_s": round(time.monotonic() - t0, 2)}
        if st is True:
            best_pv = pv
            outcome = "checkmate"
            break
        if st is None:
            outcome = "timeout" if (s.timed_out or s.nodes >= max_nodes) else "unknown"
            if outcome == "timeout":
                best_pv = None
                break
            continue
    res.update({"result": outcome, "pv": best_pv, "stats": stats,
                "budget": {"max_plies": max_plies, "timeout_s": timeout,
                           "max_nodes": max_nodes, "max_table": max_table}})
    return res


def main(argv):
    max_plies, timeout, max_nodes, max_table = 15, 60, 2000000, 200000
    workers = 4
    paths = []
    i = 0
    batch_free = False
    while i < len(argv):
        a = argv[i]
        if a == "--max-plies":
            max_plies = int(argv[i + 1]); i += 2
        elif a == "--timeout":
            timeout = float(argv[i + 1]); i += 2
        elif a == "--max-nodes":
            max_nodes = int(argv[i + 1]); i += 2
        elif a == "--max-table":
            max_table = int(argv[i + 1]); i += 2
        elif a == "--workers":
            workers = int(argv[i + 1]); i += 2
        elif a == "--batch-all-free":
            batch_free = True; i += 1
        elif a.startswith("--"):
            print(f"unknown option {a}", file=sys.stderr); return 2
        else:
            paths.append(a); i += 1
    if batch_free:
        for pat in ("collections/edo/*/drafts/*.json",):
            for p in sorted(glob.glob(os.path.join(ROOT, pat))):
                try:
                    r = json.load(open(p, encoding="utf-8"))
                except Exception:
                    continue
                if "?" not in r.get("sfen", "?") and not r.get("solution_usi"):
                    paths.append(p)
    if not paths:
        print("no target files", file=sys.stderr)
        return 2
    # Memory guard: per-worker table * workers stays small.
    # Each table entry ~ <1KB; 200k entries ~ tens of MB per worker.
    workers = max(1, min(workers, len(paths), 8))
    est_mb = workers * max_table / 1024 * 0.5
    print(f"# workers={workers} est_table_mem~{est_mb:.0f}MB (cap {max_table}/worker)",
          file=sys.stderr)
    results = []
    if len(paths) == 1 or workers == 1:
        for p in paths:
            results.append(solve_file(p, max_plies, timeout, max_nodes, max_table))
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(solve_file, p, max_plies, timeout,
                              max_nodes, max_table): p for p in paths}
            for f in concurrent.futures.as_completed(futs):
                try:
                    results.append(f.result())
                except Exception as e:  # never crash the batch
                    results.append({"file": os.path.basename(futs[f]),
                                    "result": "error", "reason": str(e)})
    results.sort(key=lambda d: d.get("id", d.get("file", "")))
    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
