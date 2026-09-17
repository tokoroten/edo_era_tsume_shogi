# Validation

Validator: `tools/validate.py` (Python 3, standard library only, MIT).
Run: `python3 tools/validate.py <problem.json> [...]` or the full suite
`python3 tests/run_tests.py`. CI runs both on every pull request.

## Checks (v1)

1. **Record validation** — required fields, types, `id`/`collection_id`/
   `number` consistency, `solution_moves` odd and equal to
   `len(solution_usi)`, `rights` = Public Domain / CC0-1.0, `source`
   has archive identifier or URL (else: provenance failure).
2. **SFEN validation** — parses; exactly one gote king on board;
   per-type totals (board + both hands) within the 40-piece set;
   sente hand countable; recomputed gote box matches the SFEN hand
   (when recorded).
3. **Position rules** — no nifu (two unpromoted sente pawns on one file)
   in the initial position; no dead-square pieces that could never move
   (flagged as errors; classical exceptions would need an explicit note).
4. **Solution validation** — sente moves first and alternates; each USI
   move is pseudo-legal and leaves no own-king exposure; drops obey
   hand counts, nifu, and dead squares; promotion flags consistent with
   the promotion zone.
5. **Mate validation** — after the final ply it is gote's turn, the gote
   king is in check, and gote has **zero** legal replies, where replies
   include king moves, captures, blocks, and drops from the full box.
6. **Provenance validation** — `needs_manual_review` is surfaced
   (warning, not failure) so uncollated records stay visible.
7. **Intended-solution validation (legality only)** —
   `intended_solution_usi` / `intended_solution_moves` /
   `intended_solution_source` / `status.intended_solution_verified`
   (see `_validate_intended_solution` in `tools/validate.py`):
   when `intended_solution_usi` is `null`/absent the check is skipped
   (a `intended_solution_source` string alone records transcription
   progress and is allowed); when present, every entry must match USI
   syntax, `intended_solution_moves` (when present) must equal
   `len(intended_solution_usi)`, and each move must replay legally from
   `sfen` in order. Continuous check and final mate are **not** required
   on this side. Solver verification (mate proof, futile-interposition
   analysis, `exhaustive_mate_in_1`) applies to `solution_usi` only.

## `status.intended_solution_verified` — granting criteria

`true` asserts only that the transcribed intended line replays legally
from `sfen`. It makes no mate / continuous-check / shortest-ness claim.
The flag is asserted by a human and checked by the machine; CI never
sets it automatically.

1. **Granting conditions (all required for `true`)** —
   (a) `intended_solution_usi` is present as a non-empty USI list and
   `intended_solution_moves` (when present) equals its length;
   (b) `_validate_intended_solution` in `tools/validate.py` passes with
   zero errors: every entry matches USI syntax and replays legally in
   order from `sfen` (legality only; continuous check and final mate
   are not required);
   (c) the transcriber records the exact source actually read in
   `intended_solution_source`: national-government archive PID /
   canvas (R number) / column range and progress state (e.g.
   `NDL PID:861212 R0000008-9`), plus who/when in
   `verification.transcribed_by` / `transcribed_from` /
   `transcribed_date` as available. Only direct reading of
   national-government archive scans counts (`docs/data-policy.md`
   §§1–4); personal sites and non-government bodies may not appear.
   Who may set `true`: the transcriber or collator who performed (c),
   after confirming (b) locally; CI then re-checks (b).
2. **Relation to collation** — full record collation (`source.page`
   filled, `verification.needs_manual_review` cleared) is **not**
   required for `true`. An intended-text-only collation (solution
   columns read and cited) may grant `true` while board collation is
   still pending. In that case `needs_manual_review` stays `true` and
   the cited PID / canvas / columns in `intended_solution_source`
   (+ `notes` / `verification.method` on mismatch) are mandatory so a
   later full collation remains possible.
3. **`false` / absent handling** — absent is treated as unverified
   (`false`) by `tools/validate.py` and `tools/build_web.py`, but
   authors SHOULD write `false` explicitly while unverified so the
   state is visible in the record. `true` without
   `intended_solution_usi` is a validator error; a present USI that
   fails the legality replay must stay `false` until fixed or
   re-transcribed.
4. **Independence from solver verification (solution side)** —
   `intended_solution_verified` is orthogonal to
   `status.solution_verified` / `unique_solution_verified` and to mate
   proof / futile-interposition analysis, which concern `solution_usi`
   only. `true` on the intended side never supports a mate claim and
   never satisfies solution-side checks; `false` on the intended side
   never blocks solution verification.

## `status.solution_verified` — single-line guarantee (not a complete solution)

`status.solution_verified: true` asserts only a **linear guarantee**
for the recorded `solution_usi` as replayed from `sfen` by
`tools/validate.py` (see the solution walk and mate test in
`tools/validate.py`): the line alternates starting with sente, every
USI move is legal (including drop and promotion rules), every sente
move gives check, every recorded gote reply resolves the check, and
the final position is mate with gote to move — gote in check with
**zero** legal replies on that line, including interpositions and
drops from the box. It does **not** assert a complete solution.

In particular, `solution_verified` does **not** cover:

