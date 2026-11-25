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
7. **Intended-solution validation (legality only)** —
   `intended_solution_usi` / `intended_solution_moves` /
   `intended_solution_source` / `status.intended_solution_verified`
   (see `_validate_intended_solution` in `tools/validate.py`):
   when `intended_solution_usi` is `null`/absent the check is skipped
   (a `intended_solution_source` string alone records transcription
   progress and is allowed); when present, every entry must match USI
   syntax, `intended_solution_moves` (when present) must equal
   `len(intended_solution_usi)`, and each move must replay legally from
   `sfen` in order. Continuous check and final mate are **not** required
   on this side. Solver verification (mate proof, futile-interposition
   analysis, `exhaustive_mate_in_1`) applies to `solution_usi` only.

## `status.intended_solution_verified` — granting criteria

`true` asserts only that the transcribed intended line replays legally
from `sfen`. It makes no mate / continuous-check / shortest-ness claim.
The flag is asserted by a human and checked by the machine; CI never
sets it automatically.

1. **Granting conditions (all required for `true`)** —
   (a) `intended_solution_usi` is present as a non-empty USI list and
   `intended_solution_moves` (when present) equals its length;
   (b) `_validate_intended_solution` in `tools/validate.py` passes with
   zero errors: every entry matches USI syntax and replays legally in
   order from `sfen` (legality only; continuous check and final mate
   are not required);
   (c) the transcriber records the exact source actually read in
   `intended_solution_source`: national-government archive PID /
   canvas (R number) / column range and progress state (e.g.
   `NDL PID:861212 R0000008-9`), plus who/when in
   `verification.transcribed_by` / `transcribed_from` /
   `transcribed_date` as available. Only direct reading of
   national-government archive scans counts (`docs/data-policy.md`
   §§1–4); personal sites and non-government bodies may not appear.
   Who may set `true`: the transcriber or collator who performed (c),
   after confirming (b) locally; CI then re-checks (b).
2. **Relation to collation** — full record collation (`source.page`
   filled, `verification.needs_manual_review` cleared) is **not**
   required for `true`. An intended-text-only collation (solution
   columns read and cited) may grant `true` while board collation is
   still pending. In that case `needs_manual_review` stays `true` and
   the cited PID / canvas / columns in `intended_solution_source`
   (+ `notes` / `verification.method` on mismatch) are mandatory so a
   later full collation remains possible.
3. **`false` / absent handling** — absent is treated as unverified
   (`false`) by `tools/validate.py` and `tools/build_web.py`, but
   authors SHOULD write `false` explicitly while unverified so the
   state is visible in the record. `true` without
   `intended_solution_usi` is a validator error; a present USI that
   fails the legality replay must stay `false` until fixed or
   re-transcribed.
4. **Independence from solver verification (solution side)** —
   `intended_solution_verified` is orthogonal to
   `status.solution_verified` / `unique_solution_verified` and to mate
   proof / futile-interposition analysis, which concern `solution_usi`
   only. `true` on the intended side never supports a mate claim and
   never satisfies solution-side checks; `false` on the intended side
   never blocks solution verification.

## `status.solution_verified` — single-line guarantee (not a complete solution)

`status.solution_verified: true` asserts only a **linear guarantee**
for the recorded `solution_usi` as replayed from `sfen` by
`tools/validate.py` (see the solution walk and mate test in
`tools/validate.py`): the line alternates starting with sente, every
USI move is legal (including drop and promotion rules), every sente
move gives check, every recorded gote reply resolves the check, and
the final position is mate with gote to move — gote in check with
**zero** legal replies on that line, including interpositions and
drops from the box. It does **not** assert a complete solution.

In particular, `solution_verified` does **not** cover:

- all gote alternatives at intermediate plies off the recorded line
  (full-branch correspondence is not checked);
- longest-defense / shortest-mate claims;
- absence of alternate solutions (yozume) — that remains
  `status.unique_solution_verified`, which stays `false` in v1
  (see Known limitations below).

Example (scope illustration): zukou-050 — the recorded 9-ply main
line satisfies the linear guarantee above (legal, continuous check,
final mate), while the complete solution covering all gote
variations is 21 plies. The 9 vs 21 difference is the gap between a
single verified mating line and a fully branched complete solution.

