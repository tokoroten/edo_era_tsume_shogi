# 将碁絹篩転記手順書（文字譜中心・題簽連鎖・附記号・落名変化・draft運用）

対象: `collections/edo/kinza/`（将棋絹篩 上・下、福島順棊、NDL書誌の出版年は欠載のため `published_year: 1800` は暫定）。
根拠は本リポジトリ内文書およびNDL一次資料スキャンの直接読取所見のみとする。
個人サイト・非政府団体サイトの参照・記載は一切行わない
（`docs/data-policy.md` §§1–4、`CONTRIBUTING.md` Ground rules 1–2、
`docs/data-acquisition.md` §1、`docs/ndl-collation.md` 冒頭、
`docs/gyokuzu-transcription.md` 冒頭の制限を準用）。

関連正本:

- 取得・URL・命名・保存先・検証: `docs/data-acquisition.md`
- 書誌・版・総題数54確定: `collections/edo/kinza/collection.json` `edition_note` / `source.digital`、`docs/research.md` §1表・§1.3・§8（絹篩P3）
- 来歴・二段階転記・二系統記録: `docs/provenance.md`、`docs/methodology.md`
- 検証・不一致時手順・solver記録様式: `docs/validation.md`、`CONTRIBUTING.md`
- 丁・canvas対応の考え方: `docs/ndl-collation.md` §1（`canvas N ↔ RID=R+7桁ゼロ埋め`、canvasは撮影順であり丁・問題番号と同一ではない）
- draft運用の原本: `docs/gyokuzu-transcription.md` §§1–3（本書§1–§2はそのkinza準用）
- 実装根拠: `tools/validate.py`（draft節）、`tests/run_tests.py`（`TestDraft`）、`schema/problem.schema.json`

書誌前提（`collection.json` より。NDL書誌情報のみに基づく）:

- NDLBibID `000000493914` / 請求記号 `183-243`、出版者 玉屋久五郎、形態 `2冊 (6, 59丁)`。
- デジタル単位 PID `861193`（上・40コマ）/ `861194`（下・31コマ）。いずれもインターネット公開。
- 任務指示名『将碁絹篩』・著者表記「福島順碁」は「棋／碁」「棊／碁」の表記ゆれであり、NDL書誌表記「将棋絹篩」「福島順棊」を正とする（`collection.json`）。
- 上巻は文字譜中心・図面なしのため、盤面転記ではなく文字譜（手順文）の読解が主体になる。
- 総題数54で確定: 上巻1番〜28番（28題）＋本文29番〜50番（22題）＋附録一番〜四番（4題）。`problem_count: 54` は確定値、`problems_transcribed: []`（未転記）。
- 出版年はNDL欠載のため暫定（`published_year_note` 参照）。版特定・原典照合未了のため全件 `needs_manual_review` 前提。

## 1. draft運用の手順（gyokuzu準用）

draftは `collections/edo/kinza/drafts/*.json` のみに置く。
`problems/` とは厳密に分離する（`collections/edo/kinza/` 直下に `problems/` は不存在）。
分離の実装根拠は `docs/gyokuzu-transcription.md` §1 と同じ
（`tools/validate.py` `is_draft_path()`、通常モードは `drafts/` を拒否・`--draft` は `drafts/` のみ受理、
`tests/run_tests.py` `TestDraft`、`build_web` 用globは `problems/*.json` のみ）。
スキーマ（`schema/problem.schema.json`）は変更しない。
kinza draftは `solution_usi: []` / `solution_moves: 0` / SFEN内 `?` を含むため意図的にスキーマ非適合のまま staging する。

kinza固有の初期値（図面なしのためgyokuzuより強い留保）:

- `sfen`: `?????????` ×9段＋`b - 1` の81升全 `?` プレースホルダ。持駒は `-` のプレースホルダであり空き・持駒の確定ではない。
  上巻・下巻とも確認範囲に盤面図・駒箱の図示なし。moji-fu（文字譜）解読なしに盤面確定不可であり、
  安易な駒落名（例: 二枚落＝飛角落）からの持駒・盤上配置の決め打ちは禁止（`drafts/001.json` `notes` のSFEN案・gap）。
