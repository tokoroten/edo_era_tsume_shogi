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
| 9 | 8c | 六八龍 | board-sparse（?=21） |
| 10 | 1c | 四二銀 | board-sparse（?=20） |
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
| 29 | 5d | 五四飛成 | board-sparse（?=23） |
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
| 45 | 7h | 八九銀 | board-sparse（?=23） |
| 46 | 1h | 八四龍 | board-partial（?=15） |
| 47 | 9h | 九八金 | board-sparse（?=22） |
| 48 | 3d | 四二銀成 | board-good（?=11） |
| 49 | 7d | 五七金 | board-good（?=10） |
| 50 | 5a | 三五香 | board-sparse（?=35） |

## 将棋精妙 下巻（検証済みのみ）

| 番 | 後手玉 | 初手 | 信頼度 |
|---|---|---|---|
| 1 | 9b | 一九角成 | board-partial（?=16） |
| 2 | 6d | 四七金 | board-good（?=1） |
| 3 | 4d | 三三銀 | board-good（?=1） |
| 4 | 8b | 三七歩成 | board-good（?=0） |
| 5 | 1d | 三二銀 | board-good（?=3） |
| 6 | 8b | 三九銀 | board-good（?=1） |
| 7 | 1a | 一七飛 | board-sparse（?=79） |
| 8 | 9a | 一八角成 | board-good（?=1） |
| 9 | 1a | 一八香 | board-sparse（?=20） |
| 10 | 4a | 三二金 | board-good（?=1） |
| 11 | 8e | 五五龍 | board-good（?=3） |
| 12 | 6c | 三八飛 | board-good（?=1） |
| 13 | 2b | 二三歩 | board-good（?=2） |
| 14 | 7b | 二六金 | board-partial（?=17） |
| 15 | 1d | 三一金 | board-good（?=5） |
| 16 | 6d | 五六金 | board-good（?=1） |
| 17 | 2b | 三二歩 | board-good（?=0） |
| 18 | 8e | 五九龍 | board-good（?=4） |
| 19 | 4b | 九二龍 | board-good（?=1） |
| 20 | 5c | 四六銀 | board-good（?=2） |
| 21 | 9c | 八二銀 | board-good（?=3） |
| 22 | 3c | 三六飛 | board-good（?=0） |
| 23 | 8b | 三八歩 | board-good（?=2） |
| 24 | 1a | 二一歩 | board-good（?=2） |
| 25 | 7a | 二七金 | board-good（?=5） |
| 26 | 1a | 二三桂 | board-good（?=3） |
| 27 | 7d | 五六龍 | board-good（?=3） |
| 28 | 7b | 三七と | board-good（?=2） |
| 29 | 1e | 三五龍 | board-partial（?=14） |
| 30 | 9b | 三八龍 | board-partial（?=17） |
| 31 | 2b | 二一龍 | board-good（?=3） |
| 32 | 9a | 二九歩 | board-good（?=0） |
| 33 | 1c | 四一銀 | board-good（?=1） |
| 34 | 7d | 四六金 | board-good（?=4） |
| 35 | 4b | 四九龍 | board-partial（?=16） |
| 36 | 4c | 三三銀成 | board-good（?=2） |
| 37 | 6d | 三七龍 | board-partial（?=15） |
| 38 | 7e | 五六金 | board-good（?=0） |
| 39 | 2c | 四二香 | board-sparse（?=25） |
| 40 | 6g | 六六金 | board-good（?=3） |
| 41 | 4e | 四五龍 | board-good（?=2） |
| 42 | 8a | 二八銀 | board-partial（?=13） |
| 43 | 1g | 一八香 | board-sparse（?=21） |
| 44 | 9a | 八二銀 | board-good（?=1） |
| 45 | 5c | 二六角 | board-good（?=3） |
| 46 | 8a | 一四飛 | board-good（?=2） |
| 47 | 1c | 三二飛 | board-good（?=0） |
| 48 | 4d | 三四龍 | board-partial（?=19） |
| 49 | 8a | 二八銀 | board-good（?=0） |
| 50 | 9b | 九三銀 | board-good（?=3） |
| 51 | 2a | 二三飛 | board-good（?=2） |
| 52 | 6e | 五三龍 | board-partial（?=16） |
| 53 | 2a | 二一歩成 | board-sparse（?=20） |
| 54 | 2b | 三三銀 | board-good（?=2） |
| 55 | 9b | 三九飛 | board-good（?=1） |
| 56 | 3d | 三三龍 | board-good（?=0） |
| 57 | 8a | 二九歩成 | board-good（?=0） |
| 58 | 1b | 一二馬 | board-good（?=5） |
| 59 | 6f | 三五飛成（開き王手） | board-good（?=1） |
| 60 | 1a | 二一歩 | board-good（?=3） |
| 61 | 8c | 九八龍 | board-good（?=7） |
| 62 | 1b | 四三角成 | board-good（?=2） |
| 63 | 9a | 二九歩 | board-good（?=2） |
| 64 | 1b | 一一桂成 | board-good（?=1） |
| 65 | 6g | 六五馬 | board-good（?=3） |
| 66 | 7b | 二六角成 | board-good（?=5） |
| 67 | 4e | 五三金 | board-good（?=0） |
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
| 80 | 9b | 一七角成（開き王手） | board-good（?=0） |
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
- 精妙下巻: 検証済み 100/100（good 61 / partial 25 / sparse 14）
- 詰手読みのみ（機械検証不可）: 貫珠 0題。五十題すべて盤面検証（十二〜十九番は玉位置を原寸確認し、王手が隣接または飛び越えない駒で決まるため）
- 2026-11-23: 八十番を3モデル（Claude/Opus・Codex/gpt-6.2-sol・OpenCode/muse-spark-1.3）の多数決で補充し 100/100。初手は **一七角成 = 9c7a+**（角9三が退き9八飛の筋が開く開き王手）。盤面は AI 読解の多数決であり `status.position_verified` は false のまま（人手による原寸照合は未了）。8七（後手金/と）は Opus+Codex=金、Muse+事前目視=と で未決着。solver は 9c7a+ を合法な王手手として列挙、max-ply 11・80M nodes では UNKNOWN（不成立は示されず）。

