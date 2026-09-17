# NDL Access（国立国会図書館デジタル資料へのアクセス手順）

作成日: 2026-09-17
情報源の制限: 本書の書誌・URL・仕様は `docs/research.md`、`docs/provenance.md`、
および国立国会図書館（NDLサーチ / NDLデジタルコレクション / IIIF manifest）のみに基づく。
個人サイト・非政府団体サイトは参照・記載しない（`docs/data-policy.md` §§1–4）。

本書はアクセス方法・URL規則・取得マナーの正本とする。
具体的な取得手順・保存命名は `docs/data-acquisition.md`、
canvas と丁・問題番号の対応は `docs/ndl-collation.md` に従う。

公開文書のため、本書にローカルマシンの絶対パス・ユーザー名は記さない。
作業用一時ディレクトリは `<WORK_DIR>` と表記し、実行時に指定する。

## 1. 書誌からデジタル資料への到達手順

1. NDLサーチで書誌を特定する（書誌ID = NDLBibID）。
   例: `https://ndlsearch.ndl.go.jp/books/R100000002-I000000493927`
2. デジタルアーカイブ入口で同 BIBID を検索する。
   `https://dl.ndl.go.jp/search/searchResult?identifierItem=BIBID&identifier=<NDLBibID>`
3. デジタルの単位ごとに PID（数字）が付く。1書誌が複数PIDに分かれることがある
   （例: 図巧は上巻相当 `861211`・下巻相当 `861212`）。
4. 各PIDの manifest を取得し、`metadata` で書誌の一致を確認する
   （Title / Call Number / Bibliographic ID / DOI `10.11501/<PID>`）。

## 2. 利用条件の確認

- manifest の `metadata` 内 `Access Restrictions` を確認する。
  本プロジェクトで扱う資料は `PDM`（パブリックドメイン相当）であることを確認済み。
- manifest の `license` が指す NDL公式ヘルプに従う。
- 原作品 Public Domain・転記データ CC0-1.0・コード MIT の整理は
  `docs/research.md` §7、`docs/copyright.md` に従う。

## 3. IIIF manifest の読み方

```text
https://dl.ndl.go.jp/api/iiif/<PID>/manifest.json
```

確認する項目:

- `metadata`: Title / Call Number / Bibliographic ID / DOI / Access Restrictions
- `sequences[0].canvases[]`: 撮影コマの一覧。各 canvas の `@id` は
  `https://dl.ndl.go.jp/api/iiif/<PID>/canvas/<N>` の形式
- 各 canvas の `images[0].resource.@id` が画像URLの正本
  （`docs/data-acquisition.md` §2 の実測と突き合わせる）
- 総canvas数（例: 861211 = 58、861212 = 36）

## 4. IIIF Image API のURL規則

```text
https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/<region>/<size>/<rotation>/<quality>.<format>
```

本プロジェクトの標準形:

```text
https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/full/full/0/default.jpg
```

各要素:

- `<PID>`: デジタル単位（例: `861211`）
- `<RID>`: 画像ID。`R` + canvas番号の7桁ゼロ埋め（§5）
- `<region>`: `full` = 全体。部分切出しは `x,y,w,h`（ピクセル指定）
- `<size>`: `full` = 原寸。軽量版が要る場合のみ `full` 以外（例: `1024,` = 幅1024px）
- `<rotation>`: `0` = 回転なし
- `<quality>.<format>`: `default.jpg`

### 4.1 部分切出し（region）の使い方

- 書式: `<x>,<y>,<w>,<h>`（左上起点のピクセル）。サーバー側で切り出されるため、
  全体取得後の再エンコードより原寸の fidelity が高い。
- 和装本の見開きは1画像=2頁の場合がある。幾何学的半分（`floor(幅/2)`）で
  左右頁を分離できる。綴じ溝（暗部）が中心からずれることがあるため、
  溝の位置は輝度プロファイル等で確認し、対向頁の枠が混入しない側に寄せる。
- 各画像の `info.json`（`https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/info.json`）で
  `width` / `height` / 対応機能（`regionByPx` / `sizeByWh` 等）を事前確認する。
- 切出し定義は `PID / region / size` の3点で記録し、再現可能にする
  （例: `R0000020 / 0,0,1649,2832 / full`）。

## 5. canvas番号とRIDの対応規則

manifest `sequences[0].canvases[]` の実測:

```text
canvas N  <->  RID = "R" + N を7桁ゼロ埋めしたもの
```

例: `canvas/1` ↔ `R0000001`、`canvas/36` ↔ `R0000036`。

注意: canvas番号は撮影順の通し番号であり、原資料の丁付け・問題番号と同一ではない。
対応付けは `docs/ndl-collation.md` の作業とする。

## 6. 取得マナーと検証

- 逐次取得とし、リクエスト間に待機時間（例: 1秒）を置く。並列 hammering はしない。
- `User-Agent` ヘッダを付ける。失敗時は指数バックオフで再試行（例: 最大3回）。
- 取得済みファイルは飛ばす（サイズ0のものは再取得）。
- 検証: 非0バイト、先頭 `FF D8`（SOI）・末尾 `FF D9`（EOI）、連番の欠番なし。
  疑わしい小サイズは manifest の `width` / `height` と突き合わせる。
  詳細は `docs/data-acquisition.md` §3.3。
- 画像ファイルはリポジトリにコミットしない。作業用一時ディレクトリ
  （`<WORK_DIR>/ndl_<PID>/`）のみに置く。

## 7. 対象書誌一覧（本プロジェクト）

詳細は `docs/data-acquisition.md` §1、`docs/research.md`。

| 作品 | NDLBibID | PID | 状態 |
|---|---|---|---|
| 将棋図巧（上巻相当） | 000000493927 | 861211（58コマ） | 取得済み |
| 将棋図巧詰手（下巻相当） | 000000493927 | 861212（36コマ） | 取得済み |
| 将棋無双（原書名「象戯図式」） | 000001281469 | なし（インターネット公開なし確定・2026-09-17） | 原書は宮城県図書館伊達文庫所蔵（代替資料存否:無し）。NDL代替所蔵は古図式全書PID:2526139（館内限定）。詳細は `docs/research.md` §1.2 |
| 将棋玉図（上・下） | 000000493916 | 861197 / 861198 | 取得済み（詳細は `docs/gyokuzu-transcription.md`） |
| 将棊絹篩（上・下） | 000000493914 | 861193 / 861194 | 取得済み（詳細は `docs/kinza-transcription.md`） |
