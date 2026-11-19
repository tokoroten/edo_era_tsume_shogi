#!/usr/bin/env python3
"""Fetch an arbitrary NDL IIIF crop for transcription work.

Examples:
  python tools/iiif_crop.py --pid 861217 --rid R0000002 \
      --region pct:40.8,16,4.8,66 --width 900 --out s1_c1.jpg
  python tools/iiif_crop.py --pid 861192 --rid R0000021 --region full \
      --width 1600 --out colophon.jpg

Region accepts IIIF region syntax ("full", "pct:x,y,w,h", "x,y,w,h").
Width is the requested output width in pixels (height follows the aspect).

The NDL IIIF endpoint requires the canvas RID, not just the PID:
  https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/<region>/<width>,/0/default.jpg
"""
import argparse
import io
import os
import sys
import urllib.request

UA = {"User-Agent": "edo-tsume-repro/1.0"}


def build_url(pid, rid, region, width):
    return "https://dl.ndl.go.jp/api/iiif/%s/%s/%s/%d,/0/default.jpg" % (
        pid, rid, region, width)


def fetch(pid, rid, region, width, timeout=180):
    url = build_url(pid, rid, region, width)
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=timeout).read()
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pid", required=True)
    ap.add_argument("--rid", required=True)
    ap.add_argument("--region", default="full",
                    help='IIIF region: "full", "pct:x,y,w,h", "x,y,w,h"')
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args(argv)

    if not args.rid.startswith("R"):
        print("warning: RID usually looks like R0000002", file=sys.stderr)
    try:
        data = fetch(args.pid, args.rid, args.region, args.width,
                     args.timeout)
    except Exception as e:
        print("fetch failed: %s" % e, file=sys.stderr)
        print("url: %s" % build_url(args.pid, args.rid, args.region,
                                    args.width), file=sys.stderr)
        return 1

    d = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(d, exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(data)
    try:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as im:
            print("%s  %dx%d  %d bytes" % (args.out, im.width, im.height,
                                           len(data)))
    except Exception:
        print("%s  %d bytes" % (args.out, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
