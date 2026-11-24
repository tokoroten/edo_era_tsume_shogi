# 詰手の初手 検証状況（2026-11-18）

「検証済み」は、原寸の切出で読んだ初手が本編/上巻の盤面で**合法に指せて王手になる**
ことを機械検証（`tools/head_check.py`）したもの。**移動元が盤上か持駒に無い**ものは
`MOVER?`（未検証）として数えない。

- 2026-11-25 定義の明確化: 以前は「印字があり `head_unassigned` でない」ものを
  「検証済み」と数えていたため、移動元が無い `MOVER?` も含まれていた（精妙 88→65、
  貫珠 46→41）。現在は `head_check` の `OK` / `OK(drop)` のみを数える。
**信頼度**は盤面の `?` 数による: `good`(≤12) / `partial`(13-19) / `sparse`(≥20)。
`sparse` は空升が多く、王手の成立が列帰属を保証しない（`docs/procedures.md` §3.8）。
盤面が不完全で王手検証ができない題の読みは `docs/kanju-procedure-readings.json` に
`attacks_gote_king` 付きで記録する（`TestKanjuProcedureReadings` が検査）。
未検証の題は、まず「後手玉」の筋段を盤面図で確認してから列頭を読む。

## 将棋貫珠 詰手（50題）

| 番 | 後手玉 | 初手 | 信頼度 |
|---|---|---|---|
| 1 | 5a | 二五飛 | board-good（?=0） |
| 2 | 2b | 一二金 | board-good（?=3） |
| 3 | 8b | 未決（列頭 五一飛） | board-good（?=6） |
| 4 | 1b | 未決（列頭 二二龍） | board-good（?=3） |
| 5 | 9b | 一九飛 | board-good（?=3） |
| 6 | 5b | 一六銀 | board-good（?=0） |
| 7 | 5b | 二四飛 | board-good（?=0） |
| 8 | 2c | 四二金 | board-good（?=0） |
| 9 | 8c | 未決（列頭 六八龍） | board-good（?=0） |
| 10 | 1c | 四二銀 | board-good（?=0） |
| 11 | 9c | 九五龍 | board-good（?=0） |
| 12 | 1b | 三一歩成 | board-good（?=0） |
| 13 | 9b | 一八銀 | board-good（?=0） |
| 14 | 1a | 三二桂 | board-good（?=0） |
| 15 | 9a | 三八桂 | board-good（?=2） |
| 16 | 1b | 一一銀成 | board-good（?=2） |
| 17 | 9b | 八二角成 | board-good（?=0） |
| 18 | 2a | 一三銀成 | board-good（?=0） |
| 19 | 8a | 八二龍 | board-good（?=0） |
| 20 | 5e | 三七角 | board-good（?=2） |
| 21 | 5e | 未決（列頭 六四馬） | board-good（?=1） |
| 22 | 3b | 未決（列頭 三三金） | board-good（?=3） |
| 23 | 7b | 一八角 | board-good（?=0） |
| 24 | 2c | 一三飛 | board-good（?=0） |
| 25 | 8c | 二九角 | board-good（?=1） |
| 26 | 5c | 二五銀成 | board-good（?=4） |
| 27 | 5c | 四六金 | board-good（?=6） |
| 28 | 5d | 二七角 | board-good（?=3） |
| 29 | 5d | 五四飛成 | board-good（?=0） |
| 30 | 5b | 三六金 | board-good（?=1） |
| 31 | 5b | 三五角成 | board-good（?=1） |
| 32 | 4e | 六五角成 | board-good（?=4） |
| 33 | 6e | 五五金 | board-good（?=4） |
| 34 | 1d | 五一金 | board-good（?=0） |
| 35 | 9d | 五九歩 | board-good（?=3） |
| 36 | 2d | 四一飛 | board-good（?=0） |
| 37 | 8d | 四九飛 | board-good（?=5） |
| 38 | 3g | 五二桂成 | board-good（?=2） |
| 39 | 7g | 七六飛 | board-good（?=2） |
| 40 | 4d | 五五金 | board-good（?=0） |
| 41 | 6d | 五六歩 | board-good（?=2） |
| 42 | 2g | 七三飛 | board-good（?=0） |
| 43 | 8g | 五六角 | board-good（?=3） |
| 44 | 3h | 三三飛打 | board-good（?=0） |
| 45 | 7h | 七九銀 | board-good（?=0） |
| 46 | 1h | 二八金打 | board-good（?=0） |
| 47 | 9h | 九八金 | board-good（?=2） |
| 48 | 3d | 四二銀成 | board-good（?=2） |
| 49 | 7d | 五七金 | board-good（?=3） |
| 50 | 5a | 三五香 | board-good（?=0） |