- `solution_usi: []`、`solution_moves: 0`（USI化確定分なし）。
- `intended_solution_usi/moves: null`（`intended_solution_source` に進捗のみ記録）。
  `null`＋本フィールドのみは正規の中間状態であり欠陥ではない（`docs/provenance.md` 二系統記録、`docs/validation.md` intended節）。
- `status.*_verified: false`、`verification.needs_manual_review: true`。
- `source.page` は読んだ範囲を直記し、丁未確定ならその旨を明記する（本書§3）。
  盤面・手順の実体は必ずNDL一次資料スキャンの直接読取とし、第三者KIF・将棋サイトはタイピング補助にも使わない
  （`CONTRIBUTING.md` Ground rules 1–2、`docs/data-policy.md` §§3–4）。

手順:

1. **draft作成**: `drafts/NNN.json`（`NNN` は3桁ゼロ埋め、001〜054）を既存draftを雛形に作成する。
   `id` は `kinza-NNN` かつ `{collection_id}-{number:03d}` と一致させること。
   必須素性は gyokuzu `DRAFT_REQUIRED`（`id, collection_id, number, author, published_year, period,`
   `sfen, solution_usi, solution_moves, status, verification, source, rights`）に準じる。
2. **`--draft` 検証**: `python3 tools/validate.py --draft`（引数なしで `collections/*/*/drafts/*.json` を自動探索）または対象ファイルを明示する。
   終了コード0は「errorなし（gap/warningは許容）」を意味する。`gap:` 行が残件リストとなる。errorは必ず修正する。
   緩和内容は `docs/gyokuzu-transcription.md` §1（`validate_draft_record`）に準じる:
   SFEN内 `?` 許容（`?→1` 置換後に構文のみ検査し盤依存検査はgap化）、
   `solution_usi: []` 許容（solution walkをskipしgap化）、
   `intended_*` は盤不完全時は構文・件数のみ検査、`needs_manual_review: true` は警告（失敗ではない）。
3. **gap解消**: 出力された `gap:` を `notes` 内の `gap:` 行および列翻刻メモに反映し、
   原寸高解像（IIIF `full`、`https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/full/full/0/default.jpg`）再読で1件ずつ潰す。
   推測で埋めない（本書§2）。軽量版（例 `1200px`、`1024,`）は作業仮読までとし、確定読取は `full` で行う。
   取得・命名・検証（SOI/EOI・非0バイト・欠番なし）は `docs/data-acquisition.md` §§2–3に従い、
   画像はリポジトリに置かず一時作業領域に保存する。
4. **`problems/` 移動**（将来）: `?` がゼロかつ `solution_usi` 非空になったdraftは
   `validate_draft_record` が内部で `validate_record`（strict）に委譲する。すなわち完成draftの `--draft` 通過＝strict同等。
   error/gapゼロを確認してから `collections/edo/kinza/problems/NNN.json` へ移動する（ファイル移動のみ。内容書換えで辻褄合わせをしない）。
5. **通常validate → tests → build**: 移動後に通常検証 `python3 tools/validate.py <problems/NNN.json>`、
   全件スイート `python3 tests/run_tests.py`（CIも同内容）を通す。
   `needs_manual_review: true` は警告でありCI失敗にしないが、維持したままにする（本書§6）。
   公開物は `problems/*.json` のみから生成するため（`build_web` glob）、`drafts/` 残置物が本番に混入しないことを確認する。

## 2. ?台帳の運用（gyokuzu §2準用・kinza拡張）

`?` は「不明升」の正規記録であり、欠陥ではない。検証器は `?` を数えて `gap: sfen has N '?'` として台帳化する。

- **記録**: kinzaの初期値は81升全 `?`（`?=81`）。読めない升は `?` のまま残す。
  `notes` に列翻刻メモ・SFEN案・`gap:` 行を持ち、
  例: `gap: 盤面81升? (図面なし・文字譜未解読)・持駒未確定(「-」はプレースホルダ)・solution全手・intended全手(USI化)・…`。
  `?` の数・字種候補・小字／くずし起点未確定・列境界未確定・手順未USI化を列挙する。
