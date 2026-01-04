#!/usr/bin/env python3
"""
note.com記事取得スクリプト

note.comアカウントから全記事を取得し、Markdown形式に変換します。
画像もダウンロードしてローカルに保存します。
"""

import argparse
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import html2text
from slugify import slugify
import yaml
from dateutil import parser as date_parser


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# データモデル
@dataclass
class Article:
    """記事メタデータ"""
    id: str
    key: str
    title: str
    publish_at: datetime
    eyecatch_url: Optional[str] = None
    url: str = ""


@dataclass
class ArticleDetail(Article):
    """詳細な記事データ"""
    body_html: str = ""
    body_markdown: str = ""
    image_urls: List[str] = field(default_factory=list)
    like_count: int = 0
    json_ld: Dict = field(default_factory=dict)
    date_modified: Optional[str] = None  # ISO 8601形式の更新日時


class ArticleParser:
    """HTML解析とデータ抽出"""

    @staticmethod
    def extract_json_ld(html: str) -> dict:
        """JSON-LDスキーマデータを抽出"""
        soup = BeautifulSoup(html, 'lxml')
        scripts = soup.find_all('script', {'type': 'application/ld+json'})

        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # @graphがある場合（Schema.org構造）
                    if '@graph' in data:
                        for item in data['@graph']:
                            if isinstance(item, dict) and item.get('@type') == 'BlogPosting':
                                return item
                    # 直接BlogPostingの場合
                    elif data.get('@type') == 'BlogPosting':
                        return data
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'BlogPosting':
                            return item
            except json.JSONDecodeError as e:
                logger.debug(f"JSON-LD parse error: {e}")
                continue

        return {}

    @staticmethod
    def extract_article_list_from_profile(html: str) -> List[dict]:
        """プロフィールページから記事リストを抽出"""
        soup = BeautifulSoup(html, 'lxml')
        articles = []

        # initialLatestNoteDataからnoteKeysを抽出（優先：確実に取得できる）
        # パターン: initialLatestNoteData\":{\"noteKeys\":[\"na3f6f4e2138e\",...]
        match = re.search(r'initialLatestNoteData\\":\{\\"noteKeys\\":\[([^\]]+)\]', html)
        if match:
            note_keys_str = match.group(1)
            # [\"na3f6f4e2138e\",\"n344e56a81c58\",...] から抽出
            note_keys = re.findall(r'\\"([a-z0-9]+)\\"', note_keys_str)

            logger.debug(f"Found {len(note_keys)} note keys: {note_keys}")

            for note_key in note_keys:
                articles.append({
                    'id': note_key,
                    'key': note_key,
                    'name': None,  # 個別ページから取得
                    'publishAt': None,  # 個別ページから取得
                    'eyecatch': None
                })

            if articles:
                return articles

        # Next.jsの __NEXT_DATA__ から抽出を試みる
        scripts = soup.find_all('script', {'id': '__NEXT_DATA__'})
        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                props = data.get('props', {}).get('pageProps', {})

                # 記事リストを探す
                user_contents = props.get('userContents', {})
                contents = user_contents.get('contents', [])

                for content in contents:
                    if content.get('type') == 'Note':
                        articles.append({
                            'id': content.get('id'),
                            'key': content.get('key'),
                            'name': content.get('name'),
                            'publishAt': content.get('publishAt'),
                            'eyecatch': content.get('eyecatch')
                        })

                if articles:
                    return articles

            except json.JSONDecodeError as e:
                logger.debug(f"__NEXT_DATA__ parse error: {e}")

        # フォールバック: HTMLから記事リンクを抽出
        article_links = soup.select('a[href*="/n/"]')
        seen_keys = set()

        for link in article_links:
            href = link.get('href', '')
            match = re.search(r'/n/([a-z0-9]+)', href)
            if match:
                key = match.group(1)
                if key not in seen_keys:
                    seen_keys.add(key)
                    title_elem = link.select_one('.note-title, h2, h3')
                    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

                    articles.append({
                        'id': key,
                        'key': key,
                        'name': title,
                        'publishAt': None,
                        'eyecatch': None
                    })

        return articles

    @staticmethod
    def extract_article_body(soup: BeautifulSoup) -> str:
        """記事本文HTMLを抽出"""
        # 優先セレクタ
        selectors = [
            'div.p-article__body',
            'article.note-common-styles__textnote-body',
            'div.note-common-styles__textnote-body',
            'article',
            '[role="article"]'
        ]

        for selector in selectors:
            body = soup.select_one(selector)
            if body:
                return str(body)

        raise ValueError("記事本文が見つかりませんでした")


