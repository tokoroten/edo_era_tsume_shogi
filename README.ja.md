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

- 『将棋図巧』（伊藤看寿、1755年）：100問すべて転記・検証器検査済み
  （`tools/validate.py`）。各問は検証解（`solution_usi`）を持ち、
  `status.solution_verified` は単一ライン保証のみを意味する
  （記録した一手順の合法・連続王手・最終詰み。分岐全体の完全解ではない。
  詳細は `docs/validation.md`）。無駄合い注記（026・073・093）は各問の
  `notes` に保持し、残り応手がすべて即取り返しで詰むものは検証済みとして記録。
  `status.unique_solution_verified` は `false` のまま（v1では余詰探索なし）。
- 『将棋無双』（三代伊藤宗看、1734年）：100問すべて転記・検証器検査済み。
  単一ライン保証は図巧と同様。無駄合い注記（028・031・037・043）は保持。
  031・037番は文献指摘の不完全作と重なる（版・伝本の特定は今後の課題）。
- 『将棋玉図』（桑原君仲、1836年）：`drafts/` に100件
  （`collections/edo/gyokuzu/drafts/001.json`〜`100.json`）があり目標100件
  （`collection.json` `problem_count: 100`）に到達。丁付けの枠は確定
  （上巻50丁・下巻28丁、図面100図＋手順100題→100問題。`docs/research.md`
  §1.5）。個別の `source.page` への丁・面充填は未了（全件 `丁未確定` を維持。
  `docs/gyokuzu-transcription.md` §4・§7.5残件3）。`?` 残存
  （`?` ゼロなし。例：099は `?=29`、100は `?=33`）。先後判定の全件一巡は
  2026-09-17に完了（全100件の `notes` に記録。`docs/gyokuzu-transcription.md`
  §7.4〜§7.5のSFEN不変原則・高確信度のみ更新。例：098は `?=21→20`、
  099は `?=29` 維持、100は `?=33` 維持）。原典翻刻のUSI化率0%
  （`intended_solution_usi: null` が100/100件）、正規手順の確定率0%
  （`solution_usi: []` が100/100件）。本番昇格は0件（`problems/` 不存在、
  `problems_transcribed: []`）。draftは staging であり昇格件数に含めない。
  100件すべて `needs_manual_review: true` を維持。詳細は
  `docs/gyokuzu-transcription.md` §6〜§7、`docs/research.md` §1.5。
- 『将棋絹篩』（福島順棊。NDL書誌は出版年欠載のため `published_year: 1800`
  は暫定）：`drafts/` に54件
  （`collections/edo/kinza/drafts/001.json`〜`054.json`）があり目標54件
  （`collection.json` `problem_count: 54`：上巻1番〜28番28題＋本文29番〜
  50番22題＋附録一番〜四番4題）に到達。個別の丁充填は未了（全件 `丁未確定` を維持。
  `docs/kinza-transcription.md` §3〜§4）。盤面SFENはいずれも81升全 `?`＋
  持駒 `-` の構文用プレースホルダ（図面なし・文字譜未解読）。原典翻刻の
  USI化率0%（`intended_solution_usi: null` が54/54件）、正規手順の確定率
  0%（`solution_usi: []` が54/54件）。本番昇格は0件（`problems/` 不存在、
  `problems_transcribed: []`）。54件すべて `needs_manual_review: true`
  を維持。詳細は `docs/kinza-transcription.md` §7。
- 二本立て：`solution_*`＝検証解（その一手順に詰み保証）、
  `intended_*`＝想定解法・原典翻刻（合法再現のみ、`null` は翻刻途中を示す
  正規の状態。例：zukou-020 は `intended_solution_source` にNDL PID・
  canvas・列を残しUSIは `null`＋系統不一致の警告を保持）。
  ビューアでは想定解法／検証解を別欄表示する。
- solver crosscheck：実施分は `verification.method` に
  `docs/validation.md` の定型順序（engine・日付・条件・結果・取扱い）で記録。
  `sfen` を直接書き換えない（訂正は `corrected_sfen`＋`correction_note`）。
  例：zukou-050は記録9手の本手順が単一ライン保証を満たす一方、完全解は
  21手（単一検証ラインと分岐完備の完全解の差）。
- 版二層管理（図巧）：`collections/edo/zukou/collection.json` の
  `edition_note` に記録。層A＝文政4年（1821）跋・北林堂、層B＝明治・
  吉川半七文王囲再版系。確定版特定までは全件 `needs_manual_review` を維持。
- 本番昇格済み全200件（図巧＋無双）が `needs_manual_review: true`
  （国営アーカイブ画像との照合待ち）であり、draft全154件
  （玉図100＋絹篩54）も同様に `needs_manual_review: true` を維持。
  現レコードは第一段階の参考転記（盤面の事実＋本手順のみ、解説なし）です。
  `docs/provenance.md`、`docs/data-policy.md`、
  `docs/data-acquisition.md` 参照。

## リポジトリ構成

