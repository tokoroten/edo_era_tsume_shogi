# 玉図転記手順書（draft運用・?台帳・本番昇格）

対象: `collections/edo/gyokuzu/`（将棋玉図・将棋玉図詰手、桑原君仲、天保7年=1836年）。
根拠は本リポジトリ内文書およびNDL手順のみとする。
個人サイト・非政府団体サイトの参照・記載は一切行わない
（`docs/data-policy.md` §§1–4、`CONTRIBUTING.md` Ground rules 1–2、
`docs/data-acquisition.md` §1、`docs/ndl-collation.md` 冒頭）。

関連正本:

- 取得・URL・命名: `docs/data-acquisition.md`
- 書誌・版・玉図100題確定: `docs/research.md` §1.5、`collections/edo/gyokuzu/collection.json`
- 来歴・二段階転記・二系統記録: `docs/provenance.md`、`docs/methodology.md`
- 検証・不一致時手順: `docs/validation.md`、`CONTRIBUTING.md`
- 丁・canvas対応メモ: `docs/ndl-collation.md`
- 実装根拠: `tools/validate.py`（draft節）、`tests/run_tests.py`（`TestDraft`）、`schema/problem.schema.json`

書誌前提（`docs/research.md` §1.5、`collection.json` より）:

- NDLBibID `000000493916` / 請求記号 `209-462`、上巻50丁・下巻28丁。
- デジタル単位 PID `861197`（上巻・図面）/ `861198`（下巻・手順）。いずれもNDL書誌情報のみに基づく。
- 上巻 図面100図（一番〜百番）・下巻 手順100題（一番〜百番、R1開始・R28終了）を
  図手順突合せで100問題と確定。`problem_count: 100`、`problems_transcribed: []`（未転記）。
- 版所見: 層B＝明治・吉川半七文玉囲再版系。下巻R29終辞・奥付の確定読取あり。
  確定版特定・原典照合未了のため全件 `needs_manual_review` 前提。

## 1. draft運用の手順

draftは `collections/edo/gyokuzu/drafts/*.json` のみに置く。
`problems/` とは厳密に分離する。実装上の分離根拠は以下。

- `tools/validate.py`: `is_draft_path()`（`/drafts/` 含有判定）。
  通常モードは `drafts/` 下ファイルを明示エラーで拒否する
  （`draft file requires --draft`）。`--draft` モードは `drafts/` 下のみ受理し、
  それ以外は `not under drafts/` で拒否する。`collection.json` は対象外。
- `tests/run_tests.py` `TestDraft`: 厳密スイートは `drafts/` を含めないこと、
  `build_web` 用glob（`collections/*/*/problems/*.json`）も `drafts/` を除外することを検査する。
- スキーマ（`schema/problem.schema.json`）は変更しない。
  draftは `solution_usi: []` / `solution_moves: 0` / SFEN内 `?` を含むため
  意図的にスキーマ非適合のまま staging する（`validate.py` docstring）。

手順:

1. **draft作成**: `drafts/NNN.json`（`NNN` は3桁ゼロ埋め）を既存draft
   （例 `drafts/001.json`）を雛形に作成する。必須素性は
   `DRAFT_REQUIRED`（`id, collection_id, number, author, published_year, period,`
   `sfen, solution_usi, solution_moves, status, verification, source, rights`）に従う。
   `id` は `^[a-z]+-[0-9]{3}$`（例 `gyokuzu-001`）かつ
   `{collection_id}-{number:03d}` と一致させること。
   初期値は未転記を正直に書く: SFEN内に `?`、`solution_usi: []`、`solution_moves: 0`、
   `intended_solution_usi/moves: null`、進捗のみ `intended_solution_source` に記録、
   `status.*_verified: false`、`verification.needs_manual_review: true`、
   `source.page` は読んだ範囲を直記（丁未確定ならその旨を明記）。
   盤面・手順の実体は必ずNDL一次資料スキャンの直接読取とし、
   第三者KIF・将棋サイトはタイピング補助にも使わない。