class HTMLToMarkdownConverter:
    """HTML→Markdown変換"""

    def __init__(self):
        self.h2md = html2text.HTML2Text()
        self.h2md.body_width = 0  # 自動改行無効
        self.h2md.ignore_links = False
        self.h2md.ignore_images = False
        self.h2md.ignore_emphasis = False

    def convert(self, html: str) -> str:
        """HTMLをMarkdownに変換"""
        markdown = self.h2md.handle(html)
        # 余分な空行を削除
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        return markdown.strip()

    def extract_image_urls(self, html: str) -> List[str]:
        """HTML内の画像URLを抽出"""
        soup = BeautifulSoup(html, 'lxml')
        images = []

        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                # 相対URLを絶対URLに変換
                if not src.startswith('http'):
                    src = urljoin('https://note.com', src)
                images.append(src)

        # 背景画像もチェック
        for elem in soup.find_all(style=re.compile(r'background-image')):
            style = elem.get('style', '')
            urls = re.findall(r'url\(["\']?([^"\'()]+)["\']?\)', style)
            for url in urls:
                if not url.startswith('http'):
                    url = urljoin('https://note.com', url)
                images.append(url)

        return list(set(images))  # 重複除去


class ImageDownloader:
    """画像ダウンロードとローカルパス管理"""

    def __init__(self, base_image_dir: Path):
        self.base_image_dir = base_image_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def download_images(self, article_id: str, image_urls: List[str]) -> Dict[str, str]:
        """画像をダウンロードしてURL→ローカルパスのマッピングを返す"""
        article_dir = self.base_image_dir / article_id
        article_dir.mkdir(parents=True, exist_ok=True)

        url_map = {}

        for idx, url in enumerate(image_urls, start=1):
            try:
                # 画像をダウンロード
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # 拡張子を取得
                parsed_url = urlparse(url)
                ext = Path(parsed_url.path).suffix
                if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                    # Content-Typeから推測
                    content_type = response.headers.get('Content-Type', '')
                    ext_map = {
                        'image/jpeg': '.jpg',
                        'image/png': '.png',
                        'image/gif': '.gif',
                        'image/webp': '.webp',
                        'image/svg+xml': '.svg'
                    }
                    ext = ext_map.get(content_type, '.jpg')

                # ファイル名を生成
                filename = f"image_{idx}{ext}"
                filepath = article_dir / filename

                # 保存
                filepath.write_bytes(response.content)

                # 相対パスを生成（articlesフォルダから見た相対パス）
                relative_path = f"../images/{article_id}/{filename}"
                url_map[url] = relative_path

                logger.info(f"  ✓ 画像ダウンロード: {filename}")
                time.sleep(0.5)  # レート制限対策

            except Exception as e:
                logger.warning(f"  ✗ 画像ダウンロード失敗 ({url}): {e}")
                continue

        return url_map

    def replace_image_urls(self, markdown: str, url_map: Dict[str, str]) -> str:
        """Markdown内の画像URLをローカルパスに置換"""
        result = markdown
        for remote_url, local_path in url_map.items():
            # Markdown画像記法
            result = result.replace(f"]({remote_url})", f"]({local_path})")
            result = result.replace(f'="{remote_url}"', f'="{local_path}"')
            # HTML img タグ
            result = result.replace(f'src="{remote_url}"', f'src="{local_path}"')
            result = result.replace(f"src='{remote_url}'", f"src='{local_path}'")

        return result


