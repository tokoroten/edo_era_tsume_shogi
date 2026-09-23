#!/usr/bin/env python3
"""build_draft_images.py — publish NDL source canvases for drafts on the web.

For every (PID, RID) cited by collections/edo/*/drafts/*.json, downscale
the temp-workspace full image to width 1024 and write
web/images/<PID>_<RID>.jpg with attribution in web/images/SOURCES.md.

Policy: docs/image-policy.md (PDM internet-public only, self-hosted,
no hotlink). Temp images live outside the repo; only the downscaled
derivatives are committed. RIDs without a temp source are skipped with
a warning (fetch on demand per docs/data-acquisition.md).
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = r"C:\Users\shinta\AppData\Local\Temp\opencode\ndl_full"
OUT = os.path.join(ROOT, "web", "images")
WIDTH = 1024


def main():
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    canvas_count = {"861197": 58, "861198": 31,
                    "861193": 40, "861194": 31}
    used = {}
    for p in sorted(glob.glob(os.path.join(
            ROOT, "collections", "edo", "*", "drafts", "*.json"))):
        rec = json.load(open(p, encoding="utf-8"))
        blob = (rec["source"].get("page", "") + " "
                + rec["verification"].get("transcribed_from", "") + " "
                + (rec.get("intended_solution_source") or ""))
        for pid in ("861197", "861198", "861193", "861194"):
            for rid in set(re.findall(r"R\d{7}", blob)):
                # R numbers are shared text: keep only RIDs that exist
                # as canvases of this PID (docs/data-acquisition.md §5).
                if int(rid[1:]) < 1 or int(rid[1:]) > canvas_count[pid]:
                    continue
                used.setdefault((pid, rid), set()).add(rec["id"])
    ok, missing = [], []
    for (pid, rid), ids in sorted(used.items()):
        src = os.path.join(WORK, "ndl_" + pid, f"{int(rid[1:]):03d}.jpg")
        dst = os.path.join(OUT, f"{pid}_{rid}.jpg")
        if not os.path.exists(src):
            missing.append((pid, rid, sorted(ids)))
            continue
        im = Image.open(src)
        if im.width > WIDTH:
            im = im.resize((WIDTH, int(im.height * WIDTH / im.width)),
                           Image.LANCZOS)
        im.save(dst, quality=82)
        ok.append((pid, rid, sorted(ids)))
    with open(os.path.join(OUT, "SOURCES.md"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("# web/images sources\n\n")
        f.write("All files are downscaled derivatives of National Diet Library\n"
                "Digital Collections scans (internet-public, PDM).\n")
        f.write("Originals: `https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/full/full/0/default.jpg`.\n")
        f.write("Attribution: 国立国会図書館デジタルコレクションより（Public Domain 転載）.\n")
        f.write("Transcription data: CC0-1.0. Viewer code: MIT.\n\n")
        for pid, rid, ids in ok:
            f.write(f"- {pid}_{rid}.jpg: {', '.join(ids)}\n")
        if missing:
            f.write("\n## RIDs cited but not fetched (no image published)\n\n")
            for pid, rid, ids in missing:
                f.write(f"- {pid} {rid}: {', '.join(ids)}\n")
    print(f"wrote {len(ok)} images, missing {len(missing)}")
    for m in missing[:20]:
        print("  MISSING:", m)


if __name__ == "__main__":
    main()