2. **`--draft` 検証**: `python3 tools/validate.py --draft`（引数なしで
   `collections/*/*/drafts/*.json` を自動探索）または対象ファイルを明示する。
   終了コード0は「errorなし（gap/warningは許容）」を意味する。
   `gap:` 行が残件リストとなる。errorは必ず修正する。
   緩和内容（`validate_draft_record`）:
   - SFEN内 `?` を許容。`?→1` 置換後に構文のみ検査し、
     盤依存検査は skip して gap 化する。
   - `solution_usi: []`（`solution_moves: 0`）を許容し、solution walk を skip して gap 化する。
     部分手順（偶数手プレフィックス等）の parity・合法歩行・詰み検査は昇格時（strict）に強制し、
     draft段階では gap 報告に留める。
   - `intended_*` は盤不完全時は構文・件数のみ検査する。
   - `needs_manual_review: true` は警告（失敗ではない）。
3. **gap解消**: 出力された `gap:` を `notes` 内の `gap:` 行および81升表・SFEN案に反映し、
   原寸高解像（IIIF `full`）再読で1件ずつ潰す。推測で埋めない（§2）。
4. **`problems/` 移動**: `?` がゼロかつ `solution_usi` 非空になったdraftは
   `validate_draft_record` が内部で `validate_record`（strict）に委譲する。
   すなわち完成draftの `--draft` 通過＝strict同等。error/gapゼロを確認してから
   `collections/edo/gyokuzu/problems/NNN.json` へ移動する（ファイル移動のみ。内容書換えで辻褄合わせをしない）。
5. **通常validate → tests → build**: 移動後に通常検証
   `python3 tools/validate.py <problems/NNN.json>`、
   全件スイート `python3 tests/run_tests.py`（CIも同内容）を通す。
   `needs_manual_review: true` は警告でありCI失敗にしないが、維持したままにする（§3）。
   公開物は `problems/*.json` のみから生成するため（`build_web` glob）、
   `drafts/` 残置物が本番に混入しないことを `TestDraft.test_no_drafts_in_strict_suite` 相当で確認する。

## 2. ?台帳の運用

`?` は「不明升」の正規記録であり、欠陥ではない。検証器は `?` の数を数えて
`gap: sfen has N '?' (untranscribed squares)` として台帳化する。

- **記録**: 読めない升は `?` のまま残す。`notes` に81升表・SFEN案・`gap:` 行を持ち、
  例: `gap: 盤面28升? (種確定でも先後未確定は?化)・…・solution全手・intended全手(USI化)`。
  `?` の数・字種候補・file割付け不確定・駒箱未計上・手順未USI化を列挙する。
- **推測補完禁止**: 字種が読めても先後不明なら `?` に倒す（大文字化による攻方決め打ち禁止）。
  くずし・文節・手番・筋が確定しない手順文はUSI化せず、`intended_solution_usi/moves` は
  `null` のまま `intended_solution_source` に進捗のみ残す。暫定読の字面列挙を手順として登録しない。
  個人サイト・非政府団体サイトによる補完は禁止（`docs/data-policy.md` §§3–4）。
- **原寸再読条件**: gapの解決条件は原寸高解像（IIIF Image API の `size=full`、
  `https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/full/full/0/default.jpg`）での再読と丁特定。
  軽量版（例 `1024,`）は作業仮読までとし、確定読取は `full` で行う。
  取得・命名・検証（SOI/EOI・非0バイト・欠番なし）は `docs/data-acquisition.md` §§2–3に従い、
  画像はリポジトリに置かず一時作業領域に保存する。印影遮蔽部（例 No.1 初手付近の矩形印影・末尾円形印影）は
  「直接読取不可」として `intended_solution_source` に記録し、推測で越えない。

## 3. 本番昇格条件

`drafts/` → `problems/` の昇格条件（すべて必須）:

1. **`?` ゼロ**: SFEN内に `?` がないこと。残存する限り draft 扱いであり、
   strict（`validate_record`）は拒否する。
2. **`solution` 確定**: `solution_usi` 非空、`solution_moves == len(solution_usi)`、
   strict の solution walk（合法歩行・王手連続・最終局面の詰み＝玉方全応手ゼロ）通過。
   空手順・偶数手プレフィックスのまま昇格しない。
3. **通常validate通過**: `python3 tools/validate.py <problems/NNN.json>` が error ゼロ。
   完成draftに対する `--draft` 実行が `validate_record` に委譲され gap ゼロになることと等価。
