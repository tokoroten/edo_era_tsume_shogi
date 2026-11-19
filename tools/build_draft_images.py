#!/usr/bin/env python3
"""build_draft_images.py — publish NDL source canvases for drafts on the web.

For every (PID, RID) cited by collections/*/*/drafts/*.json, downscale the
temp-workspace image to width 1024 and write web/images/<PID>_<RID>.jpg with
attribution in web/images/SOURCES.md.

Citation parsing is PID-scoped: an RID only belongs to the PID named by the
nearest preceding "PID:<n>" token in the same field. (An earlier version
matched bare RIDs against every known PID and mis-attributed ids across
collections.)

Policy: docs/image-policy.md (PDM internet-public only, self-hosted,
no hotlink). Temp images live outside the repo; only the downscaled
derivatives are committed. RIDs without a temp source are skipped with a
warning (fetch on demand per docs/data-acquisition.md).
"""
import glob
import json
import os
import re
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("NDL_IMAGE_CACHE") or os.path.join(
    tempfile.gettempdir(), "opencode", "ndl_full")
OUT = os.path.join(ROOT, "web", "images")
WIDTH = 1024

CANVAS_COUNT = {"861197": 58, "861198": 31,
                "861193": 40, "861194": 31,
                "861216": 57, "861217": 28,
                "861191": 32, "861192": 22}

PID_RID = re.compile(r"PID:(\d{6})\s*(R\d{7})")
BARE_RID = re.compile(r"R\d{7}")


def cited_pairs(rec):
    """(PID, RID) pairs named by this draft, PID-scoped."""
    fields = [
        rec["source"].get("page", "") or "",
        rec["verification"].get("transcribed_from", "") or "",
        rec.get("intended_solution_source") or "",
    ]
    pairs = set()
    for text in fields:
        tokens = list(PID_RID.finditer(text))
        for m in tokens:
            pid = m.group(1)
            if pid in CANVAS_COUNT:
                pairs.add((pid, m.group(2)))
        if not tokens:
            continue
        # RIDs appearing after the last "PID:<n>" token still belong to it
        last = tokens[-1]
        for m in BARE_RID.finditer(text, last.end()):
            if last.group(1) in CANVAS_COUNT:
                pairs.add((last.group(1), m.group(0)))
    return pairs


def main():
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    used = {}
    for p in sorted(glob.glob(os.path.join(
            ROOT, "collections", "*", "*", "drafts", "*.json"))):
        rec = json.load(open(p, encoding="utf-8"))
        for pid, rid in cited_pairs(rec):
            if not (1 <= int(rid[1:]) <= CANVAS_COUNT[pid]):
                continue
            used.setdefault((pid, rid), set()).add(rec["id"])

    written, kept, missing = [], [], []
    for (pid, rid), ids in sorted(used.items()):
        src = os.path.join(WORK, "ndl_" + pid, "%03d.jpg" % int(rid[1:]))
        dst = os.path.join(OUT, "%s_%s.jpg" % (pid, rid))
        if os.path.exists(src):
            im = Image.open(src)
            if im.width > WIDTH:
                im = im.resize((WIDTH, int(im.height * WIDTH / im.width)),
                               Image.LANCZOS)
            im.save(dst, quality=82)
            written.append((pid, rid, sorted(ids)))
        elif os.path.exists(dst):
            kept.append((pid, rid, sorted(ids)))
        else:
            missing.append((pid, rid, sorted(ids)))

    published = {}
    for name in sorted(os.listdir(OUT)):
        if not name.endswith(".jpg"):
            continue
        pid, rid = name[:-4].split("_", 1)
        published[(pid, rid)] = sorted(used.get((pid, rid), []))
    orphan = sorted(k for k in published if k not in used)

    with open(os.path.join(OUT, "SOURCES.md"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write("# web/images sources\n\n")
        f.write("All files are downscaled derivatives of National Diet Library\n"
                "Digital Collections scans (internet-public, PDM).\n")
        f.write("Originals: `https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/full/full/0/default.jpg`.\n")
        f.write("Attribution: 国立国会図書館デジタルコレクションより（Public Domain 転載）.\n")
        f.write("Transcription data: CC0-1.0. Viewer code: MIT.\n\n")
        for (pid, rid), ids in sorted(published.items()):
            f.write("- %s_%s.jpg: %s\n"
                    % (pid, rid, ", ".join(ids) if ids else "（引用元draft不明）"))
        if missing:
            f.write("\n## RIDs cited but not fetched (no image published)\n\n")
            for pid, rid, ids in missing:
                f.write("- %s %s: %s\n" % (pid, rid, ", ".join(ids)))
        if orphan:
            f.write("\n## 公開済みだが現在どのdraftからも引用されていない画像\n\n")
            for pid, rid in orphan:
                f.write("- %s_%s.jpg\n" % (pid, rid))
    print("written %d, kept %d, missing %d, published %d, orphan %d"
          % (len(written), len(kept), len(missing), len(published), len(orphan)))
    for m in missing[:10]:
        print("  MISSING:", m[0], m[1], m[2][:4])


if __name__ == "__main__":
    main()
