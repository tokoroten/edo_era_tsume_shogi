# NDL Collation（canvas ↔ 丁 ↔ 問題番号対応メモ）

作成日: 2026-09-16
範囲: NDL PID 861211（図巧・58コマ）・861212（詰手書・36コマ）の対応関係整理のみ。
新規転記・既存レコードの改訂は行わない。

情報源の制限: 本書の根拠は **NDL画像読取所見のみ** とする。
典拠は国立国会図書館（NDLサーチ / NDLデジタルコレクション / IIIF manifest）と
本リポジトリ内文書（`docs/data-acquisition.md`、`docs/research.md`、
`docs/provenance.md`、`docs/validation.md`、`collections/edo/zukou/*.json` の
NDL読取記載）に限定する。**個人サイト・非政府団体サイトは参照・記載しない**
（`docs/data-policy.md` §§1–4、`docs/data-acquisition.md` §1）。

関連文書:

- 取得・URL・命名の正本: `docs/data-acquisition.md`
- 書誌・版特定: `docs/research.md` §1.1、§10
- 来歴・二段階転記: `docs/provenance.md`
- 検証・不一致時手順: `docs/validation.md`
- 版注記正本: `collections/edo/zukou/collection.json` `edition_note`

状態凡例（本書で統一）:

- `確定`: NDL画像の直接読取で文言・位置まで確認済みの所見。
- `申告`: 問題JSON等に PID / RID が記載されているが
  `verification.needs_manual_review: true` かつ `source.page: null` のもの
  （画像照合未了。対応候補として扱う）。
- `推定`: 確定点からの規則性外挿。単独では `source.page` に採用しない。
- `未確定`: 読取・照合が足りず結論できないもの（§5）。

注意: 全100問の `source.page` は現時点で `null` のままである
（`docs/provenance.md`）。本書の対応表は照合作業用の作業メモであり、
`source.page` への充填は個別の原典照合をもって行う。
確定版特定までは全件 `needs_manual_review: true` を維持する
（`docs/research.md` §1.1、`collection.json` `edition_note`）。

## 1. IIIF規則（両PID共通）

詳細・再現手順の正本は `docs/data-acquisition.md` §2–§3。本書は要点のみ抜粋する。

### 1.1 manifest と画像URL

```text
manifest: https://dl.ndl.go.jp/api/iiif/<PID>/manifest.json
画像:     https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/full/<サイズ>/0/default.jpg
canvas:   https://dl.ndl.go.jp/api/iiif/<PID>/canvas/<N>
```

実例（`docs/data-acquisition.md` §2.1–§2.2）:

```text
https://dl.ndl.go.jp/api/iiif/861211/manifest.json
https://dl.ndl.go.jp/api/iiif/861212/manifest.json
https://dl.ndl.go.jp/api/iiif/861211/R0000001/full/full/0/default.jpg
https://dl.ndl.go.jp/api/iiif/861212/R0000036/full/full/0/default.jpg
```

- `<PID>`: `861211`（`将棋図巧・将棋図巧詰手.将棋図巧`）/
  `861212`（`将棋図巧・将棋図巧詰手.将棋図巧詰手`）。
  いずれも NDLBibID `000000493927`、請求記号 `209-461`、
  DOI `10.11501/<PID>`、`Access Restrictions: PDM`
  （manifest `metadata` 実測、`docs/data-acquisition.md` §2.1）。
- `<サイズ>`: `full` が原寸。軽量版のみ `1024,` 等を使う。
- 保存名規約: `<WORK_DIR>/ndl_<PID>/<NNN>.jpg`
  （`<NNN>` = canvas番号3桁ゼロ埋め、`<WORK_DIR>` = 作業用一時ディレクトリ）。
  画像はリポジトリに置かない（`docs/data-acquisition.md` §3.2）。

### 1.2 canvas番号 ↔ RID

manifest `sequences[0].canvases[]` 実測（`docs/data-acquisition.md` §2.3）:

```text
canvas N  <->  RID = "R" + N を7桁ゼロ埋め
```

- `canvas/1` ↔ `R0000001`、`canvas/10` ↔ `R0000010`、
  `canvas/58` ↔ `R0000058`（861211）、`canvas/36` ↔ `R0000036`（861212）。
