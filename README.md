# Open Tsume — Public-domain tsume-shogi dataset

[日本語](README.ja.md)

**Open Tsume** is an open dataset of Edo-period tsume-shogi (mate problems)
whose copyrights have expired. Every problem is traceable to its primary
source, stored in machine-readable formats (SFEN / USI / KIF / JSON), and
checked by software validation.

- 🎯 Not tied to any single game or service. Free for games, web services,
  shogi software, engine tests, LLM/AI benchmarks, research, education,
  redistribution, and derived datasets.
- 📜 Original works: **Public Domain** (e.g. Ito Kanju, *Shogi Zuko*, 1755).
- 🗃️ This project's machine-readable records: **CC0 1.0** (see LICENSE-DATA).
- 🛠️ Validation/conversion code: **MIT License** (see LICENSE-CODE).

## Status

- *Shogi Zuko* (Ito Kanju, 1755): all 100 problems transcribed and
  validator-checked (`tools/validate.py`). Each record carries a canonical
  verified line (`solution_usi`) with `status.solution_verified` as a
  single-line guarantee only (legal moves, continuous check, final mate on
  that recorded line — not a complete branched solution; see
  `docs/validation.md`). Former futile-interposition notes (026/073/093)
  are retained in per-record `notes`; where every remaining reply allows
  immediate mate-in-1 they are recorded as verified.
  `status.unique_solution_verified` remains `false` (no yozume search in v1).
- *Shogi Musou* (Ito Sokanz III, 1734): all 100 problems transcribed and
  validator-checked. Same single-line guarantee applies. Former
  futile-interposition notes (028/031/037/043) are retained; 031/037 overlap
  with the imperfect works cited in the literature (edition/transmission
  identification is future work).
- *Shogi Gyokuzu* (Kuwahara Kimimasa, 1836): `drafts/` holds 100 drafts
  (`collections/edo/gyokuzu/drafts/001.json` … `100.json`) against the
  target 100 (`collection.json` `problem_count: 100`). Cho framework is
  fixed (upper 50 cho / lower 28 cho, 100 figures + 100 procedures → 100
  problems; see `docs/research.md` §1.5); individual `source.page` cho fill
  remains pending (`丁未確定` maintained; see
  `docs/gyokuzu-transcription.md` §4, §7.5残件3). `?` squares remain
  (no zero-`?` draft; e.g. 099 `?=29`, 100 `?=33`); sengo (sente/gote
  orientation) first pass completed 2026-09-17 over all 100 drafts
  (`notes` records per `docs/gyokuzu-transcription.md` §7.4–§7.5, SFEN-unchanged
  principle with high-confidence-only updates, e.g. 098 `?=21→20`, 099
  `?=29` unchanged, 100 `?=33` unchanged); intended-line USI rate
  0% (`intended_solution_usi: null` 100/100) and canonical-line rate 0%
  (`solution_usi: []` 100/100). Promotion to `problems/` is 0
  (`problems/` does not exist; `problems_transcribed: []`); drafts are
  staging and never counted as promoted. All 100 drafts keep
  `needs_manual_review: true`. Details: `docs/gyokuzu-transcription.md` §6–§7,
  `docs/research.md` §1.5.
- *Shogi Kinza* (Fukushima Junki, NDL publication year missing so
  `published_year: 1800` is provisional): `drafts/` holds 54 drafts
  (`collections/edo/kinza/drafts/001.json` … `054.json`) against the
  target 54 (`collection.json` `problem_count: 54`: first volume 1–28 +
  main 29–50 + appendix 1–4). Individual cho fill remains pending
  (`丁未確定` maintained; see `docs/kinza-transcription.md` §3–§4). Board SFEN remain the all-`?` placeholder
  (no diagrams, mojifu undeciphered); intended-line USI rate 0%
  (`intended_solution_usi: null` 54/54) and canonical-line rate 0%
  (`solution_usi: []` 54/54). Promotion to `problems/` is 0
  (`problems/` does not exist; `problems_transcribed: []`). All 54 drafts
  keep `needs_manual_review: true`. Details:
  `docs/kinza-transcription.md` §7.
- Two-track solutions: `solution_*` = verified canonical line (mate guarantee
  on that line); `intended_*` = historical transcription (原典翻刻, legality
  replay only, `null` USI while pending). E.g. zukou-020 keeps
  `intended_solution_source` (NDL PID / canvas / columns) with null USI plus
  a lineage-mismatch warning. The viewer renders 想定解法 / 検証解 separately.
- Solver crosscheck: when applied, recorded in `verification.method`
  following the fixed template in `docs/validation.md` (engine / date /
  conditions / result / handling). It never rewrites `sfen`; corrections go
  to `corrected_sfen` + `correction_note`. Scope example: zukou-050 — the
  recorded 9-ply main line satisfies the single-line guarantee while the
  fully branched complete solution is 21 plies.
- Edition control (Zuko): two layers recorded in
  `collections/edo/zukou/collection.json` `edition_note` — Layer A: 1821
  (Bunsei 4) colophon / Hokurindo; Layer B: Meiji Yoshikawa Hanshichi reprint
  series. Until final edition identification, all records keep
  `needs_manual_review: true`.
