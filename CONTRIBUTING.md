# Contributing to Open Tsume

> Data policy: see `docs/data-policy.md`. Summary — allowed sources are
> only archives operated by the national government (e.g. NDL); direct
> reading/transcription from NDL primary sources is the rule. Prohibited:
> (1) any board/diagram/record/image acquisition or reference from personal
> sites (wakwak, oohasi, open-tsume, etc.), (2) any data acquisition from
> non-government organizations including the Japan Shogi Association
> (shogi.or.jp, etc.).

## Ground rules (will be enforced in review and CI)

1. **National-government archives only.** Transcribe by direct reading
   from primary-source scans held by archives operated by the national
   government (e.g. NDL digital collections). University/public libraries,
   private institutions, societies, and other non-national holdings are
   not permitted without a policy revision. Record the archive,
   identifier, and page. This rule takes precedence as defined in
   `docs/data-policy.md` (§§1–4 prevail on any conflict).
2. **No scraping of modern sites, books, or apps.** No pasting of modern
   commentaries, essays, diagrams, or solution texts. Since 2026-09-16,
   third-party KIF files and shogi websites are **not used at all** —
   not even as typing aids. All new transcriptions must be read directly
   from the primary-source scans. (The zukou/musou Stage-1 records are
   labeled as reference transcriptions pending collation; see
   docs/provenance.md.)
3. **No provenance-unknown data.** "SFEN I found online" is rejected.
4. **Never edit the original.** Put corrections in `corrected_sfen` with
   `correction_note`. `sfen` is immutable once collated.
5. **Two-track recording: `intended_*` vs `solution_*`.** New and updated
   records keep the two lines separate (see `docs/provenance.md`,
   `docs/methodology.md` §Intended vs canonical, `docs/validation.md`):
   - `intended_solution_usi` / `intended_solution_moves` /
     `intended_solution_source` = intended line (原典翻刻): the solution
     text as read from the primary-source scan (e.g. 詰手書 columns),
     transcribed into USI. Guarantees legality replay only; mate and
     shortest-ness are never claimed on this side. `null` USI +
     `intended_solution_source` progress note (e.g. NDL PID / canvas /
     column range, USI化未了) is a legitimate intermediate state.
   - `solution_usi` / `solution_moves` = canonical line (検証解): the
     engine-checked mating line that `tools/validate.py` walks and
     mate-checks. Only this side carries the mate claim.
   - Never copy a solver / validator output into `intended_*`.
     `intended_*` comes only from direct reading of the scan cited in
     `intended_solution_source`.
6. **Mark uncertainty; keep `needs_manual_review` until collated.** If a
   reading is unsure, keep `verification.needs_manual_review: true` and
   explain in `notes`. Validator success and solver crosscheck alone do
   **not** clear this flag. It is cleared only after a human collates the
   record against the national-government archive scan and fills
   `source.page` (see `docs/provenance.md` Two-stage transcription).
   On lineage mismatch between the transcribed intended line and the
   solver-verified canonical line, keep both tracks, explain in `notes` +
   `verification.method`, keep `needs_manual_review: true`, and never
   rewrite `sfen` to force agreement (see `docs/validation.md`
   Mismatch handling).
7. **Solver crosscheck is verification only.** Mate-search crosscheck
   (e.g. YaneuraOu mate search) confirms the `solution_usi` side; it is
   never a transcription source and never substitutes for direct reading.
   Record engine name + version, run date, search command/conditions, and
   result in `verification.method` (and `notes` on mismatch/futile
   findings). A futile-interposition finding does not promote a line to
   verified: keep `status.solution_verified: false` + note until a
   mate-search determination is recorded (see `docs/validation.md`,
   `docs/research.md` §§9–10).
8. **CI must pass**: record check, SFEN check, solution-legality check,
   final-mate check, intended-solution legality check (skipped when USI
   is `null`), provenance check. `needs_manual_review: true` is a
   warning, not a failure.

## Workflow

1. Pick an untranscribed number; read board + solution text directly
   from the primary-source scans. Third-party KIF files and shogi
   websites are not used at all — not even as typing aids (see Ground
   rule 2 and `docs/data-policy.md` §4). No KIF-input converter is
   provided; new records are written directly in SFEN/USI.
2. Add `collections/<era>/<collection>/problems/NNN.json` following
   `schema/problem.schema.json` and an existing record as a template.
   Fill the two tracks separately: board (`sfen`) + intended
   transcription (`intended_solution_usi` / `intended_solution_source`
   with NDL PID / canvas e.g. R number / column range and progress
   state) from direct reading; canonical line (`solution_usi`) as the
   mating line to be machine-checked. Record who/when in
   `verification.transcribed_by` / `transcribed_from` /
   `transcribed_date` as available. Never record personal or
   non-government URLs in `verification.reference_urls`
   (`docs/data-policy.md` §4).
3. Run `python3 tools/validate.py <file>` and `python3 tests/run_tests.py`.
   When `intended_solution_usi` is present it must pass the legality
   replay; when `null`, only `intended_solution_source` documents
   progress. If available, run the YaneuraOu-class mate-search
   crosscheck on `solution_usi` and record tool/version/date/command/
   result in `verification.method` (+ `notes` on mismatch or futile
   findings) per Ground rule 7.
4. Open a pull request. CI validates; a human collates against the
   archive scan before `needs_manual_review` may be cleared. Keep
   `needs_manual_review: true` while board collation is pending, even
   if `status.intended_solution_verified` or the solver check passes.

## What the verification flags mean (do not overclaim)

- `status.solution_verified: true` = **single-line guarantee only, not a
  complete solution** (see `docs/validation.md`): the recorded
  `solution_usi` replays legally from `sfen`, every sente move gives
  check, every recorded gote reply resolves the check, and the final
  position is mate with zero legal gote replies on that line. It does
  **not** cover off-line gote alternatives, longest-defense /
  shortest-mate claims, or absence of alternate solutions (yozume).
  `status.unique_solution_verified` stays `false` in v1.
- `status.intended_solution_verified: true` = the transcribed intended
  line replays legally from `sfen`. No mate / continuous-check /
  shortest-ness claim. Grant only after (a) USI present with matching
  move count, (b) local `tools/validate.py` legality replay passes,
  (c) exact read source (PID / canvas / columns + progress) recorded in
  `intended_solution_source` by the transcriber/collator who did the
  direct reading. Full collation is not required, but
  `needs_manual_review` stays `true` until board collation completes.
  Write `false` explicitly while unverified. Full criteria:
  `docs/validation.md` (`status.intended_solution_verified` — granting
  criteria). Independent of solver verification on the solution side.

## License agreement

By contributing you agree that dataset records are released under
CC0 1.0 and code under MIT. Do not submit material you do not have the
right to release under these terms.
