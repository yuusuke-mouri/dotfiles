#!/usr/bin/env python3
"""
analyze_style.py - 既存記事から文体パターンを抽出し、style_guide.md を生成

使用方法:
    python3 analyze_style.py

出力:
    references/style_guide.md を更新（または新規作成）

依存パッケージ:
    pip install janome pyyaml
"""

import os
import re
import glob
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple

# オプション: 形態素解析用（インストールされていない場合はスキップ）
try:
    from janome.tokenizer import Tokenizer
    JANOME_AVAILABLE = True
except ImportError:
    JANOME_AVAILABLE = False
    print("Warning: janome not installed. Some analysis features will be limited.")
    print("Install with: pip install janome")


class StyleAnalyzer:
    """既存記事の文体を分析するクラス"""

    def __init__(self, corpus_dir: str):
        self.corpus_dir = Path(corpus_dir)
        self.articles: List[Dict] = []
        self.tokenizer = Tokenizer() if JANOME_AVAILABLE else None

    def load_articles(self) -> int:
        """corpus/articles/ から全記事を読み込む"""
        pattern = self.corpus_dir / "articles" / "*.md"
        files = glob.glob(str(pattern))

        for filepath in files:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # frontmatter を除去
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        content = parts[2]
                self.articles.append({
                    'path': filepath,
                    'content': content.strip()
                })

        return len(self.articles)

    def analyze_sentence_length(self) -> Dict:
        """文長統計を計算"""
        all_sentences = []
        for article in self.articles:
            # 文を分割（。！？で区切る）
            sentences = re.split(r'[。！？\n]', article['content'])
            sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
            all_sentences.extend(sentences)

        if not all_sentences:
            return {'avg': 0, 'min': 0, 'max': 0, 'median': 0}

        lengths = [len(s) for s in all_sentences]
        lengths.sort()

        return {
            'avg': sum(lengths) / len(lengths),
            'min': min(lengths),
            'max': max(lengths),
            'median': lengths[len(lengths) // 2],
            'total_sentences': len(all_sentences)
        }

    def analyze_paragraph_pattern(self) -> Dict:
        """段落構成パターンを分析"""
        paragraph_lengths = []
        for article in self.articles:
            # 空行で段落を分割
            paragraphs = re.split(r'\n\s*\n', article['content'])
            for p in paragraphs:
                if p.strip() and not p.strip().startswith('#'):
                    # 段落内の文数をカウント
                    sentences = re.split(r'[。！？]', p)
                    sentence_count = len([s for s in sentences if s.strip()])
                    if sentence_count > 0:
                        paragraph_lengths.append(sentence_count)

        if not paragraph_lengths:
            return {'avg_sentences_per_paragraph': 0}

        return {
            'avg_sentences_per_paragraph': sum(paragraph_lengths) / len(paragraph_lengths),
            'total_paragraphs': len(paragraph_lengths)
        }

    def analyze_frequent_expressions(self) -> Dict:
        """頻出表現を抽出"""
        # 接続詞パターン
        connectors = [
            'そして', 'しかし', 'でも', 'ただ', 'つまり', 'なぜなら',
            '一方で', '例えば', 'むしろ', 'ところが', 'だから', 'また',
            'さらに', '要するに', '結局', 'そこで', 'このように'
        ]

        connector_counts = Counter()
        all_text = ' '.join([a['content'] for a in self.articles])

        for conn in connectors:
            count = all_text.count(conn)
            if count > 0:
                connector_counts[conn] = count

        # 語尾パターン
        ending_patterns = {
            'です': len(re.findall(r'です[。\n]', all_text)),
            'ます': len(re.findall(r'ます[。\n]', all_text)),
            'でした': len(re.findall(r'でした[。\n]', all_text)),
            'ました': len(re.findall(r'ました[。\n]', all_text)),
            'だ': len(re.findall(r'[^し]だ[。\n]', all_text)),
            'である': len(re.findall(r'である[。\n]', all_text)),
        }

        # 一人称
        first_person = {
            '私': all_text.count('私は') + all_text.count('私の') + all_text.count('私が'),
            '僕': all_text.count('僕は') + all_text.count('僕の') + all_text.count('僕が'),
        }

        return {
            'connectors': dict(connector_counts.most_common(10)),
            'endings': ending_patterns,
            'first_person': first_person
        }

    def analyze_heading_structure(self) -> Dict:
        """見出し構造を分析"""
        h2_counts = []
        h3_counts = []

        for article in self.articles:
            h2 = len(re.findall(r'^## ', article['content'], re.MULTILINE))
            h3 = len(re.findall(r'^### ', article['content'], re.MULTILINE))
            h2_counts.append(h2)
            h3_counts.append(h3)

        return {
            'avg_h2_per_article': sum(h2_counts) / len(h2_counts) if h2_counts else 0,
            'avg_h3_per_article': sum(h3_counts) / len(h3_counts) if h3_counts else 0,
        }

    def analyze_opening_patterns(self) -> List[str]:
        """導入パターンを抽出"""
        openings = []
        for article in self.articles:
            # 最初の段落を取得
            paragraphs = article['content'].split('\n\n')
            for p in paragraphs:
                if p.strip() and not p.strip().startswith('#'):
                    # 最初の100文字を取得
                    opening = p.strip()[:100]
                    openings.append(opening)
                    break
        return openings[:5]  # 最初の5つのみ返す

    def generate_style_guide(self) -> str:
        """分析結果からstyle_guide.mdを生成"""
        sentence_stats = self.analyze_sentence_length()
        paragraph_stats = self.analyze_paragraph_pattern()
        expressions = self.analyze_frequent_expressions()
        headings = self.analyze_heading_structure()

        # 一人称の判定
        first_person = '私' if expressions['first_person']['私'] > expressions['first_person']['僕'] else '僕'

        # 語尾の判定
        desu_masu = expressions['endings']['です'] + expressions['endings']['ます']
        da_dearu = expressions['endings']['だ'] + expressions['endings']['である']
        primary_style = 'です・ます調' if desu_masu > da_dearu else 'だ・である調'

        guide = f"""# 文体ガイドライン

> このファイルは analyze_style.py によって自動生成されました。
> 分析対象: {len(self.articles)}記事

---

## 一人称・語尾

### 一人称
- 基本: 「{first_person}」
- 使用頻度: 私={expressions['first_person']['私']}回, 僕={expressions['first_person']['僕']}回

### 語尾
- 基本: 「{primary_style}」
- 強調・主張: 「だ・である」調を混ぜる
- 問いかけ: 「〜ではないでしょうか？」「〜ありませんか？」

---

## 文章リズム

### 文長
- 平均文長: {sentence_stats['avg']:.1f}文字
- 最小: {sentence_stats['min']}文字, 最大: {sentence_stats['max']}文字
- 中央値: {sentence_stats['median']}文字
- 分析文数: {sentence_stats['total_sentences']}文

### 段落構成
- 平均: {paragraph_stats['avg_sentences_per_paragraph']:.1f}文/段落
- 改行頻度: 高め（読みやすさ重視）

---

## 特徴的表現

### 頻出接続詞・つなぎ言葉
"""
        for conn, count in list(expressions['connectors'].items())[:7]:
            guide += f"- 「{conn}」({count}回)\n"

        guide += f"""
### 強調表現
- **太字** を効果的に使用
- 「これが重要で」
- 「〜なんです」

---

## 記事構成パターン

### 見出し数
- H2（##）: 平均 {headings['avg_h2_per_article']:.1f}個/記事
- H3（###）: 平均 {headings['avg_h3_per_article']:.1f}個/記事

### 基本構成
1. 導入（問いかけ or エピソード）
2. 問題提起
3. 本論（解決策・考え方）
4. 具体例・実践
5. まとめ

---

## 避けるべき表現

- 過度な専門用語（説明なしで使わない）
- 断定的すぎる表現（「絶対に」「必ず」）
- 冗長な前置き
- 言い訳・謙遜しすぎ
- 競合への攻撃（→ content_policy.md 参照）

---

## ハッシュタグ

### 基本タグ
- #DX推進
- #中小企業経営
- #IT人材

### テーマ別タグ
- プロジェクト管理: #アジャイル #スクラム #プロジェクトマネジメント
- 人材: #ひとり情シス #IT人材不足 #伴走支援
- 技術: #ノーコード #API連携 #クラウド
- キャリア: #フリーランス #独立 #キャリア

### 選定ルール
- 5-8個程度
- ターゲット読者が検索しそうなキーワード
- 一般的すぎず、ニッチすぎず
"""
        return guide

    def run(self, output_path: str = None):
        """分析を実行してstyle_guide.mdを生成"""
        print(f"Loading articles from {self.corpus_dir}...")
        count = self.load_articles()
        print(f"Loaded {count} articles")

        if count == 0:
            print("No articles found. Please run fetch_note_articles.py first.")
            return

        print("Analyzing style patterns...")
        guide = self.generate_style_guide()

        if output_path is None:
            output_path = self.corpus_dir.parent / "references" / "style_guide.md"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(guide)

        print(f"Style guide generated: {output_path}")


def main():
    # スクリプトのディレクトリからの相対パスでcorpusを探す
    script_dir = Path(__file__).parent.parent
    corpus_dir = script_dir / "corpus"

    if not corpus_dir.exists():
        print(f"Error: corpus directory not found: {corpus_dir}")
        print("Please run fetch_note_articles.py first.")
        return

    analyzer = StyleAnalyzer(corpus_dir)
    analyzer.run()


if __name__ == "__main__":
    main()