4. **`needs_manual_review` 維持**: 昇格後も `verification.needs_manual_review: true` を維持する。
   validator成功・solver照合のみでは解除しない。解除は人間が国営アーカイブスキャンと照合し
   `source.page` を充填した後のみ（`docs/provenance.md` 二段階転記 Stage 2、
   `CONTRIBUTING.md` Ground rule 6、`docs/validation.md`）。
   `status.intended_solution_verified` の `true`（USIあり＋合法再演通過＋直接読取者のPID/canvas/列記録）も
   盤照合を代替しない。系統不一致時は両系統を保持し `notes`＋`verification.method` にPID/列を記録、
   `needs_manual_review: true` を維持する。`sfen` を書き換えて辻褄合わせをしない
   （訂正は `corrected_sfen`＋`correction_note`）。

`suen` 系フラグの目安: 昇格時点で `status.solution_verified` は strict の線形保証
（記録線上の合法・連続王手・最終詰み）のみを主張する。余詰・最長抵抗・完全分岐は範囲外であり
`unique_solution_verified` は `false` のまま残す（`docs/validation.md`）。

## 4. source.page・intended_solution_sourceの記録形式（PID/RID/列範囲）

いずれもNDL一次資料の直接読取所見のみを書く。PID/RID/canvas対応は
`docs/data-acquisition.md` §2.3（`canvas N ↔ RID=R+7桁ゼロ埋め`）に従う。
canvas番号は撮影順であり丁・問題番号と同一ではない（`docs/ndl-collation.md` §1.2）。

- **`source.page`**: 読んだ丁・頁・番・PID/RIDを直記する。見開き仮説（右=偶数/左=奇数 等）に依らず
  RID・左右・題簽を書く。丁未確定の間はその旨を明記する。`推定` による外挿を充填しない。
  形式例（`drafts/001.json`、`drafts/005.json`）:
  ```text
  NDL PID:861197 R0000006左 一番 / NDL PID:861198 R0000001 一番 (丁未確定)
  NDL PID:861197 R0000008左 五番 / NDL PID:861198 R0000002 五番 (丁未確定)
  ```
  すなわち `NDL PID:<上巻PID> R<7桁><左|右> <漢数字>番 / NDL PID:<下巻PID> R<7桁> <漢数字>番 (丁…)`
  の順序を守る。丁特定後は丁・面（例 `丁14表・左`）を添える
  （`docs/ndl-collation.md` §3.4 の充填メモ参照）。全件 `null` 解消は個別照合をもって行う。
- **`intended_solution_source`**: 読んだ下巻PID/canvas（R番号）/列範囲と進捗状態を必ず残す
  （`docs/provenance.md`、`docs/validation.md` の付与条件）。
  USI `null`＋本フィールドのみは正規の中間状態（未翻刻）であり、validatorは合法再演をskipする。
  形式例:
  ```text
  NDL PID:861198 R0000001 一番 (3列, USI化未了・初手印影遮蔽・くずし未確定あり)
  NDL PID:861198 R0000002 五番 (3列, USI化未了・くずし未確定あり)
  ```
  すなわち `NDL PID:<PID> R<7桁> <漢数字>番 (<列数>列, <USI化未了|くずし未確定|印影遮蔽…>)`。
  `intended_solution_verified: true` を付与できるのは、USIあり＋件数一致＋合法再演通過に加え、
  直接読取を行った転記者/照合者が正確な読取源（PID/canvas/列範囲＋進捗）を記録した場合のみ。
- **`verification.transcribed_from` / `method`**: 盤面PID/RID＋手順PID/RIDを両記する。
  例: `NDL PID:861197 R0000006 / NDL PID:861198 R0000001 (direct image reading; no external sites)`。
  `reference_urls` には国営アーカイブ頁のみを置き、個人・非政府団体URLは一切置かない。

## 5. 先後未確定・盤向き暫定の運用ルール

現行draft（001–005）の申送りに基づく暫定運用。原寸再読・盤向き確定まで維持する。

