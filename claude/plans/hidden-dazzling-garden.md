# note.com記事取得スクリプト実装プラン

## 概要
note.comアカウント（https://note.com/yusukemori_ravi）から全記事を取得し、Markdown形式に変換。画像もダウンロードしてプロジェクト内に保存する。

## 要件
- **取得範囲**: 全記事（現在5記事）
- **言語**: Python
- **ファイル名**: `day{番号}_{タイトルスラグ}_{記事ID}.md`
- **画像保存先**: `./images/` フォルダ
- **フロントマター**: Obsidianボルト標準に準拠したYAML形式

## 作成ファイル

### 1. fetch_note_articles.py（メインスクリプト）
**場所**: `/mnt/c/Users/yuusu/Documents/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/fetch_note_articles.py`

**主要クラス構成**:
```python
- NoteArticleScraper: メインオーケストレータ
- ArticleParser: HTML解析・データ抽出
- HTMLToMarkdownConverter: HTML→Markdown変換
- ImageDownloader: 画像ダウンロード・ローカルパス管理
- MarkdownGenerator: フロントマター付きMarkdownファイル生成
```

**処理フロー**:
1. プロフィールページ取得（https://note.com/yusukemori_ravi）
2. 記事一覧の抽出（JSON-LD or 埋め込みJSONから）
3. 各記事の詳細ページ取得
4. HTML→Markdown変換
5. 画像URLの抽出とダウンロード
6. ローカルパスへの置換
7. フロントマター付きファイルの生成

**エラーハンドリング**:
- HTTP 404/429: リトライロジック（指数バックオフ）
- パース失敗: 複数の抽出戦略でフォールバック
- ファイルシステムエラー: クリアなエラーメッセージで中断

### 2. requirements.txt
**場所**: `/mnt/c/Users/yuusu/Documents/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/requirements.txt`

```
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
html2text>=2020.1.16
python-slugify>=8.0.0
pyyaml>=6.0
python-dateutil>=2.8.0
```

### 3. README.md（使用方法ドキュメント）
**場所**: `/mnt/c/Users/yuusu/Documents/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/README.md`

- セットアップ手順
- 実行方法
- コマンドライン引数の説明
- トラブルシューティング

### 4. ディレクトリ構成
```
note.com2025AdventCalendar/
├── fetch_note_articles.py
├── requirements.txt
├── README.md
├── calendar.md (既存)
├── images/
│   └── {article_id}/
│       └── image_{n}.{ext}
└── articles/
    └── day{n}_{slug}_{article_id}.md
```

## 出力Markdownファイル構造

```markdown
---
type: "article"
source: "note.com"
article_id: "na3f6f4e2138e"
day_number: 1
title: "記事タイトル"
author: "毛利裕介"
publish_date: "2025-12-05"
publish_datetime: "2025-12-05T22:54:07+09:00"
original_url: "https://note.com/yusukemori_ravi/n/na3f6f4e2138e"
status: "published"
category: "advent-calendar-2025"
tags:
  - アドベントカレンダー
created: "2025-12-06"
fetched_at: "2025-12-06T12:00:00+09:00"
---

# 記事タイトル

[本文（Markdown形式）...]

![画像](../images/{article_id}/image_1.png)

---

**原文URL**: [note.com](https://note.com/...)
**公開日**: 2025年12月5日
```

## 実装戦略

### HTML解析アプローチ
note.comはReact Server Componentsを使用しているため、3つの抽出戦略を用意:

1. **JSON-LD Schema抽出**（優先）: `<script type="application/ld+json">`からBlogPostingデータを取得
2. **埋め込みReact State抽出**（フォールバック）: JavaScriptコードから記事オブジェクトを抽出
3. **HTMLセレクタ抽出**（最も信頼性が高い）: `.p-article__body`などのクラスから本文を取得

### ファイル名生成ロジック
```python
# 例: day01_connecting-the-dots_na3f6f4e2138e.md
day_number = 1  # 公開日順で自動採番
slug = slugify(title, max_length=50)  # 日本語タイトルをスラグ化
article_id = "na3f6f4e2138e"  # note.comの記事ID
filename = f"day{day_number:02d}_{slug}_{article_id}.md"
```

### 画像処理
- 記事内の画像URLを抽出（`assets.st-note.com`など）
- `images/{article_id}/`サブディレクトリに保存
- Markdown内のURLを相対パス（`../images/{article_id}/image_n.ext`）に置換

## 実行方法

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# スクリプト実行（基本）
python fetch_note_articles.py

# オプション指定
python fetch_note_articles.py \
  --username yusukemori_ravi \
  --output-dir ./articles \
  --image-dir ./images \
  --verbose
```

## コマンドライン引数
- `--username`: note.comユーザー名（デフォルト: yusukemori_ravi）
- `--output-dir`: Markdown出力先（デフォルト: ./articles）
- `--image-dir`: 画像保存先（デフォルト: ./images）
- `--max-articles`: 取得する最大記事数
- `--start-day`: 開始日番号（デフォルト: 1）
- `--verbose, -v`: 詳細ログ表示
- `--skip-existing`: 既存ファイルをスキップ

## 実装マイルストーン

1. **基本プロフィールスクレイピング**: 記事一覧の取得と表示
2. **単一記事処理**: 1記事のHTML→Markdown変換とファイル保存
3. **画像処理**: 画像ダウンロードとパス置換
4. **バッチ処理**: 全記事の一括処理
5. **エラーハンドリング＆仕上げ**: リトライロジック、ログ、ドキュメント

## 注意事項

### 技術的制約
- note.comには公式APIがないため、スクレイピングに依存
- サイト構造変更時に動作しなくなる可能性あり
- レート制限回避のため、リクエスト間に1-2秒の遅延を設定

### 倫理的考慮
- ダウンロードしたコンテンツは著作者（毛利裕介氏）の知的財産
- 個人的なナレッジマネジメント用途のみ
- 原文URLと著者情報を常に保持
- 再配布は行わない

## 次のステップ（実装後）

1. スクリプト実行して現在の5記事を取得
2. Obsidianで生成されたMarkdownを確認
3. calendar.mdの計画と実際の記事を照合
4. 今後の記事更新時に定期実行する仕組みを検討
5. 必要に応じてボルトのTemplatesフォルダに記事テンプレートを追加

## 重要ファイルパス

**作成するファイル**:
- `/mnt/c/Users/yuusu/Documents/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/fetch_note_articles.py`
- `/mnt/c/Users/yuusu/Documents/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/requirements.txt`
- `/mnt/c/Users/yuusu/Documents/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/README.md`

**参照するファイル**:
- `/mnt/c/Users/yuusu/Documents/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/calendar.md` (既存の計画)
- `/mnt/c/Users/yuusu/Documents/yuusuke.ap/03_Resources/Templates/template-project.md` (フロントマターの参考)

**出力先**:
- `/mnt/c/Users/yuusu/Documents/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/articles/` (Markdownファイル)
- `/mnt/c/Users/yuusu/Documents/yuusuke.ap/02_Projects/Active/note.com2025AdventCalendar/images/` (ダウンロード画像)
