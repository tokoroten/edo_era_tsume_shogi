# Provenance

Every problem must be traceable along this chain:

```text
Edo-period original
↓ national-government archive (e.g. NDL)
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
- `verification.reference_urls` — national-government archive pages used
  **only** for collation support (clearly labeled; never the provenance
  root). URLs outside national-government archives must not be recorded
  (see `docs/data-policy.md` §4). Pre-existing records that name other
  references are legacy pending NDL re-collation (see below) — do not
  add new ones.
- `verification.needs_manual_review` — `true` until a human collates the
  record against the national-government archive scan. The existing 200
  records remain `needs_manual_review: true` pending NDL re-collation;
  the data itself is untouched by this documentation fix.

## Two-stage transcription (honest labeling)

> Policy note: `docs/data-policy.md` takes precedence. Since 2026-09-16,
> new transcriptions must be read directly from national-government
> archive scans. Transcription from modern KIF / reference files,
> including use as a typing aid, is prohibited for new work.

Stage 1 — **legacy reference transcription (no longer permitted for new
contributions)**: the existing records were mechanically transcribed
from clearly-labeled collation references. No commentary, essays, or
diagrams were copied. Records in this stage keep
`verification.needs_manual_review: true` and
`verification.transcribed_from` names the reference file, pending
re-collation against NDL scans. **They are not
"transcribed from the original".** Do not create new Stage-1 records;
do not add new `reference_urls` outside national-government archives.

Stage 2 — **collation against the original**: a human compares the record
with the national-government archive scan (e.g. NDL), fills `source.page`,
and only then may clear `needs_manual_review`. The viewer marks uncollated records.

The primary source in `source.*` is the provenance root and the collation
target; any legacy reference in `verification.*` is not the root and does
not substitute for direct reading of the scan. The existing 200 records
stay `needs_manual_review: true` until NDL re-collation is complete;
this documentation change does not modify the data.

## Intended vs canonical lines (two-track provenance)

- `intended_solution_usi` / `intended_solution_moves` /
  `intended_solution_source` record the **intended line (原典翻刻)**:
  the solution text as read from the primary-source scan (e.g. the
  詰手書 columns), transcribed into USI. `intended_solution_source`
  names the transcription basis (NDL PID / canvas / column range and
  progress state such as USI化未了・くずし未確定あり). Like all
  transcriptions, it must come from direct reading of
  national-government archive scans (`docs/data-policy.md` §1–§4);
  no personal or non-government source may appear there.
  The intended line guarantees **legality replay only** — mate and
  shortest-ness are not claimed.
- `solution_usi` / `solution_moves` record the **canonical line
  (検証済み正解)**: the engine-checked mating line. Its provenance is
  the software-validation step of the chain above (tool, version, date,
  result in `verification.*`), and mate claims rest on this side only.
- A `intended_solution_source` string without USI (USI `null`) is a
  legitimate intermediate state: it documents that honkoku collation is
  under way, not a solution assertion. Viewer and validator treat it as
  未翻刻 (skip legality replay, show source note only).
- On lineage mismatch (e.g. zukou No.20: canonical 37-move line vs
  詰手書二十番翻刻 NDL PID:861212 R0000008-9 and zukou board PID:861211
  R0000015): keep both tracks, record the collated PIDs/columns and the
  disagreement in `notes` + `verification.method`, keep
  `needs_manual_review: true`, and isolate a betsuden (別伝) record only
  when an independent transmission is positively identified. See
  `docs/validation.md` for the full mismatch procedure.
- `status.intended_solution_verified` may be set to `true` only by the
  transcriber / collator who directly read the national-government
  archive scan cited in `intended_solution_source` (PID / canvas /
  column range required), and only when the transcribed
  `intended_solution_usi` passes the `tools/validate.py` legality
  replay. Full record collation (`source.page` +
  `needs_manual_review: false`) is not required, but the PID / canvas /
  column citation is. Unverified records SHOULD write `false`
  explicitly (absent is treated as `false`). The flag is independent of
  solver verification on the `solution_usi` side and never asserts mate.
  Full criteria: `docs/validation.md`
  (`status.intended_solution_verified` — granting criteria). All
  sources must satisfy `docs/data-policy.md` §§1–4.

## Rules

1. A record whose only basis is "SFEN found online" is rejected by CI.
   `source.identifier` or a concrete archive `source.url` is required.
2. Modern commentary (themes, essays, variations) is never copied into
   records. Move sequences established by our own transcription and
   engine-checked are facts, not prose.
3. Corrections go to `corrected_sfen` + `correction_note`; the transcribed
   original in `sfen` is immutable.
