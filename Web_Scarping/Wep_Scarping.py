import requests
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass, asdict
from typing import List, Optional
import concurrent.futures
import re

@dataclass
class Article:
    url: str
    postid: str
    title: str
    keywords: List[str]
    thumbnail: Optional[str]
    published_time: str
    last_updated: str
    author: str
    word_count: int
    video_duration: Optional[str]
    lang: str
    description: str
    classes: List[dict]
    full_text: str

class ArticleScraper:
    def __init__(self):
        self.session = requests.Session()

    def fetch_article(self, url: str, article_limit_reached: List[bool]) -> Optional[Article]:
        if article_limit_reached[0]:
            return None

        print(f"Scraping: {url}...")
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        if "video" in url or "image" in url:
            print(f"Skipped non-article content: {url}")
            return None

        script_tag = soup.find('script', type='text/tawsiyat')
        metadata = json.loads(script_tag.string) if script_tag else {}

        postid = self.extract_post_id(metadata, url)

        title = metadata.get('title') or 'Default Title'
        keywords = [k.strip() for k in metadata.get('keywords', '').split(',')] if metadata.get('keywords') else ['Default Keyword']
        thumbnail = metadata.get('thumbnail') or 'Default Thumbnail'
        published_time = metadata.get('publication_date') or self.extract_date_from_html(soup, 'published_time') or '2024-01-01T00:00:00Z'
        last_updated = metadata.get('last_updated_date') or self.extract_date_from_html(soup, 'last_updated') or published_time
        author = metadata.get('author') or 'Default Author'
        word_count = int(metadata.get('word_count') or len(self.extract_full_text(soup).split()))
        video_duration = None
        lang = metadata.get('language') or self.detect_language(soup) or 'en'
        description = metadata.get('description') or 'Default Description'
        classes = metadata.get('classes') or [{'class_name': 'Default Class'}]
        full_text = self.extract_full_text(soup) or 'Default Full Text'

        print(f"Finished: {url}")

        return Article(
            url=url,
            postid=postid,
            title=title,
            keywords=keywords,
            thumbnail=thumbnail,
            published_time=published_time,
            last_updated=last_updated,
            author=author,
            word_count=word_count,
            video_duration=video_duration,
            lang=lang,
            description=description,
            classes=classes,
            full_text=full_text
        )

    def extract_post_id(self, metadata: dict, url: str) -> str:
        postid = metadata.get('postid')
        if postid:
            return str(postid)

        match = re.search(r'/(\d+)\.html$', url)
        if match:
            return match.group(1)

        match = re.search(r'-p(\d+)$', url)
        if match:
            return match.group(1)

        return "0000"

    def extract_date_from_html(self, soup: BeautifulSoup, date_type: str) -> Optional[str]:
        if date_type == 'published_time':
            date_tag = soup.find('meta', {'property': 'article:published_time'})
        elif date_type == 'last_updated':
            date_tag = soup.find('meta', {'property': 'article:modified_time'})
        return date_tag['content'] if date_tag else None

    def detect_language(self, soup: BeautifulSoup) -> Optional[str]:
        lang_tag = soup.find('html')
        return lang_tag.get('lang') if lang_tag else None

    def extract_full_text(self, soup: BeautifulSoup) -> Optional[str]:
        paragraphs = [p.get_text() for p in soup.find_all('p')]
        return '\n'.join(paragraphs) if paragraphs else None

    def parse_sitemap(self, sitemap_url: str) -> List[str]:
        response = self.session.get(sitemap_url)
        soup = BeautifulSoup(response.content, 'xml')
        urls = [loc.get_text() for loc in soup.find_all('loc')]
        return urls

class FileUtility:
    @staticmethod
    def save_articles(articles: List[Article], year: int, month: int):
        filename = f"articles_{year}_{month:02d}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            articles_dict = [asdict(article) for article in articles]
            json.dump(articles_dict, f, ensure_ascii=False, indent=4)

def main(year: int, article_limit: int):
    article_scraper = ArticleScraper()
    total_articles = 0
    article_limit_reached = [False]

    # Parse the main sitemap to get all the month links
    main_sitemap_url = "https://www.almayadeen.net/sitemaps/all.xml"
    monthly_sitemaps = article_scraper.parse_sitemap(main_sitemap_url)

    # Filter the sitemaps to only include those from the specified year
    relevant_sitemaps = [
        sitemap for sitemap in monthly_sitemaps
        if int(sitemap.split('-')[-2]) == year
    ]

    for sitemap_url in relevant_sitemaps:
        if total_articles >= article_limit:
            print(f"Article limit of {article_limit} reached. Stopping scraping.")
            break

        month = int(sitemap_url.split('-')[-1].replace('.xml', ''))

        article_urls = article_scraper.parse_sitemap(sitemap_url)
        print(f"Found {len(article_urls)} article URLs for {year}-{month:02d}. Starting to scrape...")

        all_articles = []  # Initialize a fresh list for each month

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(article_scraper.fetch_article, url, article_limit_reached): url for url in article_urls}
            for future in concurrent.futures.as_completed(future_to_url):
                if article_limit_reached[0]:
                    break
                try:
                    article = future.result()
                    if article:
                        all_articles.append(article)
                        total_articles += 1
                        if total_articles >= article_limit:
                            print(f"Article limit of {article_limit} reached. Stopping scraping.")
                            article_limit_reached[0] = True
                            break
                except Exception as e:
                    print(f"Error fetching article from {future_to_url[future]}: {e}")

        if all_articles:
            FileUtility.save_articles(all_articles, year, month)
            print(f"Scraping complete for {year}-{month:02d}. {len(all_articles)} articles saved.")

        if article_limit_reached[0]:
            break

    print(f"Total {total_articles} articles scraped and saved.")

if __name__ == "__main__":
    year = 2024  # Set the year to scrape
    article_limit = 10000  # Set the total number of articles to scrape
    main(year, article_limit)