- **先後未確定**: 玉（玉方=`k`）および盤下持駒の確定分を除き、盤上駒の先後は未確定として扱う。
  種が読めても先後不明の升はSFEN上で `?` に倒す。安易な大文字化（攻方決め打ち）は禁止。
  玉の `k` も王/玉字形の拡大再読を要する場合は `notes` に明記する（例 `王/玉字形は要拡大再読`）。
  玉方駒箱（SFEN持駒の小文字部）は盤面確定まで未計上とし、攻方持の確定分のみ記録する。
  盤面確定後に駒箱を再計算し `tools/validate.py` の照合を通す（`docs/methodology.md` の駒箱規約）。
- **盤向き暫定**: `上=r1・右/左=f9` の仮定は暫定である。右端fileの割付けは `±1` 不確定とし、
  星目位置も印刷ずれ・数え間違いの可能性ありとして原寸確認対象に残す。
  `002.json` のみ `左=f9` 仮定で書かれているため特に要注意であり、他件（001/003/004/005の `右=f9` 仮定）と混同しない。
  盤向き確定時に全draftのSFEN・81升表を一括見直す（draft `notes` の申送り事項）。
  図巧側の作業仮説（上=rank 9側、IIIF回転 `0`）は `docs/ndl-collation.md` §2.1の扱いに準じ、
  個別盤面の確定は照合時に盤外情報（持駒欄・丁付・柱刻）でも確認する。
- **共通申送り**: crop命名（`No0X_Rxxxxxx_left/right`）と `full` の対応を維持し、
  見開き偶奇仮説に依らずRID・左右・題簽を `source.page` に直記する。
  下巻は列数・印影有無・USI化状態を `intended_solution_source` に定型記録する。

## 6. 進捗現状と次のマイルストーン（2026-09-17時点・ファイル実測）

本節は `collections/edo/gyokuzu/` のファイル実測のみに基づく進捗台帳である。
エンジン（`tools/validate.py`・solver）の新規実行は行っていない。
`?` 総数は各draftの `sfen` 文字列中の `?` 文字の単純合計であり、
`--draft` の `gap:` 集計の代替ではない（gap解消時に `--draft` で再確定する）。

- **draft件数**: `drafts/` に `001.json`〜`100.json` の100件あり（2026-09-17に `099`・`100` 到達）。
  目標100件（`collection.json` `problem_count: 100`、上巻100図・下巻100題）に到達。
  新規draft作成の残件なし。
- **`?` 総数**: 98件時点の実測ではSFEN内 `?` 合計 **2043**（例 `001.json` は `?=28`）。
  先後適用一巡（§7.5）による増減あり。個別実測例: `099.json` は `?=29`、`100.json` は `?=33`、
  `098.json` は先後適用で `?=21→20`（`notes` 記載）。
  いずれも先後未確定・字種未確定・file割付け未確定等を `?` に倒した正規記録（§2）。
  `?` ゼロのdraftはファイル実測上なし。総数の再集計および `gap:` の確定は
  次回 `--draft` 実行時に行う（本書§6冒頭の「エンジン新規実行なし」方針を維持）。
- **原典翻刻（intended）USI化率**: **0%**（`intended_solution_usi: null` が100/100件、
  `status.intended_solution_verified: false` が100/100件）。
  `intended_solution_source` にPID/RID/列範囲＋進捗（`USI化未了・くずし未確定あり` 等）を
  記録した正規の中間状態であり、欠陥ではない（§4、`docs/provenance.md` 二系統記録、
  `docs/validation.md` intended節）。
- **正規手順（solution）確定率**: **0%**（`solution_usi: []`＋`solution_moves: 0` が100/100件）。
- **本番昇格**: **0件**。`collections/edo/gyokuzu/problems/` は不存在であり、
  `collection.json` `problems_transcribed: []` を維持する。
  `drafts/` は `problems/` と厳密分離するため（§1）、draft件数は昇格件数に含めない。
- **`needs_manual_review`**: `true` が100/100件。昇格後も維持する方針（§3）に整合する。

他文書との整合（矛盾なし）:

- `collection.json`（`problem_count: 100`、`problems_transcribed: []`＝未転記）:
  draft 100件は staging であり `problems_transcribed` に含めないため矛盾しない。
- `docs/research.md` §1.5（題数100確定・本転記未了・全件 `needs_manual_review` 前提）:
  本節の「100件到達・昇格0件・全件要照合」と一致する。