Establishing a complete solution is a separate process requiring a
mate-search engine (e.g. YaneuraOu and similar mate search) and is
out of scope for the v1 validator. A dedicated `complete_solution`
field may be introduced in the future to record fully branched
solutions; it is not defined or checked in v1.

This definition changes no source requirements;
`docs/data-policy.md` §§1–4 continue to apply unchanged.

## Solver crosscheck record template (`verification.method`)

`solver` による照合を行った場合、`verification.method` への記録は
自由文ではなく以下の定型順序で書く。省略時は `none` / `記載なし` と
明示し、空欄のままにしない。

1. **engine** — engine名・版（commitを含む）。例:
    `engine=example-mate-engine v1.2.3 (commit abc1234)`。
    配布元URL・解説記事URL等は書かない。
2. **date** — 実行日（`YYYY-MM-DD`）。例: `date=2026-09-16`。
3. **command / conditions** — コマンドと探索条件。
    `go mate` の持ち時間（ms）、`Hash`、`Threads`、`DepthLimit`
    （上限なしの場合は `none`）をすべて書く。
4. **result** — `checkmate <N>手` / `nomate` / `timeout` / `none` の
    いずれか1つ。`checkmate` の場合は `solution_usi` との一致・不一致
    を併記する。`PV要約`（先頭数手＋最終手。長い場合は `...` で中略）
    を付す。
5. **handling** — 結果の取扱い。`solution不変` / `solution要検討` と
    `notes追記要` / `notes追記不要` を必ず書く。solver結果のみで
    `sfen` を書き換えない（訂正は `corrected_sfen` +
    `correction_note` に従う）。

書式（1行、順序固定）:

```text
[solver] engine=<name version (commit hash)>; date=<YYYY-MM-DD>; command="<command>"; Hash=<size>, Threads=<n>, DepthLimit=<n|none>; result=<checkmate N手|nomate|timeout|none> (<solution_usiとの一致・不一致>); PV=<PV要約>; handling=<solution不変|solution要検討>・<notes追記要|notes追記不要>
```

記載例:

```text
[solver] engine=example-mate-engine v1.2.3 (commit abc1234); date=2026-09-16; command="go mate 5000"; Hash=256MB, Threads=1, DepthLimit=none; result=checkmate 9手 (solution_usiと一致); PV=7g7f 3a4b ... 5e5d# (先頭2手＋最終手); handling=solution不変・notes追記不要
```

本テンプレは検証手段の記録であり、データ取得元ではない。
`source.*` の provenance rootを変更せず、NDL一次資料からの直接読解の
原則を置き換えない（`docs/data-policy.md` §§1–4は変更なし）。
`verification.reference_urls` 等に個人サイト・非政府団体のURLを
記録しない。engine名・版・commitの文字列のみとし、外部URLは
一切付さない。

## Mismatch handling (e.g. zukou No.20)

When the transcribed intended line (原典翻刻) and the solver-verified
canonical line (solution) disagree in lineage — e.g. zukou-020, where the
current 37-move canonical line is lineage-mismatched against the 詰手書
No.20 transcription (NDL PID:861212 R0000008-9, all 5 columns) and the
zukou No.20 board (PID:861211 R0000015) — the record is **retained with
a warning note, not deleted or overwritten**:

1. Keep `solution_usi` (verified mate) unchanged; keep `intended_*` as
   the transcription state (`null` USI + `intended_solution_source`
   progress note while USI化未了).
2. Record the mismatch in `notes` and `verification.method` (which PIDs /
   columns were collated, what disagrees, 別伝・別番・転写違いの疑い).
3. Keep `verification.needs_manual_review: true` until re-collation
   against the scans resolves it.
4. **別伝隔離条件**: isolate into a separate betsuden (別伝) record only
   when an independent lineage is positively identified (distinct
   board / distinct solution text attributable to another transmission);
   mere mismatch or undeciphered kuzushi stays as a warning on the same
   record. `sfen` itself is never rewritten to force agreement
   (corrections follow `corrected_sfen` + `correction_note`).

## Draft mode (`--draft`)