class MarkdownGenerator:
    """Markdownファイル生成"""

    @staticmethod
    def create_frontmatter(article: ArticleDetail, day_number: int, fetched_at: datetime,
                          date_modified: Optional[str] = None) -> str:
        """YAMLフロントマターを生成"""
        frontmatter = {
            'type': 'article',
            'source': 'note.com',
            'article_id': article.id,
            'day_number': day_number,
            'title': article.title,
            'author': '毛利裕介',
            'publish_date': article.publish_at.strftime('%Y-%m-%d'),
            'publish_datetime': article.publish_at.isoformat(),
            'original_url': article.url,
            'status': 'published',
            'category': 'advent-calendar-2025',
            'tags': ['アドベントカレンダー'],
            'created': datetime.now().strftime('%Y-%m-%d'),
            'fetched_at': fetched_at.isoformat()
        }

        # 更新日時を追加（dateModifiedがあれば）
        if date_modified:
            frontmatter['date_modified'] = date_modified

        return yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)

    @staticmethod
    def parse_frontmatter(filepath: Path) -> Optional[dict]:
        """既存Markdownファイルのフロントマターを解析"""
        try:
            content = filepath.read_text(encoding='utf-8')
            # フロントマターを抽出
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if match:
                frontmatter_str = match.group(1)
                return yaml.safe_load(frontmatter_str)
        except Exception as e:
            logger.debug(f"Frontmatter parse error ({filepath.name}): {e}")
        return None

    @staticmethod
    def generate_filename(day_number: int, title: str, article_id: str) -> str:
        """ファイル名を生成"""
        return f"day{day_number:04d}_{article_id}.md"

    @staticmethod
    def save_article(article: ArticleDetail, day_number: int, markdown_content: str,
                    output_dir: Path, fetched_at: datetime, date_modified: Optional[str] = None):
        """記事ファイルを保存"""
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = MarkdownGenerator.generate_filename(day_number, article.title, article.id)
        filepath = output_dir / filename

        # フロントマター
        frontmatter = MarkdownGenerator.create_frontmatter(
            article, day_number, fetched_at, date_modified
        )

        # フッター
        footer = f"\n\n---\n\n**原文URL**: [{article.url}]({article.url})\n"
        footer += f"**公開日**: {article.publish_at.strftime('%Y年%-m月%-d日')}\n"
        if date_modified:
            # date_modifiedをパースして表示
            try:
                mod_dt = date_parser.parse(date_modified)
                footer += f"**更新日**: {mod_dt.strftime('%Y年%-m月%-d日')}\n"
            except:
                pass
        footer += f"**取得日**: {fetched_at.strftime('%Y年%-m月%-d日')}\n"

        # 完全なMarkdown
        full_content = f"---\n{frontmatter}---\n\n# {article.title}\n\n{markdown_content}{footer}"

        filepath.write_text(full_content, encoding='utf-8')
        logger.info(f"✓ 保存完了: {filename}")