```text
edo_era_tsume_shogi/
├── README.md / README.ja.md
├── LICENSE-DATA (CC0-1.0) / LICENSE-CODE (MIT)
├── CONTRIBUTING.md
├── docs/            research.md, methodology.md, copyright.md,
│                    provenance.md, validation.md,
│                    data-policy.md, data-acquisition.md
├── collections/edo/
│   ├── zukou/collection.json ＋ problems/001.json …（100問）
│   ├── musou/collection.json ＋ problems/001.json …（100問）
│   ├── gyokuzu/collection.json ＋ drafts/001.json …（100件・staging。problemsなし）
│   └── kinza/collection.json ＋ drafts/001.json …（54件・staging。problemsなし）
├── schema/problem.schema.json    # 問題レコードのJSON Schema（intended_*含む）
├── tools/
│   ├── validate.py               # 検証器（標準ライブラリのみ。スキーマ/SFEN/解答/詰み＋想定解の合法性）
│   └── build_web.py              # 正本USI/SFENからPages配布用KIF/JSON/一覧を生成
├── tests/run_tests.py            # unittest一式（データセット全体に検証器を実行）
├── web/                          # GitHub Pages棋譜ビューア（静的・依存なし）
└── .github/workflows/ci.yml      # schema＋SFEN＋解答＋provenanceの自動検査
```

## データモデル（1問あたり）

- `id`（例 `zukou-001`）、`collection_id`、`number`
- `sfen` — 正本局面（手番は常に `b`。先手持駒を大文字＋玉方駒箱を小文字で記録）
- `solution_usi`／`solution_moves` — 検証解：ソルバー確認済みの詰み手順。
  検証器がたどって詰み判定する正本側
- `intended_solution_usi`／`intended_solution_moves`／
  `intended_solution_source` — 想定解法・原典翻刻：一次資料の解答文を
  読んでUSI化したもの。翻刻途中は `null`（USIなし＋出典進捗メモは正規の
  中間状態）。合法再現のみを保証し、詰みは主張しない
- `status` — `{position_verified, solution_verified,
  unique_solution_verified, intended_solution_verified}`。
  `solution_verified: true` は単一ライン保証のみ（その一手順の合法・
  連続王手・最終詰みで応手ゼロ。分岐外れ・最長抵抗・余詰なしは含まない。
  詳細は `docs/validation.md`）。`unique_solution_verified` はv1では
  `false` のまま。`intended_solution_verified` は想定解の合法再現のみを示す
- `verification` — 方法・ツール・日付・参照URL・`needs_manual_review`。
  solver照合分は `method` に `docs/validation.md` の定型で記録
- `source` — 原題・所蔵機関（NDL）・資料ID・ページ・URL・版。
  `edition` に版二層管理（図巧1821跋 vs 明治再版、無双の伝本差）を記録
- `rights` — `{original_work: Public Domain, dataset_record: CC0-1.0}`
- `corrected_sfen`（＋`correction_note`）— 修正版がある場合のみ使用。
  原典（`sfen`）は上書きしない

詳細は `schema/problem.schema.json`、`docs/methodology.md`、
`docs/validation.md` を参照。

## 利用方法

```bash
git clone https://github.com/tokoroten/edo_era_tsume_shogi.git
python3 tools/validate.py collections/edo/zukou/problems/001.json
python3 tests/run_tests.py
```

棋譜の閲覧は[GitHub Pages](https://tokoroten.github.io/edo_era_tsume_shogi/)（静的ビューア＋KIF/JSONダウンロード）で行えます。

## 由来（provenance）

```text
江戸時代の原典
↓ 国営アーカイブ（NDL等）
↓ 巻・ページ・問題番号
↓ 転記（誰が・何から・どう）
↓ 機械可読形式（SFEN/USI。二本立て：想定解法／検証解）
↓ ソフトウェア検証（実施分はsolver照合を含む）
↓ Open Tsume
```

詳細は `docs/provenance.md`。データ取得は国営アーカイブのみの方針
（`docs/data-policy.md`）に従い、NDL IIIF再現手順は
`docs/data-acquisition.md` 参照。原典画像との照合が未了のレコードは
`verification.needs_manual_review: true` を持ち、ビューア上でも明示されます。

## 貢献

CONTRIBUTING.md参照。要点：

- 国営アーカイブ（NDL等）のみ。現代サイト・書籍からのスクレイピング・
  転載は禁止。出所不明データの混入禁止。詳細は `docs/data-policy.md`。
- 国営アーカイブ（NDL等）の一次資料スキャンを直接読んで転記し、出所を記録する。
  第三者KIFは用いない。
- 二本立てを混同しない：`intended_*`（翻刻・合法のみ）／`solution_*`
  （検証詰み手順）。`sfen`（原典）は上書きしない。修正は `corrected_sfen`
  ＋`correction_note` に分離する。
- solver結果は `verification.method`（定型）＋`notes` に記録する。
  それ単独で `sfen` を書き換えない。
- CI（スキーマ・SFEN・解答合法性・最終詰み・provenance）を必ず通す。