- All 200 promoted records (Zuko + Muso) carry `needs_manual_review: true`
  until collated against national-government archive scans, and all 154
  drafts (Gyokuzu 100 + Kinza 54) likewise keep `needs_manual_review: true`.
  Records are Stage-1 reference
  transcriptions (board facts + main lines only, no commentary); see
  `docs/provenance.md`, `docs/data-policy.md`, `docs/data-acquisition.md`.

## Repository layout

```text
edo_era_tsume_shogi/
├── README.md / README.ja.md
├── LICENSE-DATA (CC0-1.0) / LICENSE-CODE (MIT)
├── CONTRIBUTING.md
├── docs/            research.md, methodology.md, copyright.md,
│                    provenance.md, validation.md,
│                    data-policy.md, data-acquisition.md
├── collections/edo/
│   ├── zukou/collection.json + problems/001.json … (100)
│   ├── musou/collection.json + problems/001.json … (100)
│   ├── gyokuzu/collection.json + drafts/001.json … (100, staging; problems/ none)
│   └── kinza/collection.json + drafts/001.json … (54, staging; problems/ none)
├── schema/problem.schema.json    # JSON Schema (incl. intended_* fields)
├── tools/
│   ├── validate.py               # stdlib-only validator (schema/SFEN/solution/mate + intended legality)
│   └── build_web.py              # generate Pages KIF/JSON/viewer index from canonical USI/SFEN
├── tests/run_tests.py            # unittest suite (runs validator over dataset)
├── web/                          # GitHub Pages kifu viewer (static, no deps)
└── .github/workflows/ci.yml      # schema + SFEN + solution + provenance checks
```

## Data model (per problem)

- `id` (e.g. `zukou-001`), `collection_id`, `number`
- `sfen` — canonical position (side to move always `b`; sente hand in
  capitals + gote box in lowercase)
- `solution_usi` / `solution_moves` — canonical verified line (検証解):
  the solver-checked mating line the validator walks and mate-checks
- `intended_solution_usi` / `intended_solution_moves` /
  `intended_solution_source` — intended line (想定解法・原典翻刻):
  the solution text as read from the primary-source scan, transcribed to
  USI. Nullable while pending (`null` USI + source progress note is a
  legitimate intermediate state). Legality replay only; mate is not claimed
- `status` — object `{position_verified, solution_verified,
  unique_solution_verified, intended_solution_verified}`.
  `solution_verified: true` asserts only the single-line guarantee
  (legal, continuous check, final mate with zero replies on that line —
  no claim over off-line gote alternatives, longest defense, or yozume;
  see `docs/validation.md`). `unique_solution_verified` stays `false`
  in v1. `intended_solution_verified` asserts legality replay of the
  intended line only
- `verification` — method, tool, date, reference URLs, `needs_manual_review`.
  Solver crosschecks (if any) are recorded in `method` per the template in
  `docs/validation.md`
- `source` — original title, repository (NDL), identifier, page, URL, edition.
  `edition` carries the two-layer control (Zuko 1821 colophon vs Meiji
  reprint; Muso transmission variants)
- `rights` — `{original_work: Public Domain, dataset_record: CC0-1.0}`
- `corrected_sfen` (+ `correction_note`) — kept `null` unless a corrected
  edition exists; the original is never overwritten

See `schema/problem.schema.json`, `docs/methodology.md`, and
`docs/validation.md`.

## Use it

```bash
git clone https://github.com/tokoroten/edo_era_tsume_shogi.git
python3 tools/validate.py collections/edo/zukou/problems/001.json
python3 tests/run_tests.py
```

Browse the kifu on [GitHub Pages](https://tokoroten.github.io/edo_era_tsume_shogi/) (static viewer + downloadable KIF/JSON).

## Provenance

```text
Edo-period original
↓ national-government archive (e.g. NDL)
↓ volume / page / problem number
↓ transcription (who, from what, how)
↓ machine-readable form (SFEN/USI, two tracks: intended vs solution)
↓ software validation (+ solver crosscheck where applied)
↓ Open Tsume
```

Details: `docs/provenance.md`. Data acquisition is national-archives-only
per `docs/data-policy.md`; NDL IIIF reproduction steps: `docs/data-acquisition.md`.
Records not yet collated against the original scans carry
`verification.needs_manual_review: true` and are visibly marked in the viewer.

## Contributing

See CONTRIBUTING.md. Key rules:

- National-government archives only (e.g. NDL). No scraping of modern
  sites/books. No data of unknown provenance. See `docs/data-policy.md`.
- Transcribe by direct reading of the primary-source scans in
  national-government archives (e.g. NDL); record the source.
  Third-party KIF files are not used.
- Keep the two tracks apart: `intended_*` (transcription, legality only) vs
  `solution_*` (verified mate line). Never overwrite `sfen` (original); put
  fixes in `corrected_sfen` + `correction_note`.
- Solver results go to `verification.method` (template) + `notes`; they never
  rewrite `sfen` by themselves.
- CI must pass (schema, SFEN, solution legality, final mate, provenance).
