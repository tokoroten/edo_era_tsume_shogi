# 駒の規則に反している draft（自動生成）

駒一式は 歩18・香4・桂4・銀4・金4・角2・飛2・玉2。成駒は元の種類で数える。
この上限を超える盤面と、同じ側の不成の歩が同じ筋に2枚ある盤面（二歩）、
動けない位置に残った歩・香・桂（死に駒）は、**印刷をどう読んでも成立しない**ので、
転記の誤りである。修正は原寸の読みにしか戻せないが、ここに挙がった題は
「完成」と数えてはいけない。**（印字）** を付けた題は、監査ではなく**印字そのもの**が
上限を超えている（詰将棋は玉方に余分な駒を与えることがあり、玉図には金5枚・銀5枚・桂5枚の図が
複数ある。docs/open-issues.json の gyokuzu-014-material / gyokuzu-032-material / gyokuzu-037-material / gyokuzu-041-material / gyokuzu-048-material / gyokuzu-060-material / gyokuzu-073-material / gyokuzu-080-material / gyokuzu-082-material / gyokuzu-087-material / gyokuzu-096-material / gyokuzu-099-material / gyokuzu-100-material）。
盤面は曲げない。

`python tools/material_audit.py --write` で作り直す。

| 書 | 題 | `?` | 内容 |
|---|---|---|---|
| gyokuzu | 14 | 0 | 総数超過 金5枚（印字） |
| gyokuzu | 32 | 0 | 総数超過 桂5枚（印字） |
| gyokuzu | 37 | 0 | 総数超過 金5枚（印字） |
| gyokuzu | 41 | 0 | 総数超過 銀5枚（印字） |
| gyokuzu | 48 | 0 | 総数超過 銀5枚（印字） |
| gyokuzu | 60 | 0 | 総数超過 金5枚（印字） |
| gyokuzu | 73 | 0 | 総数超過 金5枚（印字） |
| gyokuzu | 80 | 0 | 総数超過 銀5枚（印字） |
| gyokuzu | 82 | 0 | 総数超過 銀5枚（印字） |
| gyokuzu | 87 | 0 | 総数超過 銀5枚（印字） |
| gyokuzu | 96 | 0 | 総数超過 銀5枚（印字） |
| gyokuzu | 99 | 0 | 総数超過 金5枚（印字） |
| gyokuzu | 100 | 0 | 総数超過 金5枚（印字） |
| meijin | 4 | 0 | 二歩 1筋先手／死に駒 91・11 |
| meijin | 9 | 0 | 死に駒 41・11 |
| meijin | 14 | 1 | 総数超過 飛3枚 |