- all gote alternatives at intermediate plies off the recorded line
  (full-branch correspondence is not checked);
- longest-defense / shortest-mate claims;
- absence of alternate solutions (yozume) — that remains
  `status.unique_solution_verified`, which stays `false` in v1
  (see Known limitations below).

Example (scope illustration): zukou-050 — the recorded 9-ply main
line satisfies the linear guarantee above (legal, continuous check,
final mate), while the complete solution covering all gote
variations is 21 plies. The 9 vs 21 difference is the gap between a
single verified mating line and a fully branched complete solution.

Establishing a complete solution is a separate process requiring a
mate-search engine (e.g. YaneuraOu and similar mate search) and is
out of scope for the v1 validator. A dedicated `complete_solution`
field may be introduced in the future to record fully branched
solutions; it is not defined or checked in v1.

This definition changes no source requirements;
`docs/data-policy.md` §§1–4 continue to apply unchanged.

## Solver crosscheck record template (`verification.method`)

`solver` による照合を行った場合、`verification.method` への記録は
自由文ではなく以下の定型順序で書く。省略時は `none` / `記載なし` と
明示し、空欄のままにしない。

1. **engine** — engine名・版（commitを含む）。例:
    `engine=example-mate-engine v1.2.3 (commit abc1234)`。
    配布元URL・解説記事URL等は書かない。
2. **date** — 実行日（`YYYY-MM-DD`）。例: `date=2026-09-16`。
3. **command / conditions** — コマンドと探索条件。
    `go mate` の持ち時間（ms）、`Hash`、`Threads`、`DepthLimit`
    （上限なしの場合は `none`）をすべて書く。
4. **result** — `checkmate <N>手` / `nomate` / `timeout` / `none` の
    いずれか1つ。`checkmate` の場合は `solution_usi` との一致・不一致
    を併記する。`PV要約`（先頭数手＋最終手。長い場合は `...` で中略）
    を付す。
5. **handling** — 結果の取扱い。`solution不変` / `solution要検討` と
    `notes追記要` / `notes追記不要` を必ず書く。solver結果のみで
    `sfen` を書き換えない（訂正は `corrected_sfen` +
    `correction_note` に従う）。

書式（1行、順序固定）:

```text
[solver] engine=<name version (commit hash)>; date=<YYYY-MM-DD>; command="<command>"; Hash=<size>, Threads=<n>, DepthLimit=<n|none>; result=<checkmate N手|nomate|timeout|none> (<solution_usiとの一致・不一致>); PV=<PV要約>; handling=<solution不変|solution要検討>・<notes追記要|notes追記不要>
```

記載例:

```text
[solver] engine=example-mate-engine v1.2.3 (commit abc1234); date=2026-09-16; command="go mate 5000"; Hash=256MB, Threads=1, DepthLimit=none; result=checkmate 9手 (solution_usiと一致); PV=7g7f 3a4b ... 5e5d# (先頭2手＋最終手); handling=solution不変・notes追記不要
```

本テンプレは検証手段の記録であり、データ取得元ではない。
`source.*` の provenance rootを変更せず、NDL一次資料からの直接読解の
原則を置き換えない（`docs/data-policy.md` §§1–4は変更なし）。
`verification.reference_urls` 等に個人サイト・非政府団体のURLを
記録しない。engine名・版・commitの文字列のみとし、外部URLは
一切付さない。

## Mismatch handling (e.g. zukou No.20)

When the transcribed intended line (原典翻刻) and the solver-verified
canonical line (solution) disagree in lineage — e.g. zukou-020, where the
current 37-move canonical line is lineage-mismatched against the 詰手書
No.20 transcription (NDL PID:861212 R0000008-9, all 5 columns) and the
zukou No.20 board (PID:861211 R0000015) — the record is **retained with
a warning note, not deleted or overwritten**:

1. Keep `solution_usi` (verified mate) unchanged; keep `intended_*` as
   the transcription state (`null` USI + `intended_solution_source`
   progress note while USI化未了).
2. Record the mismatch in `notes` and `verification.method` (which PIDs /
   columns were collated, what disagrees, 別伝・別番・転写違いの疑い).
3. Keep `verification.needs_manual_review: true` until re-collation
   against the scans resolves it.
4. **別伝隔離条件**: isolate into a separate betsuden (別伝) record only
   when an independent lineage is positively identified (distinct
   board / distinct solution text attributable to another transmission);
   mere mismatch or undeciphered kuzushi stays as a warning on the same
   record. `sfen` itself is never rewritten to force agreement
   (corrections follow `corrected_sfen` + `correction_note`).

## Known limitations (explicitly out of scope for v1)

- **No yozume (alternate-solution) search** — needs a full-width solver.
- **No longest-defense check** for gote replies off the main line.
- **No uchi-fu-zume (pawn-drop mate) foul detection** on the final move.
- Hence `status.unique_solution_verified` remains `false` everywhere.

## Roadmap

- Adopt `tsshogi` (MIT) for cross-validation of SFEN legality and KIF
  round-trips; adopt a df-pn based OSS tsume solver (cf. tanuki-tsume-shogi)
  for yozume / longest-defense proofs. See `docs/research.md` §5.2.