- 総canvas数: 861211 = 1–58（計58）、861212 = 1–36（計36）。
- **canvas番号は撮影順の通し番号であり、原資料の丁付け・問題番号と同一ではない**
  （`docs/data-acquisition.md` §2.3）。対応付けは本書§2–§3の作業とする。

### 1.3 画像寸法

`docs/data-acquisition.md` §3.3 の manifest `width` / `height` 実測を目安とする
（個別canvasの微差・回転の有無は要確認。JPEG正当性は SOI/EOI・非0バイト・
欠番なしで判定する）:

- 861211: `3751x3025`
- 861212: `3698x2881`

## 2. PID 861211（図巧・58コマ）頁対応

### 2.1 外形と作業原則

- 総58コマ（canvas 1–58）。書誌形態は `2冊 (50, 32丁)` のうち図巧側が 50丁
  （`docs/research.md` §1.1）。丁数とコマ数の差は表紙・序・目録・裏表紙等の
  前後付録による。内訳の丁単位確定は未了（§5）。
- エージェント報告の整理による作業原則（いずれも `推定`。全件照合で確定させる）:
  1. 見開き撮影では **右 = 偶数番、左 = 奇数番**。
  2. `010.jpg` 右 = 十番。以降おおむね1コマ2番で進む。
  3. `055.jpg` = 百番（単頁報告あり。見開き最終部のレイアウトは要再確認）。
  4. 盤図の標準向きは **上が rank 9 側**（SFENの段順との対応付けの作業仮説。
     回転指定は IIIF 上は `0`。個別盤面の確定は照合時に行う）。

### 2.2 確定・申告対応点（NDL読取が根拠のもののみ）

| canvas / RID / ファイル | 問題番号・内容 | 状態 | 根拠 |
|---|---|---|---|
| canvas 7 / R0000007 / 007.jpg | No.4＋No.5（見開き2番分） | 申告（画像照合未了） | `problems/004.json`・`005.json` の `source.identifier` が `PID:861211 / R0000007`。`notes` に「原典画像との照合は未了」と明記 |
| canvas 11 / R0000011 / 011.jpg 右 | No.12（十二番、右頁） | 確定（位置）・盤面読取は係争中 | `problems/012.json` の `verification.method`・`notes`（原典拡大照合）。初段の駒種は未確定（§5.1） |
| canvas 15 / R0000015 / 015.jpg | No.20盤面（盤下持駒欄は空白との読取） | 確定（位置・空白の読取） | `problems/020.json` `notes`・`verification.method`（`PID:861211 R0000015` との照合）。系統不一致の警告あり（§5.2） |
| canvas 10 / R0000010 / 010.jpg 右 | 十番 | 推定（報告整理） | エージェント報告の集約。左頁（九番か）の確定読取なし |
| canvas 55 / R0000055 / 055.jpg | 百番（単頁との報告） | 推定（報告整理） | エージェント報告の集約。単頁の理由・隣接頁の有無は要再確認 |

上記以外の canvas 1–6（前付）、12–14・16–54（本文中間部）、56–58（後付）の
丁・番号対応は未確定（§5）。`2N-10 / 2N-9` 型の機械的外挿を `source.page` に
書き込まないこと。

### 2.3 本文部の読み方（作業メモ）

- R0000007 = No.4＋No.5、R0000011右 = No.12、R0000015 = No.20 は、
  「右=偶数・左=奇数」「1コマ2番」と整合する。ただし起点（No.1 の所在）と
  終点（No.100 単頁の扱い）が未確定のため、中間部を等差で埋めない。
- 前付（canvas 1–5付近）と後付（canvas 56–58付近）の内容（表紙・序・目録・
  奥付等の配分）は丁単位で読み直す必要がある。
- 盤面の向きは「上 = rank 9」仮説で SFEN 化作業を進め、照合時に盤外情報
  （持駒欄・丁付・柱刻）でも確認する。

## 3. PID 861212（詰手書・36コマ）丁付け

### 3.1 外形

- 総36コマ（canvas 1–36）。書誌形態 `2冊 (50, 32丁)` のうち詰手書側が 32丁
  （`docs/research.md` §1.1）。