## 将棋精妙 下巻（検証済みのみ）

| 番 | 後手玉 | 初手 | 信頼度 |
|---|---|---|---|
| 1 | 9b | 一九角成 | board-good（?=2） |
| 2 | 6d | 四七金 | board-good（?=0） |
| 3 | 4d | 三三銀 | board-good（?=0） |
| 4 | 8b | 三七歩成 | board-good（?=0） |
| 5 | 1d | 三二銀 | board-good（?=3） |
| 6 | 8b | 三九銀 | board-good（?=0） |
| 7 | 1a | 二一と | board-good（?=4） |
| 8 | 9a | 未決（列頭 一八角成） | board-good（?=1） |
| 9 | 1a | 二一桂成 | board-good（?=0） |
| 10 | 4a | 三二金 | board-good（?=1） |
| 11 | 8e | 未決（列頭 五五龍） | board-good（?=3） |
| 12 | 6c | 三八飛 | board-good（?=0） |
| 13 | 2b | 二三歩 | board-good（?=2） |
| 14 | 7b | 未決（列頭 二六金） | board-good（?=0） |
| 15 | 1d | 三一金 | board-good（?=3） |
| 16 | 6d | 五六金 | board-good（?=0） |
| 17 | 2b | 三二歩 | board-good（?=0） |
| 18 | 8e | 五九龍 | board-good（?=0） |
| 19 | 4b | 九二龍 | board-good（?=0） |
| 20 | 5c | 四六銀 | board-good（?=2） |
| 21 | 9c | 八二銀 | board-good（?=3） |
| 22 | 3c | 三六飛 | board-good（?=0） |
| 23 | 8b | 三八歩 | board-good（?=2） |
| 24 | 1a | 二一歩 | board-good（?=2） |
| 25 | 7a | 二七金 | board-good（?=5） |
| 26 | 1a | 三二桂 | board-good（?=3） |
| 27 | 7d | 未決（列頭 五六龍） | board-good（?=3） |
| 28 | 7b | 三七と | board-good（?=2） |
| 29 | 1e | 未決（列頭 三五龍） | board-partial（?=14） |
| 30 | 9b | 三八龍 | board-good（?=0） |
| 31 | 2b | 二一龍 | board-good（?=3） |
| 32 | 9a | 二九歩 | board-good（?=0） |
| 33 | 1c | 四一銀 | board-good（?=0） |
| 34 | 7d | 四六金 | board-good（?=0） |
| 35 | 4b | 未決（列頭 四九龍） | board-good（?=0） |
| 36 | 4c | 三三銀成 | board-good（?=2） |
| 37 | 6d | 三七龍 | board-good（?=0） |
| 38 | 7e | 未決（列頭 五六金） | board-good（?=0） |
| 39 | 2c | 四二飛 | board-good（?=3） |
| 40 | 6g | 六六金 | board-good（?=3） |
| 41 | 4e | 未決（列頭 四五龍） | board-good（?=2） |
| 42 | 9a | 一八角成 | board-good（?=0） |
| 43 | 1g | 一八銀 | board-good（?=2） |
| 44 | 9a | 八二銀 | board-good（?=0） |
| 45 | 5c | 二六角 | board-good（?=3） |
| 46 | 8a | 一四飛 | board-good（?=2） |
| 47 | 1c | 三二飛 | board-good（?=0） |
| 48 | 4d | 五四角成 | board-good（?=1） |
| 49 | 8a | 二八銀 | board-good（?=0） |
| 50 | 9b | 三九銀 | board-good（?=3） |
| 51 | 2a | 三二飛成 | board-good（?=2） |
| 52 | 6e | 六六銀 | board-good（?=2） |
| 53 | 2a | 二一歩成 | board-good（?=1） |
| 54 | 2b | 三三銀 | board-good（?=2） |
| 55 | 9b | 未決（列頭 三九飛） | board-good（?=1） |
| 56 | 3d | 未決（列頭 三三龍） | board-good（?=0） |
| 57 | 8a | 三九桂 | board-good（?=0） |
| 58 | 1b | 一二馬 | board-good（?=2） |
| 59 | 6f | 三五飛成 | board-good（?=1） |
| 60 | 1a | 二一歩 | board-good（?=3） |
| 61 | 8c | 三七歩成 | board-good（?=0） |
| 62 | 1b | 四三角成 | board-good（?=2） |
| 63 | 9a | 二九歩 | board-good（?=2） |
| 64 | 1b | 一一桂成 | board-good（?=0） |
| 65 | 6g | 未決（列頭 六五馬） | board-good（?=3） |
| 66 | 7b | 未決（列頭 二六角成） | board-good（?=3） |
| 67 | 4e | 五三金 | board-good（?=0） |
| 68 | 3d | 未決（列頭 三四角） | board-good（?=2） |
| 69 | 8c | 三七飛成 | board-good（?=0） |
| 70 | 9a | 未決（列頭 一三龍） | board-good（?=4） |
| 71 | 1a | 二一歩 | board-good（?=2） |
| 72 | 8a | 八二歩打 | board-good（?=2） |
| 73 | 1f | 二五銀 | board-good（?=3） |
| 74 | 8c | 二八角成 | board-good（?=0） |
| 75 | 4f | 七四龍 | board-good（?=3） |
| 76 | 8a | 一七金 | board-good（?=2） |
| 77 | 2a | 一一歩成 | board-good（?=2） |
| 78 | 9b | 二八金 | board-good（?=0） |
| 79 | 1a | 二一歩 | board-good（?=2） |
| 80 | 9b | 一七角成 | board-good（?=0） |
| 81 | 4b | 四四龍 | board-good（?=2） |
| 82 | 6a | 未決（列頭 二五馬） | board-good（?=2） |
| 83 | 5b | 三四角成 | board-good（?=0） |
| 84 | 6a | 未決（列頭 四六飛） | board-good（?=0） |
| 85 | 3f | 二六飛成 | board-good（?=0） |
| 86 | 9c | 二九飛 | board-good（?=2） |
| 87 | 5d | 四六飛成 | board-good（?=2） |
| 88 | 9b | 三九歩 | board-good（?=0） |
| 89 | 1a | 二一銀 | board-good（?=0） |
| 90 | 9c | 二九馬 | board-good（?=0） |
| 91 | 4c | 三五銀成 | board-good（?=2） |
| 92 | 1a | 未決（列頭 六一飛） | board-good（?=2） |
| 93 | 7c | 未決（列頭 三二飛） | board-good（?=0） |
| 94 | 8e | 六七金 | board-good（?=2） |
| 95 | 1b | 一四香 | board-good（?=0） |
| 96 | 7b | 一六龍 | board-good（?=3） |
| 97 | 5b | 未決（列頭 三五角成） | board-good（?=0） |
| 98 | 1b | 三二銀 | board-good（?=1） |
| 99 | 6e | 七五馬 | board-good（?=2） |
| 100 | 3b | 三一飛成 | board-good（?=1） |

