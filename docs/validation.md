# Validation

Validator: `tools/validate.py` (Python 3, standard library only, MIT).
Run: `python3 tools/validate.py <problem.json> [...]` or the full suite
`python3 tests/run_tests.py`. CI runs both on every pull request.

## Checks (v1)

1. **Record validation** — required fields, types, `id`/`collection_id`/
   `number` consistency, `solution_moves` odd and equal to
   `len(solution_usi)`, `rights` = Public Domain / CC0-1.0, `source`
   has archive identifier or URL (else: provenance failure).
2. **SFEN validation** — parses; exactly one gote king on board;
   per-type totals (board + both hands) within the 40-piece set;
   sente hand countable; recomputed gote box matches the SFEN hand
   (when recorded).
3. **Position rules** — no nifu (two unpromoted sente pawns on one file)
   in the initial position; no dead-square pieces that could never move
   (flagged as errors; classical exceptions would need an explicit note).
4. **Solution validation** — sente moves first and alternates; each USI
   move is pseudo-legal and leaves no own-king exposure; drops obey
   hand counts, nifu, and dead squares; promotion flags consistent with
   the promotion zone.
5. **Mate validation** — after the final ply it is gote's turn, the gote
   king is in check, and gote has **zero** legal replies, where replies
   include king moves, captures, blocks, and drops from the full box.
6. **Provenance validation** — `needs_manual_review` is surfaced
   (warning, not failure) so uncollated records stay visible.

## Known limitations (explicitly out of scope for v1)

- **No yozume (alternate-solution) search** — needs a full-width solver.
- **No longest-defense check** for gote replies off the main line.
- **No uchi-fu-zume (pawn-drop mate) foul detection** on the final move.
- Hence `status.unique_solution_verified` remains `false` everywhere.

## Roadmap

- Adopt `tsshogi` (MIT) for cross-validation of SFEN legality and KIF
  round-trips; adopt a df-pn based OSS tsume solver (cf. tanuki-tsume-shogi)
  for yozume / longest-defense proofs. See `docs/research.md` §5.2.
