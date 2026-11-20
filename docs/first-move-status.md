# 詰手の初手 検証状況（2026-11-18）

「検証済み」は、原寸の切出で読んだ初手が本編/上巻の盤面で王手になることを
機械検証（`TestKanjuFirstMoves` / `TestSeimyoFirstMoves`）したもの。
**信頼度**は盤面の `?` 数による: `good`(≤12) / `partial`(13-19) / `sparse`(≥20)。
`sparse` は空升が多く、王手の成立が列帰属を保証しない（`docs/procedures.md` §3.8）。
盤面が不完全で王手検証ができない題の読みは `docs/kanju-procedure-readings.json` に
`attacks_gote_king` 付きで記録する（`TestKanjuProcedureReadings` が検査）。
未検証の題は、まず「後手玉」の筋段を盤面図で確認してから列頭を読む。

## 将棋貫珠 詰手（50題）

| 番 | 後手玉 | 初手 | 信頼度 |
|---|---|---|---|
| 1 | 5a | 二五飛 | board-good（?=0） |
| 2 | 2b | 一二金 | board-sparse（?=24） |
| 3 | 8a | 五一飛 | board-sparse（?=23） |
| 4 | 1b | 二二龍 | board-partial（?=18） |
| 5 | 9b | 一九飛 | board-sparse（?=20） |
| 6 | 5b | 一六銀 | board-good（?=12） |
| 7 | 6a | 一四飛 | board-partial（?=14） |
| 8 | 2c | 四二金 | board-partial（?=16） |
| 9 | 8c | 八六龍 | board-sparse（?=21） |
| 10 | 1c | 二四銀 | board-sparse（?=20） |
| 11 | 9c | 九五龍 | board-partial（?=18） |
| 12 | 1b | 三一歩成 | board-good（?=8） |
| 13 | 9b | 一八銀 | board-good（?=6） |
| 14 | 1a | 三二桂 | board-partial（?=16） |
| 15 | 9a | 三八桂 | board-good（?=7） |
| 16 | 1b | 一一銀成 | board-sparse（?=20） |
| 17 | 9b | 四八桂 | board-partial（?=16） |
| 18 | 2a | 一三銀成 | board-sparse（?=23） |
| 19 | 8a | 八二龍 | board-sparse（?=22） |
| 20 | 5e | 三七角 | board-good（?=11） |
| 21 | 5e | 六四馬 | board-partial（?=13） |
| 22 | 3b | 三三金 | board-partial（?=16） |
| 23 | 7b | 一八角 | board-sparse（?=21） |
| 24 | 2c | 一三飛 | board-partial（?=14） |
| 25 | 8c | 二九角 | board-partial（?=15） |
| 26 | 5c | 二五銀成 | board-partial（?=16） |
| 27 | 5c | 四六金 | board-partial（?=19） |
| 28 | 5d | 二七角 | board-partial（?=17） |
| 29 | 5d | 四五飛成 | board-sparse（?=23） |
| 30 | 5b | 三六金 | board-sparse（?=21） |
| 31 | 5b | 三五角成 | board-sparse（?=20） |
| 32 | 4e | 六五角成 | board-partial（?=17） |
| 33 | 6e | 五五龍 | board-partial（?=16） |
| 34 | 1d | 五一金 | board-partial（?=13） |
| 35 | 9d | 五九歩 | board-sparse（?=22） |
| 36 | 2d | 四一飛 | board-partial（?=14） |
| 37 | 8d | 四九飛 | board-sparse（?=26） |
| 38 | 2f | 五二桂成 | board-good（?=11） |
| 39 | 7g | 七六飛 | board-sparse（?=23） |
| 40 | 4d | 三四と | board-partial（?=13） |
| 41 | 6d | 五六金 | board-partial（?=13） |
| 42 | 2g | 七三飛 | board-sparse（?=23） |
| 43 | 8g | 五六角 | board-partial（?=13） |
| 44 | 3h | 三三飛打 | board-sparse（?=20） |
| 45 | 7h | 八九銀 | board-sparse（?=22） |
| 46 | 1h | 八四龍 | board-partial（?=15） |
| 47 | 9h | 九八金 | board-sparse（?=22） |
| 48 | 3d | 四二銀成 | board-good（?=11） |
| 49 | 7d | 五七金 | board-good（?=10） |
| 50 | 5a | 三五香 | board-sparse（?=35） |

