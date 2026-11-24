# 未決の列頭（初手）一覧

`head_unassigned: true` の題を、**なぜ未決なのか**とともに列挙する。
判定は盤面上で「合法に指せて王手になるか」を見たもの（`?` は空き升）。

## seimyo（33題）

| 題 | 盤面`?` | 印字 | 未決の理由 |
|---|---|---|---|
| 8 | 1 | 一八角成 | MOVER? (mover may be on a ?) |
| 11 | 3 | 五五龍 | MOVER? (mover may be on a ?) |
| 12 | 1 | 三八飛 | MOVER? (mover may be on a ?) |
| 14 | 0 | 二六金 | OWN PIECE |
| 18 | 4 | 五九龍 | MOVER? (mover may be on a ?) |
| 19 | 1 | 九二龍 | MOVER? (mover may be on a ?) |
| 27 | 3 | 五六龍 | MOVER? (mover may be on a ?) |
| 29 | 14 | 三五龍 | MOVER? (mover may be on a ?) |
| 30 | 1 | 三八龍 | OWN PIECE |
| 35 | 0 | 四九龍 | NO MOVER |
| 37 | 1 | 三七龍 | MOVER? (mover may be on a ?) |
| 38 | 0 | 五六金 | NO MOVER |
| 41 | 2 | 四五龍 | MOVER? (mover may be on a ?) |
| 44 | 1 | 八二銀 | MOVER? (mover may be on a ?) |
| 53 | 4 | 二一歩成 | OWN PIECE |
| 55 | 1 | 三九飛 | MOVER? (mover may be on a ?) |
| 56 | 0 | 三三龍 | NO MOVER |
| 58 | 5 | 一二馬 | MOVER? (mover may be on a ?) |
| 65 | 3 | 六五馬 | MOVER? (mover may be on a ?) |
| 66 | 3 | 二六角成 | MOVER? (mover may be on a ?) |
| 68 | 2 | 三四角 | MOVER? (mover may be on a ?) |
| 70 | 4 | 一三龍 | PRE-CHECK |
| 75 | 3 | 七四龍 | MOVER? (mover may be on a ?) |
| 81 | 4 | 四四龍 | MOVER? (mover may be on a ?) |
| 82 | 2 | 二五馬 | MOVER? (mover may be on a ?) |
| 84 | 0 | 四六飛 | OWN PIECE |
| 85 | 1 | 二六飛成 | MOVER? (mover may be on a ?) |
| 90 | 1 | 二九馬 | MOVER? (mover may be on a ?) |
| 92 | 2 | 六一飛 | MOVER? (mover may be on a ?) |
| 93 | 0 | 三二飛 | NO MOVER |
| 97 | 0 | 三五角成 | OWN PIECE |
| 99 | 4 | 七五馬 | MOVER? (mover may be on a ?) |
| 100 | 4 | 三一飛成 | MOVER? (mover may be on a ?) |

## kanju（9題）

| 題 | 盤面`?` | 印字 | 未決の理由 |
|---|---|---|---|
| 3 | 6 | 五一飛 | NO CHECK |
| 4 | 3 | 二二龍 | MOVER? (mover may be on a ?) |
| 9 | 0 | 六八龍 | NO MOVER |
| 18 | 1 | 一三銀成 | MOVER? (mover may be on a ?) |
| 19 | 1 | 八二龍 | MOVER? (mover may be on a ?) |
| 21 | 1 | 六四馬 | MOVER? (mover may be on a ?) |
| 22 | 3 | 三三金 | MOVER? (mover may be on a ?) |
| 38 | 3 | 五二桂成 | MOVER? (mover may be on a ?) |
| 50 | 1 | 三五香 | MOVER? (mover may be on a ?) |

## 理由の意味

- `MOVER?`: 印字された駒が盤上のどこからも着地点へ届かない（持駒にも無い）。
  盤面に `?` が残るので、移動元がそこに隠れている可能性がある。
- `NO MOVER`: 同じだが `?` が無い＝盤面が完成しているのに着手できない。列の帰属が誤り。
- `OWN PIECE`: 着地点が先手の駒で埋まっている。
- `NO CHECK`: 指せても王手にならない。

