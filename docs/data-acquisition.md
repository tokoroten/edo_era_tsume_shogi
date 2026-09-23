# Data Acquisition（NDL IIIF 再現手順）

作成日: 2026-09-16
情報源の制限: 本書の書誌・URL・仕様は `docs/research.md`、`docs/provenance.md`、
および国立国会図書館（NDLサーチ / NDLデジタルコレクション / IIIF manifest）のみに基づく。
個人サイト・非政府団体サイトは参照・記載しない。

## 1. 対象書誌（`docs/research.md` より整理）

| 作品 | 著者 | 刊年 | NDLBibID | 請求記号 | NDLサーチ | デジタル上の単位（PID） |
|---|---|---|---|---|---|---|
| 将棋図巧（上巻相当） | 伊藤看寿 | 宝暦5年（1755年） | 000000493927 | 209-461 | https://ndlsearch.ndl.go.jp/books/R100000002-I000000493927 | 861211（`将棋図巧・将棋図巧詰手. 将棋図巧`） |
| 将棋図巧詰手（下巻相当） | 伊藤看寿 | 同上 | 000000493927 | 209-461 | 同上 | 861212（`将棋図巧・将棋図巧詰手. 将棋図巧詰手`） |
| 将棋無双（原書名「象戯図式」） | 三代伊藤宗看 | 享保19年（1734年） | 000001281469 | W431-4 | https://ndlsearch.ndl.go.jp/books/R100000002-I000001281469 | PID未特定・画像未取得（`docs/research.md` §10 の復製本の書誌。原典画像との照合時にPIDを特定し記録する） |

補足（`docs/research.md` §1.1、§10 に基づく）:

- 図巧の書誌事項: タイトル `将棋図巧・将棋図巧詰手`、著者 `伊藤看寿 著`、出版者 `文玉圃`、
  形態 `2冊 (50, 32丁); 16cm、和装`、原本代替記号 `YDM76178`、全国書誌番号 `40076504`。
- 図巧のデジタルアーカイブ入口:
  https://dl.ndl.go.jp/search/searchResult?identifierItem=BIBID&identifier=000000493927
- 無双の書誌事項: NDL『象戯作物』（1970年古棋書復刻委員会による享保19年版の復製。序題は「象戯図式」）。
  享保版は伝本間で図の異同（版木修正）があるため、`source.edition` で版・伝本を区別する（`docs/research.md` §1.2、§10）。
- 原作品はいずれも Public Domain（`docs/research.md` §7）。転記データは CC0-1.0、コードは MIT。
- 本書は取得・保存の再現手順のみを扱う。転記・検証の規約は `docs/methodology.md`、
  provenance連鎖は `docs/provenance.md` に従う。

## 2. NDL IIIF のURL形式（NDL公式）

manifest の実測（`@id`、`service.@id`、`resource.@id`）に基づく。

### 2.1 manifest

```text
https://dl.ndl.go.jp/api/iiif/<PID>/manifest.json
```

実例:

```text
https://dl.ndl.go.jp/api/iiif/861211/manifest.json
https://dl.ndl.go.jp/api/iiif/861212/manifest.json
```

manifest の `metadata` に含まれる対応（実測値）:

- PID 861211: Title `将棋図巧・将棋図巧詰手.将棋図巧`、Call Number `209-461`、
  Bibliographic ID `000000493927`、DOI `10.11501/861211`、Access Restrictions `PDM`
- PID 861212: Title `将棋図巧・将棋図巧詰手.将棋図巧詰手`、Call Number `209-461`、
  Bibliographic ID `000000493927`、DOI `10.11501/861212`、Access Restrictions `PDM`

利用条件は manifest の `license` が指す NDL公式ヘルプに従う。

### 2.2 画像（IIIF Image API）

```text
https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/full/<サイズ>/0/default.jpg
```

- `<PID>`: 上表のデジタル単位（例: `861211`）
- `<RID>`: 画像ID（例: `R0000001`）。§2.3 の規則に従う
- `full`: region=全体
- `<サイズ>`: size。`full` で原寸。軽量版が要る場合のみ `full` 以外（例: `1024,`）を使う
- `0`: 回転なし
- `default.jpg`: 品質・形式

実例（manifest の `resource.@id` と一致）:

```text
https://dl.ndl.go.jp/api/iiif/861211/R0000001/full/full/0/default.jpg
https://dl.ndl.go.jp/api/iiif/861212/R0000036/full/full/0/default.jpg
```

### 2.3 canvas番号とRIDの対応規則

manifest の `sequences[0].canvases[]` の実測により確認:

```text
canvas N  <->  RID = "R" + N を7桁ゼロ埋めしたもの
```

- `https://dl.ndl.go.jp/api/iiif/861211/canvas/1` <-> `R0000001`
- `https://dl.ndl.go.jp/api/iiif/861211/canvas/10` <-> `R0000010`
- `https://dl.ndl.go.jp/api/iiif/861211/canvas/58` <-> `R0000058`
- `https://dl.ndl.go.jp/api/iiif/861212/canvas/1` <-> `R0000001`
- `https://dl.ndl.go.jp/api/iiif/861212/canvas/36` <-> `R0000036`

