# Progress（進捗管理）

更新日: 2026-09-22
公開文書のため、本書にローカルマシンの絶対パス・ユーザー名は記さない。

## 更新手順

1. 各 collection の JSON を走査し、下表の数値を更新する。
   - `?総数` = 全レコードの `sfen` 盤面部に含まれる `?` の合計
   - `持駒確定率` = `sfen` 持駒部が `-` 以外の件数 / 全件
   - `intended記録率` = `intended_solution_usi` / `intended_solution_moves` が
     非nullの件数 / 全件
   - `source.page記録率` = `source.page` 非空の件数 / 全件
2. `python tools/validate.py`（problems・collections・drafts）、
   `python tests/run_tests.py`、`python tools/build_web.py --check` を実行し、
   結果を「検証状態」に記録する。
3. 残作業の完了・新規判明事項を「残作業」に反映し、更新日を改める。

## 全体サマリー（2026-09-22 時点）

| collection | 種別 | 件数 | ?総数 | 持駒確定 | intended確定 | source.page |
|---|---|---:|---:|---:|---:|---:|
| zukou（将棋図巧） | 正本 problems | 100 | 0 | 100/100 | 100/100（手順書由来の分離記録あり） | 照合中 |
| musou（将棋無双） | 正本 problems | 100 | 0 | 100/100 | 同上 | 照合中 |
| gyokuzu（将棋玉図） | staging drafts | 100 | 1,231 | 100/100（036/092/095/096は持駒なし確定） | 0/100 | 100/100 |
| kinza（将棊絹篩） | staging drafts | 54 | 4,374（=81×54、全升未転記） | 0/54 | 0/54 | 54/54 |

## 検証状態（2026-09-22 時点）

- problems 全件検証: 200/200 passed（zukou 100 + musou 100）
- collections 検証: 4/4 passed（gyokuzu, kinza, musou, zukou）
- drafts 検証: 154/154 passed（gaps allowed）
- `tests/run_tests.py`: 15 tests OK
- `tools/build_web.py --check`: 差分なし
- solver試行（?-free 4件のみ）: `tools/mate_search.py`＋tsume-solver crosscheck。
  008はMATE 3手・043はMATE 1手（図面要再読）・076は駒箱次第のMATE 1手で
  2エンジン一致（いずれも候補・昇格なし）、072は7手以内不詰（REFUTED・要再読）。
  詳細 `docs/solver-trials-2026-09-22.json`。?残draftはsolver対象外。
- 解読募集ページ: `web/drafts.html`＋`web/collections/{gyokuzu,kinza}_drafts.json`を
  `tools/build_drafts_page.py` で生成（現転記図・?数・NDLリンク・solver候補・
  Issue報告リンク154件）。候補KIF 3件（008/043/076）は `web/candidates/` に
  未検証参考として掲載。
- 元画像のWeb掲載（2026-09-23、`docs/image-policy.md` 準拠）:
  引用RID158件を幅1024に縮小し `web/images/` に自前ホスト（計23MB、
  `tools/build_draft_images.py`＋`web/images/SOURCES.md`）。
  各カードに原画像＋出典表示＋NDL原寸リンクを付し、Issue報告リンクを
  「解読結果・誤り指摘」に拡張。全154件が画像つき。
- 正本200問の独立solver照合（2026-09-22夜、8並列・
  `docs/solver-dfpn-200-2026-09-22.jsonl`ほか）: tsume-solver df-pn
  （第1ラウンド `solve --engine dfpn --max-ply 63 --node-budget 5000000
  --threads 8`、6399 CPU秒）で43件に詰み存在を証明（PROVEN）。
  第2ラウンド（未評価136件・`--node-budget 20000000`、19035 CPU秒）で
  さらに34件PROVEN（計77件）、1件DISPROVEN。
  長手数21件のexact再試行（`solve-sfen --max-ply=記録手数 --node-budget
  20000000`、8並列）は全件UNKNOWN（予算切れ）。
  第3ラウンド（残101件・`--node-budget 100000000`、8並列・57659 CPU秒、
  `docs/solver-dfpn-round4-100M-2026-09-22.jsonl`）でさらに55件PROVEN
  （計132件）、1件DISPROVEN。
  DISPROVEN計5件の内訳: 3件はbound内否認（記録手順163〜611手がbound超の
  ため矛盾なし）、musou-088（記録31手）・musou-037（記録47手）の2件は
  bound内否認だが両記録とも `solution_verified=false` 格下げ済みで整合
  （不完全作の傍証として記録する価値あり）。
  残63件（45件は100MでもUNKNOWN・18件は長手数）はvalidatorの単一ライン
  保証のみ。UNKNOWNは無情報（zukou-050はbound 15でPROVEN・bound 63で
  UNKNOWNとflipすることを確認済み）。記録の書換えなし。
  validatorの単一ライン保証は不変。
- 分解証明の確立と横展開（2026-09-22〜23）:
  記録ライン上の各後手番で全応手を列挙しdf-pnで個別証明する深さ優先手法。
  全200問から応手14050局面を抽出→9手フィルタ（8847解決）→残り5203を
  21手/10Mで8分割実行→残り僅少な65問の191応手を63手/100Mで仕上げ
  （`docs/solver-decomp-finish-63-100M-2026-09-23.jsonl`、約33k CPU秒）。
  完全証明（全応手が詰み）に達したのは **93/200問**
  （内訳: 初期35＋musou-007＋仕上げ57）。残107問は応手の一部が深い
  boundでも未決着。記録の書換えなし。
