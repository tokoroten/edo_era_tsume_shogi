# Progress（進捗管理）

更新日: 2026-09-18
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

## 全体サマリー（2026-09-18 時点）

| collection | 種別 | 件数 | ?総数 | 持駒確定 | intended確定 | source.page |
|---|---|---:|---:|---:|---:|---:|
| zukou（将棋図巧） | 正本 problems | 100 | 0 | 100/100 | 100/100（手順書由来の分離記録あり） | 照合中 |
| musou（将棋無双） | 正本 problems | 100 | 0 | 100/100 | 同上 | 照合中 |
| gyokuzu（将棋玉図） | staging drafts | 100 | 1,266 | 100/100（036/092/095/096は持駒なし確定） | 0/100 | 100/100 |
| kinza（将棊絹篩） | staging drafts | 54 | 4,374（=81×54、全升未転記） | 0/54 | 0/54 | 54/54 |

## 検証状態（2026-09-18 時点）

- problems 全件検証: 200/200 passed（zukou 100 + musou 100）
- collections 検証: 4/4 passed（gyokuzu, kinza, musou, zukou）
- drafts 検証: 154/154 passed（gaps allowed）
- `tests/run_tests.py`: 15 tests OK
- `tools/build_web.py --check`: 差分なし

## 残作業

### gyokuzu（玉図、draft 100件）

- [ ] 盤面 `?` の削減（1,266残・?-free 3件: 008/043/072）。原寸再読・空升確定・持駒基準の先後確定・死駒規定適用で進める（Wave 28で001を?19→18、Wave 31で018を?9→7、Wave 33で073を?22→19、Wave 40で021を?17→11、Wave 41で022を?17→13、Wave 43で069を?18→17に削減）
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