- **持駒 `-` の扱い**: SFEN持駒欄の `-` は構文用プレースホルダであり、持駒なし・駒箱確定を意味しない。
  玉方駒箱（SFEN持駒の小文字部）は盤面確定まで未計上とし（`docs/methodology.md` 駒箱規約:
  駒箱不明時は `-`＋`notes` 明記）、盤面（文字譜）確定後に再計算し `tools/validate.py` の照合を通す。
- **推測補完禁止**: 駒落名・前後番の落名・字種の類推で `?` を埋めない。暫定読の字面列挙を手順として登録しない。
  個人サイト・非政府団体サイトによる補完は禁止（`docs/data-policy.md` §§3–4）。
- **原寸再読条件**: gapの解決条件は原寸高解像（IIIF `full`）での再読と丁特定＋全列翻刻。
  列数・総手数は未計数のまま残し、確定分0手からの積み上げとする。

## 3. 題簽連鎖の追跡法

頁順は右→左（開き内）・R番号順に従う。見開き偶奇仮説（右＝偶数／左＝奇数等）に依らず、RID・左右・題簽を直記する。

- **直記形式**: `source.page` には `NDL PID:<PID> R<7桁><左|右> <漢数字>番 <落名|附録＋平手>` の順序を守る。
  丁未確定の間は `(丁未確定)` を明記する。`推定` による外挿を充填しない
  （`docs/ndl-collation.md` §4、`docs/gyokuzu-transcription.md` §4の形式をkinzaに適用）。
  形式例（各draft `source.page` 実測）:
  ```text
  NDL PID:861193 R0000028左 二十番 左香落 (範囲: R0000028左題簽〜R0000029左二十一番題簽直前。丁未確定)
  NDL PID:861194 R0000004右 二十九番 右香落 (範囲: R0000004右題簽〜同右「三十番」題簽直前。丁未確定)
  NDL PID:861194 R0000025左 附録一番 平手 (範囲: R0000025左題簽〜R0000026右二番題簽前。丁未確定)
  ```
- **`intended_solution_source`**: 読んだPID/canvas（R番号）/列範囲と進捗状態を必ず残す
  （`docs/provenance.md`、`docs/validation.md` の付与条件）。USI `null`＋本フィールドのみは正規の中間状態。
  形式例:
  ```text
  NDL PID:861193 R0000028左-R0000029左(二十一番題簽直前まで)を通読 (USI化未了・小字/くずし起点未確定あり)
  NDL PID:861194 R0000027右〜R0000028左 附録四番 (USI化未了・くずし/小字・升目数字未確定あり)
  ```
- **連鎖の書き方**: 各draft `notes` の「所在特定」に、前証（当該番の前の題簽）・起点（当該番題簽）・後端傍証（次番題簽）を
  R番号・左右付きで記録する。例（`drafts/020.json`）: R0000027左「十八番」→R0000028右「十九番」→R0000028左「二十番」起点→
  R0000029右は題簽なし＝二十番続き→R0000029左「二十一番」後端傍証→R0000030左「二十二番」番号連続の傍証。
  次番への申送り（`No.N以降への申送り`）に起点R・続き頁・裁定事項を残す。
- **題簽なし＝続き**: 題簽なし頁は前番の続きと判定し、題簽なしをもって欠番としない。
  原寸で列境界を裁定する（各draftの申送り定型文: `題簽なし頁が続きであるため、題簽なしをもって欠番とせず原寸で列境界を裁定すること`）。
- **題簽未確認時の `title`**: 題簽未確認のdraftは `title: null` のまま題簽欠載・未確認を示す。番号・落名の推測補完はしない
  （`drafts/010.json`、`drafts/028.json`、`drafts/035.json`、`drafts/036.json`）。