- `docs/provenance.md`（二段階転記 Stage 2、`intended null`＋`intended_solution_source` は正規中間状態）・
  `docs/validation.md`（intendedは合法再演のみ・`null` はskip）・
  `docs/methodology.md`（玉方駒箱未確定時は未計上）:
  本節の「intended 0%＝異常ではない」「駒箱未計上を残件とする」扱いと一致する。
- `docs/data-acquisition.md`・`docs/ndl-collation.md`・`docs/data-policy.md` §§1–4:
  本節はNDL一次資料・本リポジトリ内文書のみを根拠とし、
  個人サイト・非政府団体サイトの参照・記載を追加しない。

次のマイルストーン（順序固定）:

1. **draft 100件完**: 達成（`001`〜`100` が `drafts/` に存在）。
   `099`（上巻 `R0000055左`・下巻 `R0000028` 開4列＋結4列見込み）・
   `100`（上巻 `R0000056右`・下巻 `R0000028` 開3列＋`R0000029` 結5列＝計8列）は
   いずれも§1手順で作成済み（各draft `notes` の申送り・列帰属メモを参照）。
2. **`?` 解消**: 原寸高解像（IIIF `full`）再読＋丁特定で `?` を1件ずつ潰す（§2）。
   推測補完・大文字化による決め打ちは禁止。盤向き確定時は全draftのSFEN・81升表を一括見直す（§5）。
3. **USI化（intended→solution）**: 下巻列の文節・手番確定後に `intended_solution_usi/moves` を充填し
   `intended_solution_source` にPID/canvas/列範囲を残す（§4）。
   `solution_usi` はstrictのsolution walk（合法歩行・王手連続・最終詰み）通過を条件とする（§3）。
4. **昇格**: `?` ゼロかつ `solution` 確定のdraftのみ `problems/` へ移動し、
   通常validate → `tests/run_tests.py` → `build_web` を通す（§1手順4–5）。
   `needs_manual_review: true` は維持したままとする（§3）。

## 7. 先後判定法（持駒向き基準・暫定運用）

本節は上巻図面の盤上駒の先後（攻方＝先手・大文字／玉方＝後手・小文字）を
NDL一次資料スキャンの直接読取のみで判定するための暫定作業仮説である。
根拠は本リポジトリ内draftのNDL読取所見（No.4–No.7で確立・No.6–No.7で検証）および
NDL書誌・画像（PID `861197`／`861198`）のみとし、
個人サイト・非政府団体サイトの参照・記載は一切行わない
（冒頭・`docs/data-policy.md` §§1–4、`docs/provenance.md` に従う）。
本節の適用は `?` の確定を意味しない。§2（推測補完禁止）・§5（先後未確定運用）は継続し、
SFEN上の `?→大文字／小文字` 確定は原寸高解像（IIIF `full`）再読＋丁特定をもって行う。

### 7.1 R1–R5ルール

- **R1（持駒同向き＝攻方候補）**: 盤下持駒欄の駒字と同向きに印刷された盤上駒は
  攻方（先手・SFEN大文字）候補とする。持駒自体は盤下の直接読取で確定した分のみ
  攻方持として記録する（例: No.4「桂銀金金」→ `2GSN`、No.5「歩角」→ `BP`、
  No.6「桂銀銀」→ `2SN`、No.7「金金金」→ `3G`。各draft `notes` の持駒項参照）。
- **R2（180度逆向き＝玉方候補）**: 持駒字に対し180度逆向きに印刷された盤上駒は
  玉方（後手・SFEN小文字）候補とする。向きの比較は同一図内の持駒欄を基準とし、
  他図・他丁の向きを持ち込まない。
- **R3（玉によるcross-check）**: 玉（玉将）は向きによらず玉方 `k` と仮置きし、
  R1／R2判定のcross-checkに用いる。すなわち玉と同向き群は玉方候補、
  玉と逆向き群は攻方候補となることを確認する。
  玉の `k` 自体も王／玉字形の拡大再読を要する場合は `notes` に明記し（§5）、
  字形未確定のまま確定扱いしない。
