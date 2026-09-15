# Methodology

## Position representation (SFEN for tsume)

We follow the USI/SFEN definition (http://hgm.nubati.net/usi.html):

- Board: 9 ranks separated by `/`, first rank = gote side (rank 1).
  Files run 9 → 1 left to right. Sente pieces uppercase, gote lowercase,
  promoted pieces prefixed with `+`.
- Side to move: always `b` in this dataset (the attacker moves first).
- Hands: sente hand (uppercase) followed by gote hand (lowercase), in
  R-B-G-S-N-L-P order, `-` when empty.
- Ply: `1` (initial attack position).

Tsume-specific rule: the gote hand recorded in SFEN is the **box**
(komabako) — all pieces not on the board and not in the sente hand —
because tsume rules let the defender interpose any remaining piece.
`tools/validate.py` recomputes the box and cross-checks it.

If the box is unknown, record `-` and explain in `notes`.

## Solution representation

- Canonical: `solution_usi`, e.g. `["5d5d", ...]` is wrong; correct style
  is USI coordinates like `"7g7f"`, drops like `"P*3d"`, promotions with
  trailing `"+"` (e.g. `"8h2b+"`).
- Ranks map a=1 … i=9, files 1–9 as-is.
- Human-readable Japanese notation and KIF files are **generated** from
  USI by tooling, never hand-transcribed in parallel.

## Original vs corrected positions

- `sfen` = the position as found in the cited primary source. **Never edit.**
- `corrected_sfen` = a later/corrected edition's position, with
  `correction_note` explaining the difference (used e.g. for Muso edition
  variants). `null` when no correction is recorded.

## Verification levels

1. `position_verified`: SFEN parses, piece inventory is within the
   40-piece set, exactly one gote king, no nifu in the initial position.
2. `solution_verified`: every USI move is legal (incl. drop rules) and the
   final position is mate (gote in check with zero legal replies,
   including interpositions from the box).
3. `unique_solution_verified`: no alternate solution (yozume) — currently
   `false` for all records; requires a full solver (future work, see
   docs/validation.md).

Any record not yet collated against the original archive scans keeps
`verification.needs_manual_review: true`, even when 1–2 pass.

## Machine-computable features (benchmark use)

Computed later by tooling, never hand-judged: move count, piece counts on
board / in hand, presence of interpositions, sacrifices, promotions,
pawn-drop motifs, long sequences. Subjective difficulty is out of scope.
