# 解読報告Issueの運用（人間報告→エージェント取込）

`web/drafts.html` の各図面カードにある「GitHub Issueで解読結果を報告する」
リンクは、記入欄入りの報告フォーム（タイトル・本文プリフィル）を開く。
人間が目視で取り込んだ棋譜・盤面はこのIssueに書いてもらい、
エージェントが後で舐めて `drafts/` に反映する体制のための手順書である。

根拠・制限は `CONTRIBUTING.md`・`docs/data-policy.md` §§1–4・
`docs/gyokuzu-transcription.md`・`docs/kinza-transcription.md` に従う。
本書は運用手順のみを定め、転記基準を変更しない。

## 1. Issueの作り方（人間向け）

1. `drafts.html` で対象図面を開き、「GitHub Issueで解読結果を報告する」を押す。
2. 開いたフォームの空欄（```sfen / ```usi / 読取源 / 備考）を埋める。
   - 盤面読み: 読み取ったSFEN全文。不明升は `?` のまま残す（推測で埋めない）。
   - 手順読み: USI配列または日本語棋譜。不明手は `????` と書く。
   - 読取源（必須）: NDL PID / RID / 列範囲・丁（例 `NDL PID:861197 R0000010右`）。
     NDL一次資料スキャンの直接読取のみ。個人サイト・非政府団体サイトの
     参照・記載は禁止。
   - 推測箇所は「推測」と明記すること。
3. そのまま投稿する。ラベル `decipher` が自動付与される
   （初回は管理者がラベル `decipher` を作成すること）。

## 2. 報告フォーマット v1（OT-DECIPHER-REPORT v1）

生成リンク（`tools/build_drafts_page.py` `issue_url()`）が埋め込む形式。
エージェントはこのマーカーを頼りに回収する。

- 先頭コメント: `<!-- OT-DECIPHER-REPORT v1 | id:<draft-id> -->`
- `## 対象`: id・現SFEN・出典頁・読取源・NDLリンク（自動記入・編集不要）
- `## 盤面読み`: ```sfen フェンス（人間が記入）
- `## 手順読み`: ```usi フェンス（人間が記入）
- `## 読取源`: NDL PID/RID/列範囲・丁（人間が記入・必須）
- `## 備考`: 印影・くずし・推測箇所の明示（人間が記入）

## 3. エージェントの取込手順

1. 回収: `gh issue list --label decipher --state open --json number,title,body`
   で未処理Issueを列挙し、本文の `OT-DECIPHER-REPORT v1 | id:` を読む。
   マーカーなし・id不正のIssueは取込対象外（コメントで理由を返し放置）。
2. 検証（取込前に必ず行う）:
   - ```sfen が81升相当のSFEN構文か（`?` 許容）。構文不正は取込不可。
   - 読取源に NDL PID/RID の記載があるか。なければ取込不可。
   - `推測` と明記された升・手は `?` / `????` に倒して扱う。
   - solver出力・既存手順のコピーでないか（`intended_*` へのsolver転記は禁止。
     `CONTRIBUTING.md` Ground rule 5）。
3. 反映: 対象 `drafts/NNN.json` の `notes` に報告要旨（Issue番号・読取源・
   読取内容・推測箇所）を追記する。SFENの `?` 確定は高確信度のみ
   （各転記手順書の先後・丁ルールに従い、確信度不足は `?` 維持）。
   `sfen` の直接書換えで辻褄合わせをしない。`needs_manual_review: true` を維持。
4. 検証: `python tools/validate.py --draft <file>` → `python tests/run_tests.py`。
5. 完了したIssueは、反映コミットSHAをコメントして `close` する。
   部分反映は `close` せず残件をコメントに残す。

## 4. 注意

- Issue本文の棋譜・盤面は未検証の人間報告であり、そのまま正解にしない。
  `solution_usi` への昇格は各転記手順書 §3/§6 の昇格条件を満たした後のみ。
- 同一draftへの並行報告は逐次処理し、先勝ちで上書きしない
  （`.opencode/ralph-loop.local.md` の並行セッション調整に準じる）。
- `gh` コマンドの実行・Issueのcloseは人間の権限で行うものとし、
  エージェントは procéder（回収・検証・反映パッチの用意）までを担う。
  権限がある場合のみ `gh issue close` を実行する。