総canvas数（manifest実測）:

- PID 861211: canvas 1–58（計58）
- PID 861212: canvas 1–36（計36）

注意: canvas番号は撮影順の通し番号であり、原資料の丁付け・問題番号と同一ではない。
問題番号との対応付けは原典画像との照合作業（`source.page`）で行い、本書では扱わない。

## 3. ダウンロード手順（標準ライブラリのみ）

方針: NDL公式IIIF Image APIのみを用いる。実装は標準ライブラリの
`urllib` のみ（サードパーティ禁止）。正本の実装は `tools/ndl_fetch.py`
であり、本節の手順はその動作説明である。保存先・命名は §3.2 に統一する。

### 3.1 取得の仕組み

1. **URLの組み立て**: §2.2 の形式に従い、
   `https://dl.ndl.go.jp/api/iiif/<PID>/<RID>/full/<SIZE>/0/default.jpg`
   を作る。`<RID>` はcanvas番号の7桁ゼロ埋め（§2.3。例: canvas 31 →
   `R0000031`）。`<SIZE>` は原寸確定読取のための `full`（作業仮読のみ
   `1024,` 等の軽量版を許す）。
2. **リクエスト**: `User-Agent: edo-tsume-repro/1.0` を付したGET。
   タイムアウト180秒。
3. **丁寧さの確保**: 取得ごとに3秒待機する。失敗時は5秒×試行回数の
   backoffで最大5回リトライする。120超の連続 `full` 取得でHTTP 403の
   レート制限が発生した実測がある（2026-09-23。待機で解消し、canvas固有の
   制限ではないことを確認）。制限に当たったら取得を止めて待機し、
   再開すること。
4. **取得済みの再利用**: 保存先に検証済みファイルがあれば飛ばす
   （再取得しない）。
5. **保存**: 一時作業領域のみ。リポジトリには画像をコミットしない。

### 3.2 コマンド（`tools/ndl_fetch.py`）

```bash
# 範囲取得（例: 玉図上巻 PID 861197 の canvas 1–58 を原寸で）
python3 tools/ndl_fetch.py --pid 861197 --start 1 --end 58 --work-dir <WORK_DIR>
# 単一RIDの軽量版（作業仮読用）
python3 tools/ndl_fetch.py --pid 861197 --rid R0000031 --work-dir <WORK_DIR> --size 1024,
# 部分切り抜きはIIIFのregion指定で直接取得する（転記手順書の pct: 記法を参照）
```

`--work-dir` は実行時に指定する作業用一時ディレクトリ
（公開文書のため絶対パスは記さない）。終了コード0は全件成功、
1は失敗あり（失敗した番号を表示する）。

### 3.3 保存先規約

```text
<WORK_DIR>/ndl_<PID>/<NNN>.jpg
```

- `<PID>`: `861211` / `861212` / `861197` / `861198` / `861193` / `861194`
- `<NNN>`: canvas番号を3桁ゼロ埋め（例: canvas 1 → `001.jpg`、canvas 58 → `058.jpg`）
- canvas番号とRIDの対応は §2.3 に従い、ファイル名から `R{n:07d}` を復元できること
- 切り抜き・解析用の中間ファイルは同ディレクトリに置く場合、連番と衝突しない名前
  （例: `crop_*`、`t*`、`no*_*.jpg`）にし、§4 の系統的取得物（`NNN.jpg`）と区別する
- リポジトリには画像をコミットしない（一時作業領域のみ）

### 3.4 検証方法（JPEGヘッダ・バイトサイズ。`tools/ndl_fetch.py` が自動実施）

```python
import os

path = os.path.join(WORK_DIR, "ndl_861211", "001.jpg")
data = open(path, "rb").read()
print(os.path.getsize(path))  # 0バイトでないこと
print(data[:2] == b"\xff\xd8")  # SOIマーカー
print(data[-2:] == b"\xff\xd9")  # EOIマーカー
```

判定基準:

1. `os.path.getsize() > 0`（空ファイル・HTMLエラーページの誤保存を検出）
2. 先頭2バイトが `FF D8`、末尾2バイトが `FF D9`（JPEGとして完結）
3. 取得範囲の連番に欠番がないこと（§4 の範囲と突き合わせる）
4. 疑わしい小サイズ（例: 数KBのエラーページ）は manifest の `width`/`height`
  （861211: 3751x3025、861212: 3698x2881）と大きく矛盾しないか目安にする

## 4. 現状の取得済み範囲（ファイル名一覧ベース、確認日 2026-09-16）

画像自体は開いていない。ディレクトリ一覧のファイル名のみで判定した。
バイトサイズ・JPEG正当性の検証は未実施のため、§3.3 の検証を通すまでは「仮取得」と扱う。

### 4.1 `ndl_861211`（PID 861211、総canvas 58）