`python3 tools/validate.py --draft` relaxes checks for staging records
(`collections/*/*/drafts/`): `?` squares are allowed and an empty
`solution_usi` is a gap, not an error. Two position checks still run on the
confirmed pieces (unknown squares treated as empty):

- **illegal position** — the side not to move is already in check
  (2026-11-17). Such an SFEN cannot be solved; `tsume-solver` may return
  meaningless mates (observed on gyokuzu-076).
- **nifu** — two confirmed unpromoted pawns of the same side on one file
  (2026-11-17). Adding `?` squares cannot fix this, so it indicates a
  misread side or piece kind. Currently flagged on 31 gyokuzu drafts and
  none in seimyo/kanju.
- **dead pieces** — a confirmed sente pawn/lance on rank a, sente knight on
  rank a/b, or the gote mirror (2026-11-17). Flagged on 18 gyokuzu drafts,
  none in seimyo/kanju (where the dead-piece rule was used to assign sides).
- **piece budget** — a side with more than its share of a kind (2 rooks,
  2 bishops, 4 golds/silvers/knights/lances, 18 pawns, 1 king), counting
  board plus hand (2026-11-17). Flagged on 3 gyokuzu drafts (e.g. 024 with
  6 sente golds), none in seimyo/kanju.

`python3 tools/validate.py --procedures` checks the 詰手 transcriptions
(`collections/*/*/procedures/`): piece codes, destinations, markers,
move numbering, odd ply counts, and "last move is a king" (see
`docs/procedures.md` §4).

## Procedure mode (`--procedures`)

`python3 tools/validate.py --procedures` checks the 詰手 transcriptions in
`collections/*/*/procedures/*.json`: piece codes, destination squares,
promotion/drop markers, and sequential move numbers. Two structural gaps are
reported: an even total number of plies (a tsume problem ends on sente's
mating move, so the count must be odd) and a final move made by the king.
Because these records carry no board, legality is not checked here
(`intended_solution_usi` stays null).

## Known limitations (explicitly out of scope for v1)

- **No yozume (alternate-solution) search** — needs a full-width solver.
- **No longest-defense check** for gote replies off the main line.
- **No uchi-fu-zume (pawn-drop mate) foul detection** on the final move.
- Hence `status.unique_solution_verified` remains `false` everywhere.

## Roadmap

- Adopt `tsshogi` (MIT) for cross-validation of SFEN legality and KIF
  round-trips; adopt a df-pn based OSS tsume solver (cf. tanuki-tsume-shogi)
  for yozume / longest-defense proofs. See `docs/research.md` §5.2.

## Suite coverage (2026-11-26, 155 tests)

`tests/run_tests.py` is the executable form of this document. Groups:

- **Dataset**: every problem/collection record validates against the schema;
  zukou-002 spot check; intended-solution replay.
- **Drafts**: staging rules (`--draft`), id vs filename,
  `needs_manual_review`, empty solutions, one gote king per transcribed board.
- **Provenance**: `source.page` number matches the file number; draft PIDs and
  RIDs stay inside the collection's volumes and frame counts; drafts plus
  promoted problems exactly cover `1..problem_count`; every draft carries the
  NDL-only policy note.
- **First moves**: every recorded move checks the king (direct or discovered),
  `raw` digits equal file+rank, piece names match codes, `board_q` matches the
  draft; generated target/candidate docs match their generators.
- **Column heads**: cartouche/x/leaf/page/kind forms, one page reading not
  assigned twice, head leaves and head-to-problem assignment.
- **Procedures**: hand-transcribed lines replayed legally, parity/markers,
  `?`/unverified warnings, worksheet images present.
- **Pages**: KIF/JSON/viewer data, drafts page and review/procedure pages in
  sync with the records.
- **Docs hygiene**: file references exist, `?` totals and section 4.1 counts
  match the data, no control characters, no UTF-8 BOM.
- **Images**: every bundled JPEG is cited in `SOURCES.md`, every citation
  exists, and each file is a well-formed JPEG.
- **Tools**: every `tools/*.py` compiles, imports and answers `--help` with 0;
  `board_grid` line fitting is unit-tested (stroke skipping, fallbacks).
- **Code and pages**: no control characters in tools/tests/web/CI, no tabs in
  Python, and every generated HTML page has balanced tags.