- エージェント報告の整理による骨格（丁番号の読取再確認を要する。`推定`）:
  `001` 表紙 〜 `036` 裏表紙、本文は丁1表 〜 丁32表・奥付。
- 本文丁と問題番号の全対応は未確定。確定点のみ§3.2に記す。
  1丁あたり複数番が入る頁と、跨ぎ（複数頁にまたがる番）があるため、
  丁番号からの機械的割付けは行わない。

### 3.2 確定・申告対応点

| canvas / RID / ファイル | 丁・内容 | 番号 | 状態 | 根拠 |
|---|---|---|---|---|
| canvas 1 / R0000001 / 001.jpg | 表紙 | — | 推定（報告整理） | エージェント報告の集約。表紙題簽の読取再確認を要する |
| canvas 8–9 / R0000008-9 / 008.jpg左 〜 009.jpg右 | 本文（全5列） | 二十番 | 確定（位置・列数）。手順のUSI化は未了 | `problems/020.json` `intended_solution_source`・`verification.method`・`notes`（`R0000008-9, all 5 columns`、`008左〜009右二十番`） |
| canvas 32–34 / R0000032-34 / 032–034.jpg | 附載 | — | 推定（報告整理） | エージェント報告の集約。附載の開始・終了丁の読取再確認を要する |
| canvas 35 / R0000035 / 035.jpg | 跋文（文政辛巳夏・北林堂・将碁絶妙 全二冊 等） | — | 確定 | `docs/research.md` §1.1（詰手書R0000035高解像読取で確定）、`collection.json` `edition_note`。層A=文政4年(1821)跋、層B=明治・吉川半七文王囲再版系の版特定根拠 |
| canvas 36 / R0000036 / 036.jpg | 裏表紙（奥付面を含む報告あり） | —（奥付: 文王囲将碁目録16点・吉川半七・東京日本橋区南傳馬町） | 跋文・奥付の文面は確定、canvas配分は要再確認 | `docs/research.md` §1.1、`collection.json` `edition_note`。丁32表・奥付の対応関係は§5 |
| 丁1表 〜 丁32表 | 本文（32丁） | No.1–No.100（配分未確定） | 骨格のみ推定 | 形態32丁（`docs/research.md` §1.1）。番号↔丁の全表は未作成 |

### 3.3 報告された確定事項（再確認付きで引き継ぐもの）

- 二十番は `008左 〜 009右` にまたがる（上記§3.2の通り確定）。
- 二十二番の跨ぎは確定: `R0000009` 内完結（丁6裏 〜 丁7表）。
  `R0000010` には掛からない。列範囲の読み直しは§5.4に残すが、
  対象canvas・丁範囲自体は確定とし `推定` から格上げする。
- 附載は `032–034`、跋文は `035` との報告がある。跋文の文面自体は確定
  （§3.2）だが、附載の丁範囲と `036`（裏表紙・奥付）の配分は読み直す。
- 奥付「文王囲将碁目録」16点・「吉川半七」「東京日本橋区南傳馬町」の文面は
  確定（`collection.json` `edition_note`）。現スキャン本 = 明治期「東京 吉川半七」
  再版系（文王囲叢書の一冊）、底本 = 文政期・伊藤宗看『将棊絶妙』系の跋を再録、
  との版特定所見も同所見による。表記ゆれ「将碁／将棊／将棋」は画像通り＋注記で保持。

### 3.4 source.page 充填用メモ（NDL読取確定分の作業メモ）

`source.page` への転記は `docs/provenance.md` の手順による。
本節は充填時に丁・面・RIDを添えるためのメモであり、転記自体は未了:

- 51番: `R0000016` 左（丁14表）題簽にて確定。`source.page` 充填時は
  丁14表・左・`R0000016` を明記する。
- 52番: `R0000017` 右（丁14裏）。`source.page` 充填時は
  丁14裏・右・`R0000017` を明記する。
- 54番: `R0000017` 左（丁15表）。`source.page` 充填時は
  丁15表・左・`R0000017` を明記する。