- **`verification.transcribed_from` / `method`**: 盤面PID/RID＋手順PID/RIDを両記する。
  例: `NDL PID:861193 R0000028 / R0000029 (direct image reading; no external sites)`。
  `reference_urls` には国営アーカイブ頁のみを置き、個人・非政府団体URLは一切置かない
  （`docs/data-policy.md` §4、`CONTRIBUTING.md` Ground rule 2）。

## 4. 欠載の扱い

「題簽なし＝続き」と「題簽欠載（番号題簽そのものが確認できない）」と「欠コマ（画像欠落）」を区別する。
いずれも推測補完せず、捜索範囲・前証後証・判定・断定留保を `notes` に記録し、`title: null` を維持する。

- **十番（`drafts/010.json`）**: R0000018〜R0000019の確認範囲に明瞭な十番題簽なし。
  前証＝R0000018右「九番」「飛車落」、後証＝R0000019左「十一番」「飛車落」・R0000020左「十二番」「飛車落」。
  候補範囲はR0000019右左端〜R0000019左結語状1列「右何も…」の見込み。`欠載記録` に捜索範囲・結果・判定（欠載濃厚）・
  断定留保（原寸・丁付け確定までは断定を留保し要原寸再読）を記録。前後番はいずれも飛車落だが十番への推測適用はしない。
- **二十八番（`drafts/028.json`・`collection.json` `edition_note`）**:
  PID861193のR34–R37のいずれにも二十八番題簽を確認できず（R0000035左に二十七番題簽、R0000036両面・R0000037両面・R0000038右のいずれにも番号題簽なし、
  R0000038左は裏表紙）。丁–R対応に破綻は認められないため、欠コマではなく題簽の欠載（変化に含める構成）の疑いとして記録する。
  指定相当位置R0000036（丁29–30相当）をもって二十八番相当とするが、列帰属は未裁定（二十七番続きか二十八番相当かは原寸裁定待ち）。
  落名も推測補完しない。
- **三十五番・三十六番（`drafts/035.json`・`drafts/036.json`）**:
  R0000007は「欠 MISSING」表示の欠コマ、R0000008は題簽なし手順続き。三十五番・三十六番題簽は1200px読取範囲で未確認。
  前方境界＝R0000005左「三十三番」「右香落」・「三十四番」「右香落」、後方境界＝R0000009右「三十七番」「平手」・左「三十八番」「平手」。
  落名（右香落連続の終端・平手への切替点）は原寸確定待ちで推測補完しない。PID取り違え注意:
  上巻PID861193のR0000035–R0000036は上巻二十六番〜二十七番域であり、下巻No.35–36の直接根拠としない。
- **運用**: 欠載疑いのdraftは `source.page` に `題簽欠載` / `題簽未確認` を明記し、
  `intended_solution_source` に通読範囲＋帰属未確定を残す。原寸で丁–R対応と列境界を裁定するまで番号体系を動かさない
  （総題数54の内訳は `collection.json` の確定値を維持する）。

## 5. 附記号・落名変化の記録法

### 5.1 附記号

意味付け・USI化はせず、目視列挙＋帰属未確定の明記に留める。全て要原寸再読。

- **○印**: 変化・合印候補の丸囲み記号。確認例: 春・夏・秋・冬・イ・ロ・ハ・口・八・二・千・ホ・ヘ・風・花・萩・鳥・又・金・飛 等。
  例: `「○春」+「上手方」`、`「○イ」+「後手方」`、`「○夏」+「下手方」+「附」`。○印が変化か合印か・分岐帰属は断定しない。
- **返し・打**: 「同」（同升の意味と見られるがUSI化はしない）、「附／付」（例: `五六歩付`、`五七歩附`、`七八飛附`、
  `同飛附`）、「打／打てよ」（例: `五八角打`、`荒飛角打てよ`、`飛角打てよ`）。
- **末尾・手合表示**: 「上手方」「上手方右」「下手方」「後手方」「先手方」、
  「上手より（指す）」「下手方より指す」「後手より」「先手より」「出手方」「同請」等。
  本文では「上手方／下手方」系、附録・下巻後半では「後手方／先手方」系が現れるが、機能の切り分けは断定しない。
