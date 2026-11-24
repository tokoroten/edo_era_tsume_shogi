# 初手の機械監査レポート

`python tools/head_check.py --md --all` の出力（2026-11-25）。
判定: OK=移動元が盤上にあり経路も空 / OK(drop)=持駒から打つ / MOVER?=盤面の `?` 升に移動元がある可能性 / NO MOVER=移動元なし / NO CHECK=王手にならない / PRE-CHECK?=初期局面で既に王手（`?` が遮っている可能性）。

開き王手も検出する（移動元を盤から除いた後に、先手のどの駒かが玉を攻撃しているかを見る）。

| collection | # | head | status | detail |
|---|---|---|---|---|
| kanju | 1 | 二五飛 | OK(drop) |  |
| kanju | 2 | 一二金 | OK(drop) |  |
| kanju | 3 | 五一飛 | OK(drop) |  |
| kanju | 4 | 二二龍 | MOVER? | (2, 2) |
| kanju | 5 | 一九飛 | OK(drop) |  |
| kanju | 6 | 一六銀 | OK | move (6, 2)->(6, 1) |
| kanju | 7 | 二四飛 | OK(drop) |  |
| kanju | 8 | 四二金 | OK(drop) |  |
| kanju | 9 | 六八龍 | MOVER? | (8, 6) |
| kanju | 10 | 四二銀 | OK(drop) |  |
| kanju | 11 | 九五龍 | OK(drop) |  |
| kanju | 12 | 三一歩成 | OK | move (1, 4)->(1, 3) |
| kanju | 13 | 一八銀 | OK | move (8, 2)->(8, 1) |
| kanju | 14 | 三二桂 | OK | move (3, 5)->(2, 3) |
| kanju | 15 | 三八桂 | OK(drop) |  |
| kanju | 16 | 一一銀成 | OK | move (2, 2)->(1, 1) |
| kanju | 17 | 四八桂 | MOVER? | (8, 4) |
| kanju | 18 | 一三銀成 | MOVER? | (3, 1) |
| kanju | 19 | 八二龍 | MOVER? | (8, 2) |
| kanju | 20 | 三七角 | OK(drop) |  |
| kanju | 21 | 六四馬 | MOVER? | (6, 4) |
| kanju | 22 | 三三金 | MOVER? | (3, 3) |
| kanju | 23 | 一八角 | OK(drop) |  |
| kanju | 24 | 一三飛 | OK | move (1, 2)->(1, 3) |
| kanju | 25 | 二九角 | OK(drop) |  |
| kanju | 26 | 二五銀成 | OK | move (6, 3)->(5, 2) |
| kanju | 27 | 四六金 | OK(drop) |  |
| kanju | 28 | 二七角 | OK(drop) |  |
| kanju | 29 | 五四飛成 | OK | move (4, 2)->(4, 5) |
| kanju | 30 | 三六金 | OK | move (6, 4)->(6, 3) |
| kanju | 31 | 三五角成 | OK | move (6, 2)->(5, 3) |
| kanju | 32 | 六五角成 | OK | move (8, 3)->(5, 6) |
| kanju | 33 | 五五金 | OK | move (5, 4)->(5, 5) |
| kanju | 34 | 五一金 | OK(drop) |  |
| kanju | 35 | 五九歩 | OK(drop) |  |
| kanju | 36 | 四一飛 | OK(drop) |  |
| kanju | 37 | 四九飛 | OK(drop) |  |
| kanju | 38 | 五二桂成 | MOVER? | (2, 5) |
| kanju | 39 | 七六飛 | OK | move (6, 6)->(6, 7) |
| kanju | 40 | 五五金 | OK | move (6, 6)->(5, 5) |
| kanju | 41 | 五六歩 | OK(drop) |  |
| kanju | 42 | 七三飛 | OK | move (3, 6)->(3, 7) |
| kanju | 43 | 五六角 | OK | move (3, 8)->(6, 5) |
| kanju | 44 | 三三飛打 | OK(drop) |  |
| kanju | 45 | 七九銀 | OK | move (8, 8)->(7, 9) |
| kanju | 46 | 二八金打 | OK | move (2, 7)->(2, 8) |
| kanju | 47 | 九八金 | OK | move (7, 9)->(8, 9) |
| kanju | 48 | 四二銀成 | OK | move (1, 3)->(2, 4) |
| kanju | 49 | 五七金 | OK(drop) |  |
| kanju | 50 | 三五香 | MOVER? | (5, 3) |
| seimyo | 1 | 一九角成 | OK | move (8, 2)->(9, 1) |
| seimyo | 2 | 四七金 | OK | move (8, 4)->(7, 4) |
| seimyo | 3 | 三三銀 | OK(drop) |  |
| seimyo | 4 | 三七歩成 | OK | move (7, 4)->(7, 3) |
| seimyo | 5 | 三二銀 | OK(drop) |  |
| seimyo | 6 | 三九銀 | OK(drop) |  |
| seimyo | 7 | 二一と | OK | move (2, 3)->(1, 2) |
| seimyo | 8 | 一八角成 | MOVER? | (8, 1) |
| seimyo | 9 | 一八香 | MOVER? | (1, 8) |
| seimyo | 10 | 三二金 | OK | move (2, 2)->(3, 2) |
| seimyo | 11 | 五五龍 | MOVER? | (5, 5) |
| seimyo | 12 | 三八飛 | MOVER? | (8, 3) |
| seimyo | 13 | 二三歩 | OK | move (2, 4)->(2, 3) |
| seimyo | 14 | 二六金 | MOVER? | (6, 2) |
| seimyo | 15 | 三一金 | OK | move (2, 3)->(1, 3) |
| seimyo | 16 | 五六金 | OK | move (5, 6)->(6, 5) |
| seimyo | 17 | 三二歩 | OK(drop) |  |
| seimyo | 18 | 五九龍 | MOVER? | (9, 5) |
| seimyo | 19 | 九二龍 | MOVER? | (9, 2) |
| seimyo | 20 | 四六銀 | OK | move (5, 5)->(6, 4) |
| seimyo | 21 | 八二銀 | OK(drop) |  |
| seimyo | 22 | 三六飛 | OK | move (2, 6)->(3, 6) |
| seimyo | 23 | 三八歩 | OK(drop) |  |
| seimyo | 24 | 二一歩 | OK(drop) |  |
| seimyo | 25 | 二七金 | OK(drop) |  |
| seimyo | 26 | 三二桂 | OK | move (3, 5)->(2, 3) |
| seimyo | 27 | 五六龍 | MOVER? | (6, 5) |
| seimyo | 28 | 三七と | OK | move (6, 4)->(7, 3) |
| seimyo | 29 | 三五龍 | MOVER? | (3, 5) |
| seimyo | 30 | 三八龍 | MOVER? | (8, 3) |
| seimyo | 31 | 二一龍 | OK | move (3, 1)->(2, 1) |
| seimyo | 32 | 二九歩 | OK(drop) |  |
| seimyo | 33 | 四一銀 | OK(drop) |  |
| seimyo | 34 | 四六金 | OK | move (5, 4)->(6, 4) |
| seimyo | 35 | 四九龍 | MOVER? | (4, 9) |
| seimyo | 36 | 三三銀成 | OK | move (2, 2)->(3, 3) |
| seimyo | 37 | 三七龍 | MOVER? | (7, 3) |
| seimyo | 38 | 五六金 | NO MOVER | (6, 5) |
| seimyo | 39 | 四二香 | MOVER? | (2, 4) |
| seimyo | 40 | 六六金 | OK | move (7, 6)->(6, 6) |
| seimyo | 41 | 四五龍 | MOVER? | (5, 4) |
| seimyo | 42 | 二八銀 | PRE-CHECK? |  |
| seimyo | 43 | 一八香 | MOVER? | (1, 8) |
| seimyo | 44 | 八二銀 | MOVER? | (8, 2) |
| seimyo | 45 | 二六角 | OK | move (9, 5)->(6, 2) |
| seimyo | 46 | 一四飛 | OK | move (4, 5)->(4, 1) |
| seimyo | 47 | 三二飛 | OK | move (2, 7)->(2, 3) |
| seimyo | 48 | 三四龍 | MOVER? | (4, 3) |
| seimyo | 49 | 二八銀 | OK | move (7, 1)->(8, 2) |
| seimyo | 50 | 三九銀 | OK(drop) |  |
| seimyo | 51 | 二三飛 | MOVER? | (2, 3) |
| seimyo | 52 | 六六銀 | OK | move (5, 5)->(6, 6) |
| seimyo | 53 | 二一歩成 | OK(drop) |  |
| seimyo | 54 | 三三銀 | OK | move (4, 2)->(3, 3) |
| seimyo | 55 | 三九飛 | MOVER? | (9, 3) |
| seimyo | 56 | 三三龍 | NO MOVER | (3, 3) |
| seimyo | 57 | 三九桂 | OK(drop) |  |
| seimyo | 58 | 一二馬 | MOVER? | (2, 1) |
| seimyo | 59 | 三五飛成 | OK | move (5, 5)->(5, 3) (discovered) |
| seimyo | 60 | 二一歩 | OK(drop) |  |
| seimyo | 61 | 三七歩成 | OK | move (6, 3)->(7, 3) |
| seimyo | 62 | 四三角成 | OK | move (4, 3)->(3, 4) |
| seimyo | 63 | 二九歩 | OK(drop) |  |
| seimyo | 64 | 一一桂成 | OK | move (2, 3)->(1, 1) |
| seimyo | 65 | 六五馬 | MOVER? | (5, 6) |
| seimyo | 66 | 二六角成 | MOVER? | (6, 2) |
| seimyo | 67 | 五三金 | OK | move (2, 6)->(3, 5) |
| seimyo | 68 | 三四角 | MOVER? | (4, 3) |
| seimyo | 69 | 三七飛成 | OK | move (7, 1)->(7, 3) |
| seimyo | 70 | 一三龍 | MOVER? | (3, 1) |
| seimyo | 71 | 二一歩 | OK(drop) |  |
| seimyo | 72 | 二七と | OK | move (6, 3)->(7, 2) |
| seimyo | 73 | 六二馬 | MOVER? | (2, 6) |
| seimyo | 74 | 二八角成 | OK | move (7, 3)->(8, 2) |
| seimyo | 75 | 七四龍 | MOVER? | (4, 7) |
| seimyo | 76 | 一七金 | OK(drop) |  |
| seimyo | 77 | 一一歩成 | OK | move (1, 2)->(1, 1) |
| seimyo | 78 | 二八金 | OK | move (7, 2)->(8, 2) |
| seimyo | 79 | 二一歩 | OK(drop) |  |
| seimyo | 80 | 一七角成 | OK | move (9, 3)->(7, 1) (discovered) |
| seimyo | 81 | 四四龍 | MOVER? | (4, 4) |
| seimyo | 82 | 二五馬 | MOVER? | (5, 2) |
| seimyo | 83 | 三四角成 | OK | move (3, 2)->(4, 3) |
| seimyo | 84 | 四六飛 | MOVER? | (6, 4) |
| seimyo | 85 | 二六飛成 | MOVER? | (2, 6) |
| seimyo | 86 | 二九飛 | OK | move (2, 2)->(9, 2) |
| seimyo | 87 | 四六飛成 | OK | move (6, 3)->(6, 4) |
| seimyo | 88 | 三九歩 | OK(drop) |  |
| seimyo | 89 | 二一銀 | OK | move (2, 1)->(1, 2) |
| seimyo | 90 | 二九馬 | MOVER? | (9, 2) |
| seimyo | 91 | 三五銀成 | OK | move (6, 4)->(5, 3) |
| seimyo | 92 | 六一飛 | MOVER? | (1, 6) |
| seimyo | 93 | 三二飛 | MOVER? | (2, 3) |
| seimyo | 94 | 六七金 | OK(drop) |  |
| seimyo | 95 | 一四香 | OK(drop) |  |
| seimyo | 96 | 一六龍 | MOVER? | (6, 1) |
| seimyo | 97 | 三五角成 | OK(drop) |  |
| seimyo | 98 | 三二金 | MOVER? | (2, 3) |
| seimyo | 99 | 七五馬 | MOVER? | (7, 5) |
| seimyo | 100 | 三一飛成 | MOVER? | (3, 1) |