- **R4（判定不能は `?` 維持）**: 向き不鮮明・くずし未確定・印影遮蔽・印刷かすれ等で
  R1／R2のいずれとも断定できない駒は判定不能とし、種が読めてもSFEN上は `?` に倒す。
  R1／R2を推測で拡張しない（§2の推測補完禁止を維持）。
- **R5（盤向き未確定下の扱い）**: `上=r1・右／左=f9` の仮定は暫定（§5）のため、
  R1–R4による先後候補は file／rank 割付けの確定には使わない。
  右端file割付け `±1`・星目印刷ずれの留保は維持し、
  盤向き確定時に全draftのSFEN・81升表を一括見直す。

### 7.2 確信度

- **総合確信度 70–80%**（暫定作業仮説としての目安。確定読取ではない）。
- 内訳の目安: 持駒字の読取自体は明瞭な題（No.4–No.7の持駒欄はいずれも明瞭との所見）。
  向き対比の有効性はNo.4–No.7の4題連続で成立したことにより確立し、
  うちNo.6–No.7で対向写り（`R0000009` 左右）・下巻列帰属（`R0000002` 六番＝中央1列短手・
  七番＝左端2列）との突合せを含む検証を経た。
- 70–80%に留める理由: 原寸（IIIF `full`）再読・丁特定・王／玉字形拡大確認が未了であり、
  印刷ずれ・数え間違い・盤向き `±1`・くずし未確定が残るため（§5・各draft `gap:` 参照）。
  validator・solverによる裏付けはなく、数値は作業優先度付けの目安に留める。

### 7.3 留保事項

1. 本法はSFEN確定根拠ではない。R1–R3で候補が付いてもSFENの `?` は外さない。
   安易な大文字化（攻方決め打ち）は引き続き禁止（§2・§5）。
2. 玉方駒箱（SFEN持駒の小文字部）は盤面確定まで未計上とし（§5、`docs/methodology.md` 駒箱規約）、
   盤面確定後に再計算し `tools/validate.py` の照合を通す。
3. 玉の王／玉字形・持駒欄外の小字（枚数表記なし等の確認）・欄外丁字（例 No.5「三」・No.7「四」）は
   丁特定と切り離して断定しない。`source.page` への丁充填は個別照合による（§4）。
4. R1–R3の適用は原寸高解像（IIIF `full`）再読を条件とし、
   軽量版（例 `1024,`）は作業仮読に留める（§2）。
5. `needs_manual_review: true` は本法の適用によっても解除しない（§3・§6）。
   解除は人間が国営アーカイブスキャンと照合し `source.page` を充填した後のみ。

### 7.4 全draft適用手順

全draft（`001.json`〜`100.json`）への適用は
以下の順序で行い（2026-09-17に全100件へ一巡済み。詳細は§7.5）、
SFEN書換えによる辻褄合わせは行わない：

1. **持駒再読**: IIIF `full` で当該番の盤下持駒欄を再読し、字種・向き・枚数表記の有無を
   `notes` 持駒項に記録する。読めない場合は `?` 維持とし次番に進まない。
2. **R1–R4適用（候補記録）**: 盤上各駒について持駒基準の向き対比を行い、
   攻方候補／玉方候補／判定不能（`?` 維持）を81升表に追記する。
   R3として玉との向き整合（cross-check）を必ず記録する。
3. **SFEN不変**: 本段階ではSFENの `?` を外さない。`solution_usi: []`・
   `intended_solution_usi: null`・`needs_manual_review: true` を維持する。
4. **gap更新**: R1–R4で得た候補・残件を `notes` の `gap:` 行に反映する
   （例 `gap: 盤面N升?（R1–R2候補付・原寸要確定）・…`）。
   `source.page`・`intended_solution_source` の形式は§4に従い、推定による外挿を充填しない。
5. **`--draft` 再確定**: `tools/validate.py --draft` の新規実行は行わず、
   次回実行時の `gap:` 集計で再確定する（本書§6の「エンジン新規実行なし」方針を維持）。
   errorは必ず修正、gapは推測で潰さない（§1手順2–3）。
6. **盤向き確定時の一括見直し**: §5の盤向き（`上=r1・右／左=f9`）確定時に、
   R1–R5の候補を含む全draftのSFEN・81升表を一括見直す。
   `002.json` の `左=f9` 仮定の特異性に注意し他件と混同しない。