- **短文・結語状**: 頁内・番尾のくずし短文・結語候補。確認例: `いづれも…`、`以上…`、`右何も…`、
  `下手方全く〜宣流とするなり`、`上手方指悪`、`文手指悪`、`為一方悪`、`落一方宣`、`香の弱さ` 状等。
  帰属・内容は未確定として記録する。
- **小字・合印・手書注記**: 小字升目数字・起点小字・合印候補・枠外注記・手書注記（例: R0000008左中央の手書注記は二番側に属するため一番draftには取り込まず存在のみ記録）。
  低解像では段筋の1字違い・小字の有無は未確定とし、確定読取不可と明記する。
  小字読順の作業仮説（`drafts/018.json` 十八番所見）: 小数字2字は視覚左→右＝筋→段（C6「一八飛」「七六銀」でanchor）。
  C2-2「六七歩」の七六逆読可能性は未確定要素として残す。全番への一般化は未確定であり、USI化の根拠に単独で用いない。

### 5.2 落名変化

題簽の落名は画像通り記録し、前後番との同一・変化を `題簽` 項に一文で残す。推測適用はしない。
本文の駒落と附録の「平手」を混同しない。

| 番 | 落名（各draft `題簽` 項の実測） | 切替点メモ |
|---|---|---|
| 一番〜四番 | 二枚落 | 一番題簽に書名・著者・校正者（「将碁絹篩」「福島順碁著」「大橋銀英校正」）を伴う。表記ゆれは画像通り＋注記 |
| 五番〜八番 | 飛香落 | 五番で二枚落→飛香落に変化（`drafts/005.json`） |
| 九番〜十四番 | 飛車落 | 九番で飛香落→飛車落に変化（`drafts/009.json`）。十番題簽は未確認のため前後番からの推測適用なし |
| 十五番〜十九番 | 角行落 | 十五番で飛車落→角行落に転じる最初の題（`drafts/015.json`） |
| 二十番〜二十四番 | 左香落 | 二十番で角行落→左香落に替わる（`drafts/020.json`） |
| 二十五番〜三十四番 | 右香落 | 二十五番で左香落→右香落へ切替（`drafts/025.json`）。三十五番・三十六番題簽は未確認のため終端判断をせず原寸に委ねる |
| 三十七番〜五十番 | 平手 | 三十七番で右香落→平手へ替わる（`drafts/037.json`）。三十五番・三十六番の落名は原寸裁定待ち |
| 附録一番〜四番 | 平手（落名ではなく「平手」） | `附録`＋漢数字＋平手。例: R0000025左「附録」「一番」「平手」。本文の駒落と混同しない。本文終頁に大字「将碁絹篩 終」、附録尾部に「附録終」、奥付に書林（大坂4軒＋東京6軒計10軒）を確認 |

表記ゆれの扱い: 画像表記（「将碁絹篩」「福島順碁」等）は画像通り記録し、`collection.json` のNDL書誌正書（「将棋絹篩」「福島順棊」）との
表記ゆれとして注記で区別する（`drafts/001.json` 題簽項、`collection.json` `edition_note`）。
校正者末字「正」は「校正」の略記と見られるが断定せず要原寸再読。

## 6. 本番昇格条件（gyokuzu §3準用）

`drafts/` → `problems/` の昇格条件（すべて必須）:

1. **`?` ゼロ**: SFEN内に `?` がないこと。kinzaでは文字譜からの初形復元（配置・持駒・手番の実質確定）が条件。
   残存する限り draft 扱いであり strict（`validate_record`）は拒否する。
2. **`solution` 確定**: `solution_usi` 非空、`solution_moves == len(solution_usi)`、
   strict の solution walk（合法歩行・王手連続・最終局面の詰み＝玉方全応手ゼロ）通過。
   空手順のまま昇格しない。`solution_usi` は検証解（詰み保証側）のみを担い、`intended_*` からのコピーはしない
   （`CONTRIBUTING.md` Ground rule 5）。
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

`solution_verified` は昇格時点でも strict の線形保証（記録線上の合法・連続王手・最終詰み）のみを主張する。
余詰・最長抵抗・完全分岐は範囲外であり `unique_solution_verified` は `false` のまま残す（`docs/validation.md`）。

