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

## Intended vs canonical solutions (two-track)

Two parallel lines are recorded; they have different guarantees:

- `intended_solution_usi` / `intended_solution_moves` /
  `intended_solution_source` = **intended (原典翻刻)**. The line as read
  from the primary-source solution text (e.g. the 詰手書 columns),
  transcribed into USI. It is a historical record of what the source
  presents, **not a claim that the line mates**. It may be `null` while
  transcription is pending (USI化未了・くずし未確定を含む). Its provenance
  goes in `intended_solution_source` (which NDL PID / canvas / column was
  read, e.g. `NDL PID:861212 R0000008-9`); see `docs/provenance.md`.
- `solution_usi` / `solution_moves` = **solution (canonical, 検証済み正解)**.
  The solver-verified mating line that `tools/validate.py` walks and
  mate-checks. Only this side carries the mate guarantee.

Operational rules:

1. **intended requires legality only.** Each USI move in
   `intended_solution_usi` must be legally playable in order from the
   recorded `sfen`. Continuous check, final mate, and shortest-ness are
   **not required** — old records may contain an incorrect or non-mating
   line, and that is recorded as-is.
2. **Solver verification applies to the solution side.** Mate proof,
   futile-interposition analysis, and `status.solution_verified` concern
   `solution_usi` only. `status.intended_solution_verified` records only
   whether the intended line passed the legality replay.
3. **Japanese notation and KIF remain generated** from the canonical
   `solution_usi` by tooling. The intended line is shown in USI as
   transcribed; it is never used as validator or generator input.
4. The viewer renders the two lines in separate sections
   (想定解法（原典翻刻） / 検証解（ソルバー確認）) and shows 未翻刻 while
   `intended_solution_usi` is `null`. `intended_solution_source` alone
   (without USI) documents transcription progress, not a solution claim.

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
