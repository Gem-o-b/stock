"""네이버 금융 뉴스 크롤링 모듈

네이버 뉴스 > 경제 > 증권 섹션에서 최신 기사를 수집합니다.
"""
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import KST, NEWS_MAX_ARTICLES

# 네이버 뉴스 증권 섹션
NAVER_STOCK_NEWS_URL = "https://news.naver.com/breakingnews/section/101/258"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def clean_text(text: str) -> str:
    """HTML 태그 제거 및 텍스트 정리"""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_stock_news(max_articles: int = 30) -> list[dict]:
    """네이버 증권 뉴스 섹션에서 최신 기사 수집"""
    articles = []

    try:
        resp = requests.get(NAVER_STOCK_NEWS_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("li.sa_item")
        for item in items[:max_articles]:
            title_tag = item.select_one("a.sa_text_title")
            lede_tag = item.select_one("div.sa_text_lede")
            press_tag = item.select_one("div.sa_text_press")

            if title_tag:
                title = clean_text(title_tag.get_text())
                description = clean_text(lede_tag.get_text()) if lede_tag else ""
                press = clean_text(press_tag.get_text()) if press_tag else ""
                url = title_tag.get("href", "")

                articles.append({
                    "title": title,
                    "description": description,
                    "press": press,
                    "url": url,
                })
    except Exception as e:
        print(f"  경고: 증권 뉴스 수집 실패: {e}")

    return articles


def collect_news() -> list[dict]:
    """증권 뉴스 수집 메인 함수"""
    print("뉴스 크롤링 시작...")
    articles = fetch_stock_news(max_articles=NEWS_MAX_ARTICLES)

    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    print(f"수집 완료: {len(articles)}건 ({now})")
    return articles


if __name__ == "__main__":
    articles = collect_news()
    for i, a in enumerate(articles, 1):
        print(f"{i}. [{a['press']}] {a['title']}")
