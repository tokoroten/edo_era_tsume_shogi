# Provenance

Every problem must be traceable along this chain:

```text
Edo-period original
↓ digital archive (NDL, university library, public archive)
↓ volume / page / problem number
↓ transcription (who, from what source, how, when)
↓ machine-readable form (SFEN / USI)
↓ software validation (tool, version, date, result)
↓ Open Tsume record
```

## Recorded fields

- `source.title` — original title (e.g. 将棋図巧)
- `source.repository` — archive (e.g. 国立国会図書館)
- `source.identifier` — permanent ID when available
  (e.g. NDL BibID `000000493927`, call number `209-461`)
- `source.page` — volume/page/problem location (`null` until collated
  against the scans; the collation task fills this in)
- `source.url` — archive URL (accessed date goes in `docs/research.md`
  and the commit message, not in every record)
- `source.edition` — edition/copy when variants exist
  (e.g. Muso献上本 vs 享保版刷次 — see docs/research.md §1.2)
- `verification.transcribed_by` / `transcribed_from` / `transcribed_date`
- `verification.reference_urls` — secondary sources used **only** for
  collation (clearly labeled; never the provenance root)
- `verification.needs_manual_review` — `true` until a human collates the
  record against the original archive image

## Two-stage transcription (honest labeling)

Stage 1 — **reference transcription**: board facts and main-line moves are
mechanically transcribed from a clearly-labeled collation reference
(modern KIF). No commentary, essays, or diagrams are copied. Records in
this stage keep `verification.needs_manual_review: true` and
`verification.transcribed_from` names the reference file. **They are not
"transcribed from the original".**

Stage 2 — **collation against the original**: a human compares the record
with the archive scan (NDL etc.), fills `source.page`, and only then may
clear `needs_manual_review`. The viewer marks uncollated records.

The primary source in `source.*` is the provenance root and the collation
target; the reference in `verification.*` is a typing aid, never the root.

## Rules

1. A record whose only basis is "SFEN found online" is rejected by CI.
   `source.identifier` or a concrete archive `source.url` is required.
2. Modern commentary (themes, essays, variations) is never copied into
   records. Move sequences established by our own transcription and
   engine-checked are facts, not prose.
3. Corrections go to `corrected_sfen` + `correction_note`; the transcribed
   original in `sfen` is immutable.
