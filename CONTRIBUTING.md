# Contributing to Open Tsume

## Ground rules (will be enforced in review and CI)

1. **Public-domain primary sources only.** Transcribe from NDL digital
   collections, university/public archives, or other public-domain
   originals. Record the archive, identifier, and page.
2. **No scraping of modern sites, books, or apps.** No pasting of modern
   commentaries, essays, diagrams, or solution texts. Modern KIF files may
   be used as *collation references* (listed in
   `verification.reference_urls`) but are never the provenance root and
   are never redistributed here.
3. **No provenance-unknown data.** "SFEN I found online" is rejected.
4. **Never edit the original.** Put corrections in `corrected_sfen` with
   `correction_note`. `sfen` is immutable once collated.
5. **Mark uncertainty.** If a reading is unsure, keep
   `verification.needs_manual_review: true` and explain in `notes`.
6. **CI must pass**: record check, SFEN check, solution-legality check,
   final-mate check, provenance check.

## Workflow

1. Pick an untranscribed number; transcribe board + solution from the
   primary source (use `tools/kif2open.py` only as a typing aid — the
   primary source stays authoritative).
2. Add `collections/<era>/<collection>/problems/NNN.json` following
   `schema/problem.schema.json` and an existing record as a template.
3. Run `python3 tools/validate.py <file>` and `python3 tests/run_tests.py`.
4. Open a pull request. CI validates; a human collates against the
   archive scan before `needs_manual_review` may be cleared.

## License agreement

By contributing you agree that dataset records are released under
CC0 1.0 and code under MIT. Do not submit material you do not have the
right to release under these terms.