class NoteArticleScraper:
    """メインスクレイパー"""

    def __init__(self, username: str, base_dir: Path, image_dir: Path, output_dir: Path):
        self.username = username
        self.base_dir = base_dir
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        self.parser = ArticleParser()
        self.converter = HTMLToMarkdownConverter()
        self.image_downloader = ImageDownloader(image_dir)

    def fetch_with_retry(self, url: str, max_retries: int = 3) -> requests.Response:
        """リトライ付きHTTPリクエスト"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    raise ValueError(f"ページが見つかりません: {url}")
                elif e.response.status_code == 429:
                    sleep_time = 2 ** attempt
                    logger.warning(f"レート制限中。{sleep_time}秒後にリトライ...")
                    time.sleep(sleep_time)
                else:
                    raise
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"リクエスト失敗 (試行{attempt + 1}回目): {e}")
                time.sleep(1)

        raise ValueError(f"最大リトライ回数を超えました: {url}")

    def fetch_article_list(self) -> List[Article]:
        """記事一覧を取得"""
        profile_url = f"https://note.com/{self.username}"
        logger.info(f"プロフィールページ取得中: {profile_url}")

        response = self.fetch_with_retry(profile_url)
        html = response.text

        articles_data = self.parser.extract_article_list_from_profile(html)

        articles = []
        for data in articles_data:
            try:
                # 日付をパース
                publish_at = None
                if data.get('publishAt'):
                    publish_at = date_parser.parse(data['publishAt'])
                else:
                    publish_at = datetime.now()  # フォールバック

                note_id = data['id']
                # URLを正しく生成
                article_url = f"https://note.com/{self.username}/n/{note_id}"

                article = Article(
                    id=note_id,
                    key=note_id,  # keyは記事ID
                    title=data.get('name', 'Untitled'),
                    publish_at=publish_at,
                    eyecatch_url=data.get('eyecatch'),
                    url=article_url
                )
                articles.append(article)
            except Exception as e:
                logger.warning(f"記事データのパース失敗: {e}")
                continue

        # 公開日順にソート（古い順）
        articles.sort(key=lambda x: x.publish_at)

        # デバッグ: 記事の順序を確認
        if logger.level <= logging.DEBUG:
            logger.debug("記事リストの順序（公開日順）:")
            for i, a in enumerate(articles, 1):
                title_preview = (a.title[:30] if a.title else 'Untitled')
                logger.debug(f"  {i}. {a.id} - {a.publish_at} - {title_preview}")

        logger.info(f"✓ {len(articles)}件の記事を検出")
        return articles

    def scrape_article_detail(self, article: Article) -> ArticleDetail:
        """記事詳細を取得"""
        logger.info(f"\n記事取得中: {article.title if article.title != 'Untitled' else article.id}")
        logger.info(f"  URL: {article.url}")

        response = self.fetch_with_retry(article.url)
        html = response.text
        soup = BeautifulSoup(html, 'lxml')

        # JSON-LDデータを取得
        json_ld = self.parser.extract_json_ld(html)

        # タイトルと公開日をJSON-LDから取得（Noneの場合）
        title = article.title
        publish_at = article.publish_at
        eyecatch_url = article.eyecatch_url

        if json_ld:
            if not title or title == 'Untitled':
                title = json_ld.get('headline', json_ld.get('name', 'Untitled'))
            if not publish_at or publish_at == datetime.now():
                date_str = json_ld.get('datePublished')
                if date_str:
                    try:
                        publish_at = date_parser.parse(date_str)
                    except:
                        pass
            if not eyecatch_url:
                image = json_ld.get('image')
                if image:
                    if isinstance(image, dict):
                        eyecatch_url = image.get('url')
                    elif isinstance(image, list) and len(image) > 0:
                        eyecatch_url = image[0].get('url') if isinstance(image[0], dict) else image[0]
                    elif isinstance(image, str):
                        eyecatch_url = image

        # metaタグからも取得を試みる
        if not title or title == 'Untitled':
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content', 'Untitled')

        # 更新日時を取得（JSON-LDから）
        date_modified = None
        if json_ld:
            date_modified = json_ld.get('dateModified')

        logger.info(f"  タイトル: {title}")
        logger.info(f"  公開日: {publish_at.strftime('%Y-%m-%d') if publish_at else 'Unknown'}")
        if date_modified:
            logger.info(f"  更新日: {date_modified}")

        # 記事本文を取得
        body_html = self.parser.extract_article_body(soup)

        # HTML→Markdown変換
        body_markdown = self.converter.convert(body_html)

        # 画像URLを抽出
        image_urls = self.converter.extract_image_urls(body_html)
        if eyecatch_url:
            image_urls.insert(0, eyecatch_url)

        logger.info(f"  画像: {len(image_urls)}枚検出")

        return ArticleDetail(
            id=article.id,
            key=article.key,
            title=title,
            publish_at=publish_at,
            eyecatch_url=eyecatch_url,
            url=article.url,
            body_html=body_html,
            body_markdown=body_markdown,
            image_urls=image_urls,
            json_ld=json_ld,
            date_modified=date_modified
        )

    def load_local_articles(self) -> Dict[str, dict]:
        """ローカルの既存記事情報を読み込む（article_id -> frontmatter）"""
        local_articles = {}

        if not self.output_dir.exists():
            return local_articles

        for filepath in self.output_dir.glob('*.md'):
            frontmatter = MarkdownGenerator.parse_frontmatter(filepath)
            if frontmatter and 'article_id' in frontmatter:
                local_articles[frontmatter['article_id']] = {
                    'frontmatter': frontmatter,
                    'filepath': filepath
                }

        return local_articles

    def run(self, max_articles: Optional[int] = None, start_day: int = 1,
            skip_existing: bool = False, update_check: bool = False):
        """メイン実行"""
        fetched_at = datetime.now()

        logger.info("=" * 60)
        logger.info("note.com記事取得スクリプト")
        logger.info("=" * 60)

        # ローカル記事を読み込む（day_number決定のため常に必要）
        local_articles = self.load_local_articles()
        if update_check:
            logger.info("更新チェックモード: ローカルファイルを確認中...")
            logger.info(f"✓ {len(local_articles)}件のローカル記事を検出\n")
        elif local_articles:
            logger.debug(f"既存ローカル記事: {len(local_articles)}件検出")

        # 記事一覧を取得
        articles = self.fetch_article_list()

        if max_articles:
            articles = articles[:max_articles]

        logger.info(f"\n{len(articles)}件の記事を処理します\n")

        # 統計
        stats = {'new': 0, 'updated': 0, 'skipped': 0}

        # 既存記事の最大day_numberを取得
        max_existing_day = 0
        if local_articles:
            for info in local_articles.values():
                day_num = info['frontmatter'].get('day_number', 0)
                if day_num > max_existing_day:
                    max_existing_day = day_num
            logger.debug(f"既存記事の最大day番号: {max_existing_day}")

        # 新規記事を特定し、date_modified順でソートしてday_numberを事前に割り当てる
        # まず各新規記事のdate_modifiedを取得する必要がある
        new_articles_with_date = []
        for article in articles:
            if article.id not in local_articles:
                # 記事ページからdate_modifiedを取得
                logger.info(f"新規記事のメタデータ取得中: {article.id}")
                try:
                    response = self.fetch_with_retry(article.url)
                    html = response.text
                    json_ld = self.parser.extract_json_ld(html)
                    date_modified = json_ld.get('dateModified') if json_ld else None
                    new_articles_with_date.append({
                        'article': article,
                        'date_modified': date_modified
                    })
                    logger.debug(f"  {article.id}: date_modified = {date_modified}")
                except Exception as e:
                    logger.warning(f"  メタデータ取得失敗 ({article.id}): {e}")
                    new_articles_with_date.append({
                        'article': article,
                        'date_modified': None
                    })

        # 新規記事をdate_modified昇順でソート（Noneは最後に）
        new_articles_with_date.sort(key=lambda x: x['date_modified'] or '9999-99-99')

        # 新規記事にday_numberを事前割り当て（article_id -> day_number）
        new_article_day_map = {}
        next_day = max_existing_day + 1 if max_existing_day > 0 else start_day
        for item in new_articles_with_date:
            new_article = item['article']
            new_article_day_map[new_article.id] = next_day
            logger.debug(f"  🆕 新規記事 {new_article.id} (date_modified: {item['date_modified']}) → day{next_day:04d} に事前割り当て")
            next_day += 1

        # 各記事を処理
        for idx, article in enumerate(articles, start=start_day):
            try:
                # 既存ファイルチェック
                if skip_existing:
                    filename = MarkdownGenerator.generate_filename(idx, article.title, article.id)
                    if (self.output_dir / filename).exists():
                        logger.info(f"スキップ (既存): {article.title}")
                        stats['skipped'] += 1
                        continue

                # 更新チェックモード
                should_fetch = True
                if update_check and article.id in local_articles:
                    # まず記事ページにアクセスしてdateModifiedを確認
                    logger.info(f"\n更新チェック中: {article.id}")
                    logger.info(f"  ⚡ 軽量チェック: メタデータのみ取得（本文・画像はスキップ）")
                    response = self.fetch_with_retry(article.url)
                    html = response.text
                    json_ld = self.parser.extract_json_ld(html)

                    web_date_modified = json_ld.get('dateModified') if json_ld else None
                    local_date_modified = local_articles[article.id]['frontmatter'].get('date_modified')

                    if web_date_modified and local_date_modified:
                        if web_date_modified == local_date_modified:
                            logger.info(f"  ✓ 更新なし: {web_date_modified}")
                            logger.info(f"  💾 スキップ（本文・画像のダウンロードを回避）")
                            stats['skipped'] += 1
                            should_fetch = False
                        else:
                            logger.info(f"  🔄 更新検出: {local_date_modified} → {web_date_modified}")
                            logger.info(f"  📥 再取得を開始...")
                            stats['updated'] += 1
                    else:
                        # dateModifiedがない場合は取得
                        logger.info(f"  ⚠ 更新日時情報なし - 再取得します")
                        stats['updated'] += 1

                if not should_fetch:
                    continue

                # day番号の決定
                if article.id in local_articles:
                    # 既存記事: ローカルのday番号を保持
                    day_number = local_articles[article.id]['frontmatter'].get('day_number', idx)
                    logger.debug(f"  🔄 既存記事の day{day_number:04d} を保持")
                elif article.id in new_article_day_map:
                    # 新規記事: 事前割り当てマップから取得
                    day_number = new_article_day_map[article.id]
                    stats['new'] += 1
                    logger.debug(f"  🆕 新規記事として day{day_number:04d} に割り当て")
                else:
                    # フォールバック: enumerateのidxを使用
                    day_number = idx
                    stats['new'] += 1

                # 記事詳細を取得
                detail = self.scrape_article_detail(article)

                # 画像をダウンロード
                if detail.image_urls:
                    logger.info(f"  画像ダウンロード中...")
                    url_map = self.image_downloader.download_images(detail.id, detail.image_urls)

                    # MarkdownのURLを置換
                    detail.body_markdown = self.image_downloader.replace_image_urls(
                        detail.body_markdown, url_map
                    )

                # Markdownファイルを保存
                MarkdownGenerator.save_article(
                    detail, day_number, detail.body_markdown, self.output_dir, fetched_at,
                    date_modified=detail.date_modified
                )

                time.sleep(2)  # レート制限対策

            except Exception as e:
                logger.error(f"✗ エラー ({article.title}): {e}")
                continue

        # 処理時間を計算
        elapsed_time = datetime.now() - fetched_at

        logger.info("\n" + "=" * 60)
        logger.info("完了！")
        logger.info("=" * 60)
        logger.info(f"出力先: {self.output_dir}")
        logger.info(f"画像: {self.image_dir}")
        logger.info(f"処理時間: {elapsed_time.total_seconds():.1f}秒")

        if update_check:
            logger.info(f"\n📊 更新チェックモード統計:")
            logger.info(f"  🆕 新規記事: {stats['new']}件")
            logger.info(f"  🔄 更新された記事: {stats['updated']}件")
            logger.info(f"  ⏭️  スキップ: {stats['skipped']}件")

            if stats['skipped'] > 0:
                logger.info(f"\n💡 効率化:")
                logger.info(f"  {stats['skipped']}件の記事で本文・画像のダウンロードを回避")
                logger.info(f"  推定データ削減: ~{stats['skipped'] * 100}KB（画像分）")
        else:
            total_articles = stats.get('new', 0) + stats.get('updated', 0) + stats.get('skipped', 0)
            if total_articles > 0:
                logger.info(f"\n📊 処理統計: {total_articles}件の記事を取得")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='note.com記事取得スクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--username',
        default='yusukemori_ravi',
        help='note.comユーザー名 (デフォルト: yusukemori_ravi)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('./articles'),
        help='Markdown出力先ディレクトリ (デフォルト: ./articles)'
    )
    parser.add_argument(
        '--image-dir',
        type=Path,
        default=Path('./images'),
        help='画像保存先ディレクトリ (デフォルト: ./images)'
    )
    parser.add_argument(
        '--max-articles',
        type=int,
        default=None,
        help='取得する最大記事数'
    )
    parser.add_argument(
        '--start-day',
        type=int,
        default=1,
        help='開始日番号 (デフォルト: 1)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='既存ファイルをスキップ'
    )
    parser.add_argument(
        '--update-check',
        action='store_true',
        help='更新チェックモード: ローカルファイルとWeb側のdateModifiedを比較し、更新された記事のみ取得'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細ログを表示'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # スクレイパーを実行
    scraper = NoteArticleScraper(
        username=args.username,
        base_dir=Path.cwd(),
        image_dir=args.image_dir,
        output_dir=args.output_dir
    )

    scraper.run(
        max_articles=args.max_articles,
        start_day=args.start_day,
        skip_existing=args.skip_existing,
        update_check=args.update_check
    )


if __name__ == '__main__':
    main()