- 22番: `R0000009` 内完結（丁6裏 〜 丁7表）。`R0000010` に掛からない。
  `source.page` 充填時は丁6裏 〜 丁7表・`R0000009` を明記し、列範囲を添える。
- 53番は未確定のまま残す（§5.3）。`推定` による補完を `source.page` に採用しない。

## 4. 運用（照合が済むまでの扱い）

- 本書の `推定` を `source.page` に転記しない。`source.page` は NDL画像を
  直接読んだ番のみ、丁・頁・番を添えて充填する（`docs/provenance.md`）。
- `intended_solution_source` には読んだ PID / canvas（R番号）/ 列範囲と
  進捗状態（USI化未了・くずし未確定あり等）を必ず残す
 （`docs/provenance.md`、`docs/validation.md`）。
- 系統不一致（例: No.20）は `solution_usi` を書き換えず、両系統を保持して
  `notes`＋`verification.method` に PID / 列を記録し、
  `needs_manual_review: true` を維持する。別伝隔離は独立系統の陽性確認後のみ
  （`docs/validation.md`、`docs/provenance.md`）。

## 5. 未確定事項一覧

### 5.1 No.12 初段論争（861211 R0000011）

- 位置は確定: `011.jpg` 右 = 十二番（`problems/012.json`）。
- 初段の読取が係争中:
  - 当初読取で `5+rl1s → 5sl1r` に修正（f4=銀・f1=飛を確認、f3=香維持の主張）。
  - 修正後に現行21手手順の6手目 `1a2b` が不成立となり `validate` FAIL。
  - 第三読取 `5sr1l` でも手順不成立。
  - 結果として検証通過する原状 `5+rl1s` に復帰（他段・持駒・`solution_usi` 不変）。
  - 原典拡大での別読取: f4=銀 90–95%、f1=香 85–90%、f3=飛 65–75%
    （`5sr1l` 相当）との記録もあるが、現行21手手順（6手目 `1a2b`）と両立しない。
- 解決条件: 手順再構築または別伝本照合。現状は原状維持＋
  `needs_manual_review: true`（`problems/012.json` `notes`）。

### 5.2 No.20 系統不一致（861211 R0000015 × 861212 R0000008-9）

- 図巧二十番盤面（`PID:861211 R0000015`、盤下持駒欄は空白との読取）と、
  詰手書二十番翻刻（`PID:861212 R0000008-9`、全5列、USI化未了・くずし未確定あり）が、
  現行37手正規手順と初手から系統不一致（No.19 / No.21 との取違えは否定済み）。
- 打駒を要する作意のため印刷脱落の疑いとの読取メモあり。
- 取扱い: 現行手順・持駒を維持し、警告保持＋別伝本照合待ち。別伝候補としての
  隔離は独立伝承の陽性確認後のみ（`problems/020.json`、`docs/validation.md`
  Mismatch handling、`docs/provenance.md`）。

### 5.3 51番確定・53番未確定

- 51番は確定: `R0000016` 左（丁14表）題簽にて確認。`source.page` 充填用メモは
  §3.4 に記す（充填自体は `docs/provenance.md` の手順による）。
- 53番は未確定のまま残す。対象canvas・丁・読取内容の特定からやり直す。
  未読のまま `source.page` に採用しない。

### 5.4 その他の残照合

- 861211: 前付（canvas 1–5付近）の丁構成、No.1起点、本文中間部（canvas 12–14・
  16–54）の全対応、No.100単頁（canvas 55）の隣接頁関係、後付（canvas 56–58）の
  丁構成、盤面の向き（上 = rank 9）の個別確定。
- 861212: 表紙（001）・本文丁1表 〜 丁32表の番号配分全表、22番跨ぎの列範囲の
  読み直し（対象canvas・丁範囲は確定: `R0000009` 内完結・丁6裏 〜 丁7表、§3.4）、
  53番の対象canvas・丁・読取内容の特定、附載（032–034報告）の丁範囲確定、
  跋文（035確定）と奥付・裏表紙（036）の丁・面配分確定。
- 共通: `source.page` 全件 `null` の解消、`needs_manual_review` の解除は個別照合後に
  行う。画像寸法の個別確認と `docs/data-acquisition.md` §3.3 の全件検証も残る。