- 深bound追加試行の打切り（2026-09-23、
  `docs/solver-decomp-127-probe-2026-09-23.jsonl`）: 残り僅少45問の
  320応手を127手/100Mで仕上げる計画で10応手を試験し8解決（27〜37手）。
  ただし1応手あたり平均265 CPU秒（63手/100M時の約20倍）を要し、
  全量では約180 CPU時間の見込みのため一括遂行を中止。
  深い分岐は選択的（1問完成が見える場合のみ）に対処する方針に切替え。
- musou-001残り2応手の200M深掘り（2026-09-23、
  `docs/solver-exact-musou001-200M-2026-09-23.jsonl`）: 初手への5b4b・
  3手目への3b3cをexact maxPly 63/nodeBudget 200000000で実行したが
  両方UNKNOWN（予算切れ）。記録11手の musou-001 は序盤分岐が高密度で、
  exact 2億ノードでも決着せず。記録の書換えなし。
- 深さ優先専用DFS（自前 `tools/mate_search.py`）のhead-to-head（2026-09-23）:
  未証明の短手数3件（musou-065=9・zukou-021=21・zukou-031=23）に
  max-plies 25/timeout 600s/max-nodes 100万・3並列で実行し全件timeout。
  実測速度は約60ノード/秒で、Rust（数百万ノード/秒）の約1万分の1。
  深さ優先という戦略自体はexact/df-pnに既載であり、壁は戦略ではなく
  証明木サイズに対する実装速度と予算と結論。Python DFSの全問投入は行わない。
- 完成間近5問の仕上げ試行（2026-09-23、
  `docs/solver-decomp-close9-63-100M-2026-09-23.jsonl`、7251 CPU秒）:
  残り3応手以内の musou-001/008・zukou-021/055/080 の計9応手を63手/100Mで
  実行したが全件UNKNOWN（予算切れ）。いずれも初手・3手目への応手（ply 0/2）
  で、序盤分岐の防御が深いことが判明。完成には別手法（超大予算・局面特化）
  が必要。記録の書換えなし。
- 全体証明の200Mラウンド前半（2026-09-23、
  `docs/solver-dfpn-r5a-200M-2026-09-23.jsonl`、約34k CPU秒）:
  未証明22件中5件PROVEN（zukou-003=45・musou-028=51・musou-053=47・
  musou-064=27・musou-072=41。全体計137件）。
  1件あたり約1500 CPU秒を要し、200M級の費用対効果は低下中。
- 全体証明の200Mラウンド後半（2026-09-23、
  `docs/solver-dfpn-r5b-200M-2026-09-23.jsonl`、約35k CPU秒）:
  残り23件中12件PROVEN（musou-002=47・040=39・045=49・046=29・052=63・
  067=49・068=39・080=35・zukou-032=31・049=49・062=29・070=27。
  **全体計149件**）。musou-052はbound 63ちょうどでの証明。
  残りはvalidator保証＋UNKNOWNのまま。

## 残作業

### gyokuzu（玉図、draft 100件）

- [ ] 盤面 `?` の削減（1,231残・?-free 4件: 008/043/072/076）。原寸再読・空升確定・持駒基準の先後確定・死駒規定適用で進める（Wave 28で001を?19→18、Wave 31で018を?9→7、Wave 33で073を?22→19、Wave 40で021を?17→11、Wave 41で022を?17→13、Wave 43で069を?18→17、Wave 44で083を?18→17、Wave 45で071を?13→12、Wave 46で084を?13→12、Wave 47で088を?12→11、Wave 49で081を?11→9、Wave 50で098を?20→19、Wave 51で017を?19→16に削減）
- [x] ?-free 4件の台帳同期・solver記録（2026-09-22。008/043/072/076に台帳同期note＋solver照合note＋`verification.method`定型追記。012に`gap:`行を補完。旧gap行の到達前数値は履歴として残す）
- [ ] ?-free 4件の原典照合（008は丁推定・駒箱未計上、043は1手詰のため図面要再読、072は不詰のため再読、076は駒箱確定が先決。いずれも昇格条件未達）
- [x] 持駒の確定（100/100。036/092/095/096は持駒なし確定）
- [ ] `intended_solution_usi` / `moves` の USI 化（0/100）
- [ ] `solution_usi` の確定（0/100）
- [ ] 下巻丁番号・対向頁の丁継ぎ確定
- 丁–R対応メモは `docs/gyokuzu-chotei.md`（Wave 26作成・作業メモ・非正本。上巻R1–29/R30–58・下巻R1–31）
- 詳細は `docs/gyokuzu-transcription.md`

### kinza（絹篩、draft 54件）

- [ ] 文字譜の全列翻刻（高解像は分岐頁のみに絞る）
- [ ] 盤面・持駒の確定（0/54）
- [ ] `intended_solution_usi` / `moves` の USI 化（0/54、初形頁の確定後に再試行）
- [ ] 附記号（○春・○夏・春・夏・附・同）の帰属記録（列単位JSON化を検討）
- 詳細は `docs/kinza-transcription.md`

### zukou / musou（正本）

- [ ] `source.page` の充填（NDL画像を直接読んだ番のみ。推定の転記禁止）
- [ ] 論争点の解決: No.12 初段、No.20 系統不一致（詳細は `docs/ndl-collation.md` §5）
- [ ] musou-037/073/088 は `solution_verified=false` に格下げ済み。別伝本照合待ち
- [ ] 無双の原典画像の入手方法の検討（NDLインターネット公開なし確定。館内利用・遠隔複写等の別手段が要検討）

## 運用メモ

- 画像はリポジトリにコミットしない。取得・命名は `docs/data-acquisition.md`、
  アクセス方法は `docs/ndl-access.md` に従う。
- `verification.needs_manual_review: true` は個別の原典照合が済むまで維持する。
- 推測補完の禁止: 不確定升は `?` に倒す。先後未確定升は種が読めても `?` とする。
- `git push` は権限上、作業者（リポジトリ所有者）が行う。