## 将棋精妙 下巻（検証済みのみ）

| 番 | 後手玉 | 初手 | 信頼度 |
|---|---|---|---|
| 1 | 9b | 一九角成 | board-partial（?=16） |
| 2 | 6d | 四七金 | board-sparse（?=24） |
| 3 | 4d | 三三銀 | board-sparse（?=24） |
| 4 | 8b | 三七歩成 | board-partial（?=13） |
| 5 | 1d | 三二銀 | board-partial（?=18） |
| 6 | 8b | 三九銀 | board-sparse（?=75） |
| 7 | 1a | 一七飛 | board-sparse（?=79） |
| 8 | 9a | 一八角成 | board-good（?=9） |
| 9 | 1a | 一八香 | board-sparse（?=20） |
| 10 | 4a | 三二金 | board-partial（?=14） |
| 11 | 8e | 五五龍 | board-partial（?=14） |
| 12 | 6c | 八三飛 | board-good（?=9） |
| 13 | 2b | 二三歩 | board-good（?=12） |
| 14 | 7b | 二六金 | board-partial（?=17） |
| 15 | 1d | 一三金 | board-sparse（?=23） |
| 16 | 6d | 五六金 | board-sparse（?=21） |
| 17 | 2b | 三二歩 | board-good（?=5） |
| 18 | 8e | 九五龍 | board-partial（?=15） |
| 19 | 4b | 九二龍 | board-partial（?=14） |
| 20 | 5c | 四六銀 | board-partial（?=19） |
| 21 | 9c | 八二銀 | board-partial（?=17） |
| 22 | 3c | 三六飛 | board-partial（?=18） |
| 23 | 8b | 三八歩 | board-good（?=8） |
| 24 | 1a | 二一歩 | board-good（?=8） |
| 25 | 7a | 二七金 | board-sparse（?=21） |
| 26 | 1a | 二三桂 | board-partial（?=13） |
| 27 | 7d | 六五龍 | board-partial（?=19） |
| 28 | 7b | 三七と | board-partial（?=17） |
| 29 | 1e | 三五龍 | board-partial（?=14） |
| 30 | 9b | 三八龍 | board-partial（?=17） |
| 31 | 2b | 二一龍 | board-partial（?=15） |
| 32 | 9a | 二九歩 | board-good（?=8） |
| 33 | 1c | 四一銀 | board-partial（?=13） |
| 34 | 7d | 四六金 | board-partial（?=15） |
| 35 | 4b | 四九龍 | board-partial（?=16） |
| 36 | 4c | 三三金 | board-partial（?=15） |
| 37 | 6d | 三七龍 | board-partial（?=15） |
| 38 | 7e | 五六金 | board-sparse（?=20） |
| 39 | 2c | 四二香 | board-sparse（?=25） |
| 40 | 6g | 六六金 | board-sparse（?=23） |
| 41 | 4e | 四五龍 | board-partial（?=19） |
| 42 | 8a | 二八銀 | board-partial（?=13） |
| 43 | 1g | 一八香 | board-sparse（?=21） |
| 44 | 9a | 八二銀 | board-good（?=11） |
| 45 | 5c | 六二角 | board-sparse（?=20） |
| 46 | 8a | 四一飛 | board-partial（?=19） |
| 47 | 1c | 三二飛 | board-sparse（?=24） |
| 48 | 4d | 三四龍 | board-partial（?=19） |
| 49 | 8a | 二八銀 | board-partial（?=15） |
| 50 | 9b | 九三銀 | board-good（?=11） |
| 51 | 2a | 二三飛 | board-sparse（?=24） |
| 52 | 6e | 五三龍 | board-partial（?=16） |
| 53 | 2a | 二一歩成 | board-sparse（?=20） |
| 54 | 2b | 三三銀 | board-sparse（?=20） |
| 55 | 9b | 三九飛 | board-good（?=5） |
| 56 | 3d | 三三龍 | board-partial（?=16） |
| 57 | 8a | 二九歩成 | board-good（?=8） |
| 58 | 1b | 一二馬 | board-partial（?=18） |
| 59 | 6f | 三五飛成（開き王手） | board-partial（?=15） |
| 60 | 1a | 二一歩 | board-sparse（?=21） |
| 61 | 8c | 八九龍 | board-good（?=7） |
| 62 | 1b | 四三角成 | board-partial（?=13） |
| 63 | 9a | 二九歩 | board-partial（?=16） |
| 64 | 1b | 一一桂成 | board-partial（?=16） |
| 65 | 6g | 六五馬 | board-sparse（?=22） |
| 66 | 7b | 二六角成 | board-sparse（?=20） |
| 67 | 4e | 五三金 | board-sparse（?=22） |
| 68 | 3d | 三四角 | board-good（?=12） |
| 69 | 8c | 三七飛成 | board-partial（?=19） |
| 70 | 9a | 一三龍 | board-sparse（?=21） |
| 71 | 1a | 二一歩 | board-sparse（?=20） |
| 72 | 8a | 二七と | board-good（?=12） |
| 73 | 1f | 六二馬 | board-sparse（?=22） |
| 74 | 8c | 二八角成 | board-good（?=9） |
| 75 | 4f | 七四龍 | board-partial（?=18） |
| 76 | 8a | 一七金 | board-good（?=9） |
| 77 | 2a | 一一歩成 | board-sparse（?=22） |
| 78 | 9b | 二八金 | board-good（?=8） |
| 79 | 1a | 二一歩 | board-partial（?=16） |
| 81 | 4b | 四四龍 | board-sparse（?=22） |
| 82 | 6a | 二五馬 | board-partial（?=18） |
| 83 | 5b | 三四角成 | board-sparse（?=21） |
| 84 | 6a | 四六飛 | board-partial（?=14） |
| 85 | 3f | 二六飛成 | board-partial（?=16） |
| 86 | 9c | 二九飛 | board-partial（?=13） |
| 87 | 5d | 四六飛成 | board-partial（?=17） |
| 88 | 9b | 三九歩 | board-good（?=12） |
| 89 | 1a | 二一銀 | board-partial（?=16） |
| 90 | 9c | 二九馬 | board-partial（?=13） |
| 91 | 4c | 三五銀成 | board-sparse（?=20） |
| 92 | 1a | 六一飛 | board-good（?=8） |
| 93 | 7c | 三二飛 | board-partial（?=19） |
| 94 | 8e | 六七金 | board-partial（?=19） |
| 95 | 1b | 一四香 | board-partial（?=14） |
| 96 | 7b | 一六龍 | board-sparse（?=30） |
| 97 | 5b | 三五角成 | board-partial（?=19） |
| 98 | 1b | 三二金 | board-partial（?=19） |
| 99 | 6e | 七五馬 | board-partial（?=19） |
| 100 | 3b | 三一飛成 | board-sparse（?=20） |

## 集計

- 貫珠詰手: 検証済み 50/50（good 9 / partial 21 / sparse 20）
- 精妙下巻: 検証済み 99/100（good 19 / partial 50 / sparse 30）
- 詰手読みのみ（機械検証不可）: 貫珠 0題。五十題すべて盤面検証（十二〜十九番は玉位置を原寸確認し、王手が隣接または飛び越えない駒で決まるため）
- 未検証は **精妙 八十番** のみ。題簽（R21左 x≈44%）の左の列群（一七角成・四四龍・六二角成）も、右頁の頁またぎ候補（一二角・五四飛・四八龍・八六龍）も玉9二に王手にならず、本文の先頭列が未特定（`docs/seimyo-transcription.md` の「八十番の本文列の全読み」）。