## 集計

- 貫珠詰手: 検証済み 41/50（good 50 / partial 0 / sparse 0）。残り9題は盤面のみ採用し**初手は未決**（列頭の帰属を原本で確認）
- 精妙下巻: 検証済み 67/100（good 99 / partial 1 / sparse 0）。残り33題は盤面のみ採用し**初手は未決**
- 詰手読みのみ（機械検証不可）: 貫珠 0題。四十七題すべて盤面検証（十二〜十九番は玉位置を原寸確認し、王手が隣接または飛び越えない駒で決まるため）
- 2026-11-23: 八十番を3モデル（Claude/Opus・Codex/gpt-6.2-sol・OpenCode/muse-spark-1.3）の多数決で補充し 96/100 へ到達（当時）。初手は **一七角成 = 9c7a+**（角9三が退き9八飛の筋が開く開き王手）。盤面は AI 読解の多数決であり `status.position_verified` は false のまま（人手による原寸照合は未了）。8七（後手金/と）は Opus+Codex=金、Muse+事前目視=と で未決着。solver は 9c7a+ を合法な王手手として列挙、max-ply 11・80M nodes では UNKNOWN（不成立は示されず）。

- 2026-11-25 データの一貫性: `head_check` が `MOVER?` / `NO MOVER` / `OWN PIECE` /
  `NO CHECK` と判定した列頭は、すべて `head_unassigned: true` として記録する
  （印字は `raw` に残す）。これにより「未決」の数と `head_check` の `UNASSIGNED` が一致する
  （精妙 35・貫珠 9）。列頭レコードも `verified: false` にしてある。
