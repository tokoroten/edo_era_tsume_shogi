#!/usr/bin/env python3
"""ndl_fetch.py — systematic NDL IIIF download (stdlib only, MIT).

Follows docs/data-acquisition.md §§2-3: official IIIF Image API only,
temp workspace (never commit images), polite waits with backoff,
and §3.3 verification (non-zero size, JPEG SOI/EOI markers, no gaps).

Usage:
    python3 tools/ndl_fetch.py --pid 861197 --start 1 --end 58 --work-dir <DIR>
    python3 tools/ndl_fetch.py --pid 861197 --start 1 --end 58 --work-dir <DIR> --size 1024,
    python3 tools/ndl_fetch.py --pid 861197 --rid R0000031 --work-dir <DIR>

Rate-limit experience (2026-09-23): >120 consecutive `full` fetches
trigger HTTP 403; pause and resume with --wait 3 --retries 5.
"""
import argparse
import os
import sys
import time
import urllib.error
import urllib.request

UA = "edo-tsume-repro/1.0"


def fetch(url, dest, wait, retries):
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as resp, \
                    open(dest, "wb") as f:
                f.write(resp.read())
            return None
        except Exception as e:  # noqa: BLE001 - retry whatever NDL returns
            err = f"{type(e).__name__}: {str(e)[:80]}"
            print(f"  attempt {attempt} failed: {err}", file=sys.stderr)
            if attempt == retries:
                return err
            time.sleep(wait * attempt)
    return "unreachable"


def verify(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        return f"unreadable: {e}"
    if not data:
        return "zero bytes"
    if data[:2] != b"\xff\xd8" or data[-2:] != b"\xff\xd9":
        return "bad JPEG markers"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", required=True)
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=None)
    ap.add_argument("--rid", default=None,
                    help="single RID like R0000031 (overrides --start/--end)")
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--size", default="full")
    ap.add_argument("--wait", type=float, default=3.0)
    ap.add_argument("--retries", type=int, default=5)
    args = ap.parse_args(argv)

    if args.rid:
        numbers = [int(args.rid[1:])]
    else:
        if args.end is None:
            ap.error("--end is required without --rid")
        numbers = list(range(args.start, args.end + 1))

    outdir = os.path.join(args.work_dir, "ndl_" + args.pid)
    os.makedirs(outdir, exist_ok=True)
    got, skipped, failed = 0, 0, []
    for n in numbers:
        dest = os.path.join(outdir, f"{n:03d}.jpg")
        if os.path.exists(dest) and verify(dest) is None:
            skipped += 1
            continue
        rid = f"R{n:07d}"
        url = (f"https://dl.ndl.go.jp/api/iiif/{args.pid}/{rid}/full/"
               f"{args.size}/0/default.jpg")
        err = fetch(url, dest, args.wait, args.retries)
        if err is None:
            verr = verify(dest)
            if verr is None:
                got += 1
            else:
                failed.append((n, verr))
        else:
            failed.append((n, err))
        time.sleep(args.wait)
    print(f"pid={args.pid}: got={got} cached={skipped} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