### 7.5 全100件一巡記録（2026-09-17・ファイル実測・エンジン新規実行なし）

本節は `collections/edo/gyokuzu/drafts/001.json`〜`100.json` の `notes` 実測のみに基づく。
`tools/validate.py`・solverの新規実行は行っていない。`?` 削減数の確定は次回 `--draft` の
`gap:` 集計による（§7.4手順5）。

- **一巡の範囲**: 全100件の `notes` に先後適用記録あり（98件は `先後適用` 表記、
  `081.json`・`082.json` は `SENGO-081`／`SENGO-082` 表記で同趣旨）。
  いずれもNDL一次資料スキャンの直接読取のみを根拠とし、
  個人サイト・非政府団体サイトの参照・記載はない。
- **適用内容**: §7.4手順1–4に従い、持駒再読→R1–R4候補記録→SFEN不変を原則とし、
  高確信度（持駒字種＋字形一致＋同向き明瞭＋駒数上限整合）のみに限り `?→大文字／小文字` 化。
  該当なしは削減0としてSFEN不変（例 `099.json` は `?=29→29`、
  `100.json` は `?=33→33`、`007.json` は `?=21` 維持）。
  `solution_usi: []`・`intended_solution_usi: null`・`needs_manual_review: true` は全件維持。
  玉はR3 cross-checkで `k` 維持（王／玉字形は原寸再読対象として `notes` に残す）。
- **残件1（反転群なし図の限界）**: 多数図で180度逆向きの反転群なしとの所見。
  反転群がない図では向きのみによる先後確定は不可とし、高確信度のみ更新・他は `?` 維持。
  持駒なし図は基準なしのため更新不可（例 `036.json`・`092.json`・`095.json`）。
  持駒表記と `notes` の不整合申送りあり（例 `096.json` の持駒申送り）は原寸確認後に再適用する。
  駒数上限超過の傍証（例 `099.json` の金5・`100.json` の金5／香4／桂4）は
  単独の攻方決め打ち不可の根拠とし、小文字化・大文字化の推測拡張は行わない（§2・§5維持）。
- **残件2（原寸再読）**: 全件に `file` 割付け `±1`・星目位置・くずし字形・王／玉字形の留保あり。
  解決条件は原寸高解像（IIIF `full`）再読。軽量版は作業仮読に留める（§2）。
- **残件3（丁特定）**: 全件 `丁未確定` を維持。`source.page` への丁・面充填は個別照合による（§4）。
  欄外丁数・見開き丁継ぎ・対向頁同時写りによる天地校正・最終丁見込み（`100.json`）の再確認が残る。
- **残件4（USI化）**: 原典翻刻（intended）USI化率0%・正規手順（solution）確定率0%を維持。
  `intended_solution_source` のPID／canvas／列範囲＋進捗記録は正規の中間状態であり欠陥ではない
  （§4、`docs/provenance.md`、`docs/validation.md`）。
  下巻列の文節・手番確定後に `intended→solution` の順序で進める（§6マイルストーン2–3）。
  `needs_manual_review: true` は維持し、本法の適用によっても解除しない（§3・§7.3）。

他文書との整合（§7.5追加分。矛盾なし）:

- `docs/methodology.md`（先手大文字・後手小文字・手番 `b`・駒箱＝残り駒・検証器照合・
  駒箱不明時は `-`＋`notes` 明記）: 本節は向きによる候補付けのみを行い、
  SFEN確定・駒箱計上は盤面確定後に回すため矛盾しない。
- `docs/validation.md`・`docs/provenance.md`（二系統記録・`intended null`＋`source` は正規中間状態・
  `needs_manual_review` 維持・系統不一致時は両系統保持）:
  本節は手順（intended／solution）・系統判定に介入せず、盤先後の候補整理に留まるため矛盾しない。
- `docs/data-policy.md` §§1–4・`docs/data-acquisition.md` §1・`docs/ndl-collation.md` 冒頭・
  `docs/research.md` §1.5（NDL一次資料・本リポジトリ内文書のみを根拠とし全件要照合）:
  本節はNDL読取所見（No.4–No.7確立・No.6–No.7検証）のみを根拠とし、
  個人サイト・非政府団体サイトの参照・記載を追加しない。