## 出典 RID の実在確認（2026-11-25・NDL manifest 実測）

各 draft の `source.page` に書かれた `PID` と `RID` が、実際に NDL の IIIF
manifest に存在するかを機械照合した。

| PID | 画像（コマ）数 |
|---|---|
| 861216（精妙 上） | 57 |
| 861217（精妙 下・詰手） | 28 |
| 861191（貫珠 本編） | 32 |
| 861192（貫珠 詰手） | 22 |

- 精妙・貫珠の draft **502件**を照合し、**存在しない RID は0件**。
- 残り2件は別 collection（kinza, PID 861193）で、今回の照合対象外。

**意味**: 「この升は NDL のこのコマ」という参照が切れていないことの確認。
ネットワークが要るのでテストには入れず、日付つきの記録として残す。
再確認は manifest を取得して `R\d+` を集め、draft と突き合わせるだけ。

## 持ち駒（盤下持駒）の照合（2026-11-25）

持ち駒は**大きい活字**なので、1升170pxの解像度でも確実に読める。
`tools/hand_sheet.py` で複数題の持ち駒行を1枚に並べ、SFEN の手駒と**多重集合として**
比べた（順序は問わない）。

- **精妙 100題すべて照合**（100題完全一致。23 は 2026-11-25 に 桂2＋歩5 と確定）。
- **貫珠 50題すべて照合**（すべて完全一致）。
- 合計 **149題、不一致 0**。記録: `docs/hand-audit.json`。

**版による持ち駒の位置（重要）**:
- **精妙**: 盤の**下**（外枠の外）。切出しは下向き（`--yoff 0.5`、圧縮頁は `6.5`）。
- **貫珠**: **外枠の内側**、盤の最下段の罫線のすぐ上。切出しは**上向き**（`--yoff -5.2`）。
  これを知らずに下だけを探すと「未確認」が量産される（実際に5題を無駄にした）。

**意味**: 持ち駒の転記は**信頼できる**（150題で不一致0）。
升の駒種のように草書で潰れないため、**全題の照合が可能**。

## 題号（盤面頁の番号）の抜き取り照合（2026-11-25）

盤面頁の右上に刷られた題号を、draft の `number` と照合した。12題を抜き取り
（精妙 3・17・33・50・66・88、貫珠 5・19・30・41・47・50）、すべて一致。

- 方法: 盤の右上の帯（盤の右端 −10% 〜 ＋1%、盤の上 −8.5% 〜 −0.5%）を切り、
  期待する題号と並べて読む。
- その後、**精妙100題すべて**を連続で照合し、**計150題すべて一致**（精妙 100題・貫珠 50題）。
  題号は盤の右上の角にあり、頁によっては格子の右端より内側にある（帯を広げて対応）。
  百番は「百番」と刷られている。
  記録: `docs/number-audit.json`（帯の位置も記録してある）。
- **意味**: 「この盤面は N 番である」という対応が、少なくともこの106題では正しい。
  `source.page` の題号は活字から転記されており、その読みに誤りは見当たらない。
- 残りは貫珠の未読分。貫珠の題号は**正式数字**（壹・貳・叄…）で刷られている。
  3・11 は頁の格子が合わないため、固定窓（pct:30,19,18,13）で読み直して確認した。

### 精妙23 の持ち駒は 桂2＋歩5 で確定（2026-11-25・2400px 比較）

前回「香1＋桂1 か 桂2 か」で止めたが、同書の活字を並べて決着した。

| 参照 | 字形 |
|---|---|
| 精妙64（記録 `L`）、精妙95 の `香` | 禾 の下に**日（箱）** |
| 精妙95 の `桂`、精妙37（記録 `N`） | 木＋**圭（土の重なり）**、箱なし |
| 精妙23 の末尾2字 | **95 の 桂 と同一（木＋圭）**、2字とも同形 |

したがって印字は **桂2＋歩5**。draft を `N L 5P` から **`NN5P`** に直した。
材数は 桂4（盤上 n8一・N9五＋手2）・香1（盤上 7九）・歩7 で、いずれも上限内。
これで持ち駒の照合は **150題すべて一致**（うち23は今回確定）。