- 系統的取得物: `001.jpg`–`058.jpg` がすべて存在（58/58、欠番なし）
- その他（系統外・作業ファイル、63件）:
  `c_fu_gote.jpg`、`c_fu_sente.jpg`、`c_gin_gote.jpg`、`c_gin_sente.jpg`、
  `c_kaku_gote.jpg`、`c_kaku_sente.jpg`、`c_kei_gote.jpg`、`c_kei_sente.jpg`、
  `c_ryu_gote.jpg`、`c_ryu_sente.jpg`、`c_to_gote.jpg`、`c_to_sente.jpg`、
  `crop_005_right.jpg`、`crop_006_no2.jpg`、`crop_006_r4f1.jpg`、
  `crop_006_r4to.jpg`、`crop_006_r79.jpg`、`fu_gote.jpg`、`fu_sente.jpg`、
  `gin_gote.jpg`、`gin_sente.jpg`、`kaku_gote.jpg`、`kaku_sente.jpg`、
  `kei_gote.jpg`、`kei_sente.jpg`、`kou_gote.jpg`、`kou_sente.jpg`、
  `n4_f1col_new.jpg`、`n4_f1low_big.jpg`、`n4_f1r1_big.jpg`、`n4_f1r1_new.jpg`、
  `n4_f1r9_big.jpg`、`n4_f1r9_new.jpg`、`n4_f2r9_big.jpg`、`n4_G_ref.jpg`、
  `n4_kou_ref.jpg`、`n4_L_ref.jpg`、`n4_Lsente.jpg`、`n4_r4f1f2.jpg`、
  `n4a.jpg`、`n4a2.jpg`、`n4a3.jpg`、`n4a4.jpg`、`n4a5.jpg`、`n4b.jpg`、
  `n4b2.jpg`、`n4b3.jpg`、`n4b5.jpg`、`n4b6.jpg`、`n4f1col.jpg`、
  `no1_diagram.jpg`、`no4_board.jpg`、`no4_f1r1.jpg`、`no4_f1r1b.jpg`、
  `no4_grid.jpg`、`no5_f8r1.jpg`、`no5_f8r1b.jpg`、`no5_full.jpg`、
  `no5_r1.jpg`、`no5_r1wide.jpg`、`pair_kou.jpg`、`ryu_gote.jpg`、`ryu_sente.jpg`
- 判定: ファイル名上は全canvas取得済み。残作業は §3.3 の全件検証のみ

### 4.2 `ndl_861212`（PID 861212、総canvas 36）

- 系統的取得物: `001.jpg`–`036.jpg` がすべて存在（36/36、欠番なし）
- その他（系統外・作業ファイル、7件）:
  `no5_sol.jpg`、`t001.jpg`、`t002.jpg`、`t003.jpg`、`t004.jpg`、`t005.jpg`、`t006.jpg`
- 判定: ファイル名上は全canvas取得済み。残作業は §3.3 の全件検証のみ

### 4.3 未取得範囲（結論）

- 将棋図巧 PID 861211: 系統的連番の欠番なし（001–058）。未取得のcanvasなし（検証待ち）
- 将棋図巧詰手 PID 861212: 系統的連番の欠番なし（001–036）。未取得のcanvasなし（検証待ち）
- 将棋無双（NDLBibID 000001281469、W431-4）: NDLインターネット公開の画像なし確定（2026-09-17、NDLサーチ実測。詳細は `docs/research.md` §1.2）。原典照合用の画像取得は未実施

## 5. 玉図・絹篩のmanifest台帳（2026-09-23実測）

`https://dl.ndl.go.jp/api/iiif/<PID>/manifest.json` の実測。画像取得ではなく
canvas数・寸法・利用条件の確認のみ。いずれも `viewingHint: individuals`、
licenseはNDL公式IIIFヘルプを指す。

| PID | 対応資料 | canvas数 | 寸法 | 既存記録との整合 |
|---|---|---:|---|---|
| 861197 | 玉図上巻相当 | 58 | 3251x2949 | `docs/gyokuzu-chotei.md` §1–§2（R1–R58）と一致 |
| 861198 | 玉図下巻相当 | 31 | 3167x3007 | `docs/gyokuzu-chotei.md` §3（R1–R31）と一致 |
| 861193 | 絹篩上巻相当 | 40 | 3343x2850 | `collection.json`（上・40コマ）と一致 |
| 861194 | 絹篩下巻相当 | 31 | 3299x2832 | `collection.json`（下・31コマ）と一致 |

系統的全取得（2026-09-23実施、一時作業領域のみ・リポジトリにコミットしない）:

- 4単位160コマすべて `full/full` で取得・§3.3検証通過（SOI/EOI・非0バイト・
  欠番なし、計約245MB）: 861197（58/58）・861198（31/31）・
  861193（40/40）・861194（31/31）
- 取得時の知見: 120超の連続 `full` 取得でHTTP 403のレート制限が発生。
  2分待機後は `1024,` で疎通確認、待機3秒＋最大5リトライで残り37コマを
  `full` で完遂。制限はcanvas固有ではなく回数起因（待機で解消）。
  大量取得時は待機3秒以上・失敗時5秒×試行回の backoff を用いること。
