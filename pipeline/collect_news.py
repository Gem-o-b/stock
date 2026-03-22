"""네이버 금융 뉴스 크롤링 모듈"""
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import KST, NEWS_MAX_ARTICLES, NEWS_SEARCH_QUERIES

NAVER_NEWS_URL = "https://search.naver.com/search.naver"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def clean_text(text: str) -> str:
    """HTML 태그 제거 및 텍스트 정리"""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_naver_news(query: str, display: int = 10) -> list[dict]:
    """네이버 뉴스 검색 결과 크롤링"""
    articles = []
    params = {
        "where": "news",
        "query": query,
        "sort": "1",  # 최신순
        "sm": "tab_smr",
        "nso": "so:dd,p:1d",  # 최근 1일
    }

    try:
        resp = requests.get(NAVER_NEWS_URL, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        news_items = soup.select("div.news_area")
        for item in news_items[:display]:
            title_tag = item.select_one("a.news_tit")
            desc_tag = item.select_one("div.news_dsc")
            press_tag = item.select_one("a.info.press")

            if title_tag:
                title = clean_text(title_tag.get_text())
                description = clean_text(desc_tag.get_text()) if desc_tag else ""
                press = clean_text(press_tag.get_text()) if press_tag else ""
                url = title_tag.get("href", "")

                articles.append({
                    "title": title,
                    "description": description,
                    "press": press,
                    "url": url,
                    "query": query,
                })
    except Exception as e:
        print(f"  경고: '{query}' 뉴스 수집 실패: {e}")

    return articles


def collect_news() -> list[dict]:
    """모든 검색어에 대한 뉴스를 수집"""
    print("뉴스 크롤링 시작...")
    all_articles = []
    seen_titles = set()

    for query in NEWS_SEARCH_QUERIES:
        print(f"  검색어: '{query}'")
        articles = fetch_naver_news(query, display=NEWS_MAX_ARTICLES // len(NEWS_SEARCH_QUERIES))

        for article in articles:
            if article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                all_articles.append(article)

        time.sleep(0.5)  # 요청 간격

    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    print(f"수집 완료: {len(all_articles)}건 ({now})")
    return all_articles


if __name__ == "__main__":
    articles = collect_news()
    for i, a in enumerate(articles, 1):
        print(f"{i}. [{a['press']}] {a['title']}")
