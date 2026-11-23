# Solver status — draft collections（精妙・貫珠ほか）

対象: `collections/*/*/drafts/*.json`（盤面が転記途中の collection）。
正本200問の検証状況は `docs/solver-coverage.md` を参照。

## 2026-11-17 時点の結論

- 精妙100・貫珠50・絹篩54 は盤面に `?`（未読升）が残り、`tsume-solver.exe` に
  渡せる完全な SFEN になっていない（検証可能 0 件）。
- 完全 SFEN は 貫珠 `001` と 玉図 `008/043/072/076` の 5 件のみ。うち 4 件は
  既に solver 実行済みで、下表のとおり結果が記録されている。

| draft | SFEN | 結果 | 備考 |
|---|---|---|---|
| kanju-001 | `4k4/9/9/9/9/9/9/9/9 b RBGSN 1` | REFUTED（3手上限・exhaustive・nodes 11010） | 盤面不完全（`?` の升に駒あり） |
| gyokuzu-008 | `9/9/4PPPPB/7B1/6gS1/7+P1/4+P11L1/6Pkg/5+R11N b G2S 1` | MATE 3（exhaustive・nodes 5930） | 2 エンジン一致。丁帰属推定のため候補止まり |
| gyokuzu-043 | `9/9/2g6/4N1S2/1B2S11B1/R53/3Sk4/4P4/1N111G1N1 b P 1` | MATE 1（exhaustive・nodes 7967） | **1手詰・複数解は不自然 → 転記誤りの疑い。要再読** |
| gyokuzu-072 | `4R4/9/5B3/9/+R3Pg+P2/2PSS4/GSL1P2B1/3g1+P3/k3N4 b S3N 1` | MATE 11（exhaustive・nodes 1397144） | 初手 9g8f / 9g9h の両方が詰み＝**複数解**。7手上限の REFUTED は浅すぎた |
| gyokuzu-076 | `1B1S2R2/3PgLP+P1/8P/2Pk+PP3/1S4+Pg1/1P1L1S2N/5N3/8L/9 b B2GS 1` | **非合法局面**（先手番で後手玉が王手） | と金 5d が玉 6d を利く。solver の MATE 1 は無効。要再読 |

- 玉図 043 の 1 手詰（4i5i / 9f9h）と 076 の非合法局面は、玉位置または持駒の
  転記誤りを示唆する。solver 結果を `solution_usi` に昇格させず、原寸再読の対象
  として `notes` に記録した。
- **SFEN を solver に渡す前に「手番側でない玉が王手されていないか」を検査する**
  こと。非合法局面では solve-sfen が無意味な MATE を返す（076 の実例）。

## 貫珠001 の probe 記録

```
$ tsume-solver.exe solve-sfen "4k4/9/9/9/9/9/9/9/9 b RBGSN 1" --max-ply 3 --node-budget 20000
outcome: REFUTED (exhaustiveWithinBound: true, nodes 11010)
```

- 玉1枚（5一）＋攻方持駒 RBGSN では3手以内の詰みが無い。したがって
  **draft 001 の盤面は不完全**（図には `?` の升に駒がある）。

## 玉図072 の再照合記録（2026-11-17）

```
$ tsume-solver.exe solve-sfen "4R4/9/5B3/9/+R3Pg+P2/2PSS4/GSL1P2B1/3g1+P3/k3N4 b S3N 1" \
    --max-ply 11 --node-budget 5000000
outcome: MATE distance 11 (exhaustiveWithinBound: true, nodes 1397144)
初手: 9g8f → MATE 11 / 9g9h → MATE 11 / S*8h → REFUTED (9i8h)
```

- 玉方持駒は未計上分を標準駒数から自動補完（`g3l13p`）。詰将棋の慣例どおり。
- 7 手上限で REFUTED だったのは単に探索が浅かったため。以後の probe は
  最短手数を 11〜13 手まで見る（`--max-ply 11` 以上）。

## 検証を解禁する条件

1. 当該 draft の盤面 `?` が 0 になる（原寸照合・先後確定）。
2. `tools/validate.py --draft` が盤面依存チェックを実行できる状態になる
   （`gap: board-dependent checks skipped` が出ない）。
3. `validate.py --draft` が `illegal position` gap を出さないこと
   （2026-11-17 追加。手番側でない玉が王手されている SFEN を検出する。
   076 がこれに該当し、solver に渡すと無意味な MATE が返る）。
4. そのうえで `probe --max-ply N`（N≥11）を実行し、詰み／不詰を記録してから
   `intended_solution_usi` / `solution_usi` を確定する。初手が複数出た場合は
   一意解検証に失敗したものとして扱い、図面の再読に戻す。

## 参考: 詰手（手順）との関係

- 下巻・詰手の翻刻は `docs/procedures.md` と `web/procedures.html` で進行中。
  精妙下巻は全25コマの題簽対応が確定済み（§1.1）。盤面が不完全な現状では、
  詰手の合法性検査（各手がその局面で合法か）も部分的なものになる。

## 2026-11-25 精妙（上巻）完全SFEN 14件の一括検証

道具: `tools/mate_search.py`（純Python df-pn、詰め手番は毎手王手）。予算 `--max-plies 13 --timeout 40 --max-nodes 800000`。
盤面に ? が無い精妙 draft 14件を対象。**結果は各 draft の solution_usi には書き戻していない**（方針どおり記録のみ）。

| draft | 結果 | 手数/PV | 計測 |
|---|---|---|---|
| seimyo-004 | MATE（証明） | 7手 6d7b+ 8b9c N*8e 9c8d B*7c 8d8e P*8f | depth7 / nodes 3813 / 41.8s |
| seimyo-017 | MATE（証明） | 3手 3g3b+ 2b1a P*1b | nodes 96 |
| seimyo-032 | MATE（証明） | 5手 P*9b 9a8b 6a8c+ | nodes 28 |
| seimyo-049 | MATE（証明） | 5手 7a8b 8a8b 4d7a+ 8b9b P*9c | nodes 56 |
| seimyo-067 | MATE（証明） | 3手 2f3e 4e3e G*3f | nodes 57 / **記録した初手 五三金（2六→3五＝2f3e）と一致** |
| seimyo-047 | unknown | 13手まで不成立の証明も詰みも得られず | depth13 / nodes 1534 / 29.6s |
| seimyo-022 | timeout | 打切り（depth7, 48s） | 予算内で未決 |
| seimyo-038 | timeout | 打切り（depth7, 55s） | 予算内で未決 |
| seimyo-056 | timeout | 打切り（depth11, 86s） | 予算内で未決 |
| seimyo-057 | timeout | 打切り（depth9, 76s） | 予算内で未決 |
| seimyo-074 | timeout | 打切り（depth11, 69s） | 予算内で未決 |
| seimyo-078 | timeout | 打切り（depth11, 63s） | 予算内で未決 |
| seimyo-080 | timeout | 打切り（depth7, 52s） | 予算内で未決 |
| seimyo-083 | timeout | 打切り（depth9, 84s） | 予算内で未決 |

所見:
- 完備盤面の少なくとも5件は実際に詰むことが**独立に証明**された（初手含め盤面転記の妥当性を支持）。
- 特に 067 は列頭の初手 五三金 と solver の最善初手が一致した。
- timeout 8件は「予算不足」であり反証ではない。--max-plies 拡大・ノード増で再走行の余地。
- 047 は depth13 完走で unknown（この深さでは詰み無しの証明も詰みも付かず）。
