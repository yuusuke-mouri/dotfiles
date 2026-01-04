#!/usr/bin/env python3
"""
research_trends.py - ターゲット層の関心トレンドを調査

使用方法:
    python3 research_trends.py [--keywords "キーワード1,キーワード2"]

注意:
    Claude CLI では web_search ツールを直接使用可能なため、
    このスクリプトは主にキーワードリスト管理と補助用途。

依存パッケージ:
    pip install pyyaml requests beautifulsoup4
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict
import argparse


def load_target_audience(references_dir: Path) -> Dict:
    """target_audience.md からターゲット情報を読み込む"""
    filepath = references_dir / "target_audience.md"

    if not filepath.exists():
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # トレンドリサーチキーワードを抽出
    keywords = []
    in_keywords_section = False

    for line in content.split('\n'):
        if 'トレンドリサーチキーワード' in line:
            in_keywords_section = True
            continue
        if in_keywords_section:
            if line.startswith('#'):
                break
            if line.strip().startswith('-'):
                # 「」内のキーワードを抽出
                keyword = line.strip().lstrip('- ').strip('「」')
                if keyword:
                    keywords.append(keyword)

    return {
        'keywords': keywords
    }


def generate_search_queries(keywords: List[str]) -> List[str]:
    """検索クエリを生成"""
    queries = []
    for kw in keywords:
        queries.append(kw)
        # 年度を追加したクエリ
        queries.append(f"{kw} 2025")

    return queries


def print_research_guide(keywords: List[str]):
    """リサーチガイドを表示"""
    print("\n" + "=" * 60)
    print("トレンドリサーチガイド")
    print("=" * 60)

    print("\n## 推奨検索キーワード\n")
    for i, kw in enumerate(keywords, 1):
        print(f"{i}. {kw}")

    print("\n## Claude CLI での使用方法\n")
    print("以下のようにWeb検索を実行できます：")
    print()
    for kw in keywords[:3]:
        print(f'  WebSearch: "{kw}"')
    print()

    print("## 情報源の優先順位\n")
    print("1. 公的機関（経産省、中小企業庁、IPA）")
    print("2. 業界団体（商工会議所、中小企業診断士協会）")
    print("3. 大手メディア（日経、ITmedia）")
    print("4. 調査会社レポート")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='ターゲット層の関心トレンドを調査'
    )
    parser.add_argument(
        '--keywords',
        type=str,
        help='カンマ区切りのキーワード（指定しない場合はtarget_audience.mdから取得）'
    )
    args = parser.parse_args()

    # スクリプトのディレクトリからの相対パスでreferencesを探す
    script_dir = Path(__file__).parent.parent
    references_dir = script_dir / "references"

    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(',')]
    else:
        target_data = load_target_audience(references_dir)
        keywords = target_data.get('keywords', [])

    if not keywords:
        print("キーワードが見つかりません。")
        print("--keywords オプションで指定するか、")
        print("references/target_audience.md にキーワードを追加してください。")
        return

    print_research_guide(keywords)

    # 検索クエリを生成
    queries = generate_search_queries(keywords)

    print("## 生成された検索クエリ\n")
    for q in queries:
        print(f"- {q}")
    print()


if __name__ == "__main__":
    main()
