# Open Tsume — 著作権切れ詰将棋のオープンデータセット

[English](README.md)

**Open Tsume** は、著作権の消滅した江戸時代の詰将棋を集めたオープンデータセットです。
各問題は一次資料まで出典を追跡でき、機械可読形式（SFEN / USI / KIF / JSON）で保存し、
ソフトウェアによる検証を行います。

- 🎯 特定のゲームやサービス専用ではありません。ゲーム、Webサービス、将棋ソフト、
  エンジンのテスト、LLM/AIベンチマーク、研究・教育、再配布・派生データセットに自由に利用できます。
- 📜 原作品：**Public Domain**（例：伊藤看寿『将棋図巧』1755年）。
- 🗃️ 本プロジェクトが作成した機械可読レコード：**CC0 1.0**（LICENSE-DATA参照）。
- 🛠️ 検証・変換コード：**MIT License**（LICENSE-CODE参照）。

## 状況

Phase 1の対象：伊藤看寿『将棋図巧』（100問）。
現在の状況（2026-09-16）：100問すべての転記とエンジン検査が完了。
うち97問は最終詰みを確定、3問（026・073・093）は無駄合い候補として
solver確認待ちで記録。NDL原典画像との照合が済むまでは全件
`needs_manual_review: true` とします。

## リポジトリ構成

```text
open-tsume/
├── README.md / README.ja.md
├── LICENSE-DATA (CC0-1.0) / LICENSE-CODE (MIT)
├── CONTRIBUTING.md
├── docs/            research.md, methodology.md, copyright.md,
│                    provenance.md, validation.md
├── collections/edo/zukou/
│   ├── collection.json
│   └── problems/001.json …       # 1問1JSON（正本データ）
├── schema/problem.schema.json    # 問題レコードのJSON Schema
├── tools/
│   ├── validate.py               # 検証器（標準ライブラリのみ。スキーマ/SFEN/解答/詰み）
│   └── kif2open.py               # KIF→Open Tsume JSON変換器
├── tests/run_tests.py            # unittest一式（データセット全体に検証器を実行）
├── web/                          # GitHub Pages棋譜ビューア（静的・依存なし）
└── .github/workflows/ci.yml      # schema＋SFEN＋解答＋provenanceの自動検査
```

## データモデル（1問あたり）

- `id`（例 `zukou-001`）、`collection_id`、`number`
- `sfen` — 正本局面（手番は常に `b`。先手持駒を大文字＋玉方駒箱を小文字で記録）
- `solution_usi` — 正本解答（USI指し手列 `7g7f`、`P*3d`、`...+`）
- `solution_moves` — 手数（奇数、先手が詰ます）
- `status` — `position_verified` / `solution_verified` / `unique_solution_verified`
- `verification` — 方法・ツール・日付・参照URL・`needs_manual_review`
- `source` — 原題・所蔵機関（NDL）・資料ID・ページ・URL・版
- `rights` — `{original_work: Public Domain, dataset_record: CC0-1.0}`
- `corrected_sfen` — 修正版がある場合のみ使用。原典（`sfen`）は上書きしない

詳細は `schema/problem.schema.json` と `docs/methodology.md` を参照。

## 利用方法

```bash
git clone https://github.com/tokoroten/open-tsume.git
python3 tools/validate.py collections/edo/zukou/problems/001.json
python3 tests/run_tests.py
```

棋譜の閲覧はGitHub Pages（静的ビューア＋KIF/JSONダウンロード）で行えます。

## 由来（provenance）

```text
江戸時代の原典
↓ デジタルアーカイブ（NDL等）
↓ 巻・ページ・問題番号
↓ 転記（誰が・何から・どう）
↓ 機械可読形式（SFEN/USI）
↓ ソフトウェア検証
↓ Open Tsume
```

詳細は `docs/provenance.md`。原典画像との照合が未了のレコードは
`verification.needs_manual_review: true` を持ち、ビューア上でも明示されます。

## 貢献

CONTRIBUTING.md参照。要点：

- 現代サイト・書籍からのスクレイピング・転載は禁止。出所不明データの混入禁止。
- Public Domainの一次資料から転記し、出所を記録する。
- `sfen`（原典）は上書きしない。修正は `corrected_sfen` に分離する。
- CI（スキーマ・SFEN・解答合法性・最終詰み・provenance）を必ず通す。