## 7. 進捗現状と次のマイルストーン（ファイル実測・エンジン新規実行なし）

本節は `collections/edo/kinza/` のファイル実測のみに基づく進捗台帳である。
`tools/validate.py`・solverの新規実行は行っていない。

- **draft件数**: `drafts/` に `001.json`〜`054.json` の54件あり。
  目標54件（`collection.json` `problem_count: 54`、上巻28題＋本文22題＋附録4題）に到達。新規draft作成の残件なし。
- **原典翻刻（intended）USI化率**: **0%**（`intended_solution_usi: null` が54/54件、
  `status.intended_solution_verified: false` が54/54件。ファイル内容検索による実測）。
  `intended_solution_source` にPID/RID/列範囲＋進捗（`USI化未了・くずし未確定あり` 等）を
  記録した正規の中間状態であり、欠陥ではない（`docs/provenance.md` 二系統記録、`docs/validation.md` intended節）。
- **正規手順（solution）確定率**: **0%**（`solution_usi: []`＋`solution_moves: 0` が54/54件。ファイル内容検索による実測）。
- **盤面**: 確認したdraftはいずれもSFEN81升全 `?`＋持駒 `-` の構文用プレースホルダ。上巻・下巻とも図面なし・文字譜未解読のため、
  初形・持駒ともに未確定。文字譜解読なしの盤面確定・大文字化による先後決め打ちは禁止。
- **本番昇格**: **0件**。`collections/edo/kinza/problems/` は不存在であり、
  `collection.json` `problems_transcribed: []` を維持する。`drafts/` は `problems/` と厳密分離するため、draft件数は昇格件数に含めない。
- **`needs_manual_review`**: `true` が54/54件（ファイル内容検索による実測）。昇格後も維持する方針（§6）に整合する。

他文書との整合（矛盾なし）:

- `collection.json`（`problem_count: 54`、`problems_transcribed: []`＝未転記）:
  draft 54件は staging であり `problems_transcribed` に含めないため矛盾しない。
- `collection.json` `edition_note`（総題数54内訳・二十八番題簽欠載疑い・R0000034二十六番右香落／R0000035二十七番右香落の連続確認）:
  本書§4の欠載扱い・§5.2の落名表と一致する。
- `docs/provenance.md`（二段階転記 Stage 2、`intended null`＋`intended_solution_source` は正規中間状態）・
  `docs/validation.md`（intendedは合法再演のみ・`null` はskip）・
  `docs/methodology.md`（玉方駒箱未確定時は `-`＋`notes` 明記・二系統記録・KIF/日本語表記は生成物）:
  本書の「intended 0%＝異常ではない」「駒箱未計上を残件とする」扱いと一致する。
- `docs/data-acquisition.md`・`docs/ndl-collation.md`・`docs/data-policy.md` §§1–4:
  本書はNDL一次資料・本リポジトリ内文書のみを根拠とし、個人サイト・非政府団体サイトの参照・記載を追加しない。

次のマイルストーン（順序固定）:

1. **draft 54件完**: 達成（`001`〜`054` が `drafts/` に存在）。
2. **全列翻刻**: 原寸高解像（IIIF `full`）再読で文字譜の全列翻刻＋列境界裁定（§3）。推測補完は禁止。
   欠載疑い（十番・二十八番・三十五番・三十六番）は原寸で丁–R対応と列境界を裁定する（§4）。
3. **USI化（intended→solution）**: 列の文節・手番確定後に `intended_solution_usi/moves` を充填し
   `intended_solution_source` にPID/canvas/列範囲を残す（§3）。
   `solution_usi` はstrictのsolution walk（合法歩行・王手連続・最終詰み）通過を条件とする（§6）。
4. **昇格**: `?` ゼロかつ `solution` 確定のdraftのみ `problems/` へ移動し、
   通常validate → `tests/run_tests.py` → `build_web` を通す（§1手順4–5）。
   `needs_manual_review: true` は維持したままとする（§6）。
