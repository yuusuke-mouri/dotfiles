---
name: note-writer
description: |
  note.com記事を生成。既存記事から文体・価値観を継承し、ターゲット層向けの新規投稿を作成。
  「note記事を書いて」「ブログ投稿を作成」「〇〇についてnoteにまとめて」と言われたときに使用。
  「fetchして」と言われたら、corpusを最新化するfetchスクリプトを実行。
allowed-tools: Read, Bash(python3:*), WebSearch, Glob
---

# note-writer

毛利裕介（yusukemori_ravi）のnote.com投稿スタイルを継承した記事生成スキル。

## fetchコマンド

「fetchして」と言われたら以下を実行:

```bash
cd ~/.claude/skills/note-writer && python3 scripts/fetch_note_articles.py --output-dir corpus/articles --image-dir corpus/images --update-check
```

**動作**:
- note.comから最新記事を取得
- 更新された記事のみダウンロード（軽量チェック）
- corpus/articles/ と corpus/images/ を更新

## 事前準備（手動実行時）

初回または記事更新時:
```bash
cd ~/.claude/skills/note-writer && python3 scripts/fetch_note_articles.py --output-dir corpus/articles --image-dir corpus/images --update-check
```

## 記事生成フロー（Phase 0-5 + Output）

### Phase 0: スキル発動・コンテキストロード

以下のファイルを順次読み込む:
- `references/style_guide.md` - 文体ルール
- `references/values_and_themes.md` - 価値観・テーマ
- `references/content_policy.md` - コンテンツ作成方針（NG/OK表現）
- `references/target_audience.md` - ターゲット定義
- `references/writing_prompt.md` - 記事執筆プロンプトテンプレート
- `references/backlog_themes.md` - 未執筆テーマリスト
- `corpus/articles/` - 既存記事の文体・事例を参照可能に

**白書データ（テーマに応じて）**:
- `references/hakusyo/README.md` - 白書データの使い方
- `references/hakusyo/hakusyo_index.md` - 白書の目次・構造
- `references/hakusyo/case_studies.md` - 事例一覧（18社）
- `references/hakusyo/note_topics.md` - 記事ネタ集

### Phase 1: 入力項目の自動構築

スキルが references/ から自動入力し、ユーザーは最小確認のみ。

**自動マッピング**:
| 入力項目 | 自動入力元 |
|----------|------------|
| ターゲット読者 | target_audience.md |
| 制約とNG | content_policy.md（自動適用） |
| 著者の独自視点 | corpus/articles/ + values_and_themes.md |
| デフォルトゴール | values_and_themes.md から推測 |
| 関連キーワード候補 | トレンドリサーチ or 既存記事 |

**ユーザーへの簡易確認**:
```
テーマ『〇〇』で記事を作成します。

【自動設定】
・ターゲット: 中小企業経営者（DX推進に悩む方）
・ゴール: 最初の一歩を踏み出す決意をする
・制約: content_policy.md 適用済み

【確認】
・追加したいキーワードはありますか？
・盛り込みたい独自の経験・事例はありますか？
・未執筆テーマと関連づけますか？

問題なければ『OK』、変更があればお知らせください。
```

**最小入力**: テーマのみ指定で記事生成可能

### Phase 2: 探求と戦略立案【内部処理】

- Web検索で上位記事を分析
- 公的統計・調査レポートを収集
- **白書データの活用**（下記テーマの場合）
- ターゲットのJTBD（本当に解決したい課題）を言語化
- キラーインサイト候補を3つ仮説立て → 最も強力な1つを採用

**白書データを活用するテーマ**:
- DX・デジタル化・IT投資
- 価格転嫁・値上げ・適正価格
- 賃上げ・人件費・労働分配率
- 人手不足・採用・人材育成
- 事業承継・後継者・M&A
- 経営戦略・経営力・経営計画
- GX・脱炭素・サステナビリティ
- スケールアップ・成長戦略

上記テーマの場合、`references/hakusyo/` のデータを参照し:
1. 該当する統計データを抽出（出典明記）
2. 関連事例（18社）から具体例を選定
3. ターゲット別の切り口・Painを確認

**詳細データが必要な場合はDify APIで検索**:
```bash
curl -s -X POST 'https://dify.ravi.fukuoka.jp/v1/chat-messages' \
  -H 'Authorization: Bearer app-2ZWUFIhY2QMuc6OKom6VQkev' \
  -H 'Content-Type: application/json' \
  -d '{"inputs": {}, "query": "【検索内容】", "response_mode": "blocking", "user": "note-writer"}'
```

### Phase 3: 構成提案

キラーインサイトと見出し構成をユーザーに提案し、承認を得る。

### Phase 4: 本文執筆

**適用ルール**:
- style_guide.md → 文体・語尾・リズム
- content_policy.md → NG表現チェック
- values_and_themes.md → 価値観の一貫性
- writing_prompt.md → PREP法、短文、問いかけ、失敗談

**出力要件**:
- タイトル案×3（13文字以内 + サブタイトル25文字以内）
- リード文（150字以内、「本記事は、」で開始）
- 本文（3000-5000文字）
- CTA + マイクロコピー
- ハッシュタグ提案

### Phase 5: 最終レビュー【内部処理】

- 全主張に根拠があるか？
- content_policy.md のNG表現に該当しないか？
- 論理は一貫しているか？
- 敵を作る表現がないか？

### Output: 最終出力

```markdown
# [タイトル13文字以内]
## 〜[サブタイトル25文字以内]〜

本記事は、[ターゲット]に向けて、[解決できること]を解説します。

[本文 3000-5000文字]

---
**タイトル案**:
1. [案1]｜[サブタイトル1]
2. [案2]｜[サブタイトル2]
3. [案3]｜[サブタイトル3]

**ハッシュタグ**: #DX推進 #中小企業 #[関連タグ]
```

## コンテンツチェック

- コンセプトから外れていないか？（IT/DX、経営と現場の断絶）
- 想定読者に響くか？（中小企業経営者、IT担当者）
- 敵を作る表現がないか？

## 参照ファイル

- `references/style_guide.md` - 文体ルール
- `references/values_and_themes.md` - 価値観・テーマ
- `references/content_policy.md` - コンテンツ作成方針（NG/OK表現）
- `references/target_audience.md` - ターゲット定義
- `references/article_templates.md` - 構成テンプレート
- `references/backlog_themes.md` - 未執筆テーマリスト
- `references/writing_prompt.md` - 記事執筆プロンプトテンプレート
- `corpus/articles/` - 既存記事（参考用）

### 白書データ（references/hakusyo/）

中小企業白書・小規模企業白書（2025年版）のデータ:
- `hakusyo/README.md` - 使い方ガイド
- `hakusyo/hakusyo_index.md` - 白書の目次・構造
- `hakusyo/case_studies.md` - 事例一覧（18社、★★★評価付き）
- `hakusyo/note_topics.md` - ターゲット別記事ネタ集

**PDFパス**:
```
~/Data/Obsidian/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/中小企業白書2025/
```
