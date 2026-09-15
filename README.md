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
  engine-checked — 97 with final mate proven, 3 (026/073/093) recorded as
  futile-interposition candidates pending solver confirmation.
- *Shogi Musou* (Ito Sokanz III, 1734): all 100 problems transcribed and
  engine-checked — 96 with final mate proven, 4 (028/031/037/043) recorded
  as futile-interposition candidates. Note 31/37 overlap with the
  imperfect works cited in the literature.
- All records carry `needs_manual_review: true` until collated against the
  original archive scans. Records are Stage-1 reference transcriptions
  (board facts + main lines only, no commentary); see docs/provenance.md.

## Repository layout

```text
open-tsume/
├── README.md / README.ja.md
├── LICENSE-DATA (CC0-1.0) / LICENSE-CODE (MIT)
├── CONTRIBUTING.md
├── docs/            research.md, methodology.md, copyright.md,
│                    provenance.md, validation.md
├── collections/edo/zukou/
│   ├── collection.json
│   └── problems/001.json …       # one JSON per problem (canonical data)
├── schema/problem.schema.json    # JSON Schema for problem records
├── tools/
│   ├── validate.py               # stdlib-only validator (schema/SFEN/solution/mate)
│   └── kif2open.py               # KIF -> Open Tsume JSON converter (tooling)
├── tests/run_tests.py            # unittest suite (runs validator over dataset)
├── web/                          # GitHub Pages kifu viewer (static, no deps)
└── .github/workflows/ci.yml      # schema + SFEN + solution + provenance checks
```

## Data model (per problem)

- `id` (e.g. `zukou-001`), `collection_id`, `number`
- `sfen` — canonical position (side to move always `b`; sente hand in
  capitals + gote box in lowercase)
- `solution_usi` — canonical solution as USI moves (`7g7f`, `P*3d`, `...+`)
- `solution_moves` — plies (odd number, mate by sente)
- `status` — `position_verified` / `solution_verified` /
  `unique_solution_verified`
- `verification` — method, tool, date, reference URLs, `needs_manual_review`
- `source` — original title, repository (NDL), identifier, page, URL, edition
- `rights` — `{original_work: Public Domain, dataset_record: CC0-1.0}`
- `corrected_sfen` — kept `null` unless a corrected edition exists;
  the original is never overwritten

See `schema/problem.schema.json` and `docs/methodology.md`.

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
↓ digital archive (NDL etc.)
↓ volume / page / problem number
↓ transcription (who, from what, how)
↓ machine-readable form (SFEN/USI)
↓ software validation
↓ Open Tsume
```

Details: `docs/provenance.md`. Records not yet collated against the
original scans carry `verification.needs_manual_review: true` and are
visibly marked in the viewer.

## Contributing

See CONTRIBUTING.md. Key rules:

- No scraping of modern sites/books. No data of unknown provenance.
- Transcribe from public-domain primary sources; record the source.
- Never overwrite `sfen` (original); put fixes in `corrected_sfen`.
- CI must pass (schema, SFEN, solution legality, final mate, provenance).
