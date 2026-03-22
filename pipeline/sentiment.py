"""감성 분석 모듈

1차: KR-FinBERT (snunlp/KR-FinBert-SC) - GPU/고성능 환경
2차: 키워드 기반 감성 분석 - GitHub Actions 경량화용 폴백
"""
from config import FINBERT_MODEL, SENTIMENT_DICT_DIR, USE_FINBERT


def load_sentiment_dict() -> tuple[set[str], set[str]]:
    """감성 사전 로드"""
    pos_path = SENTIMENT_DICT_DIR / "positive_words.txt"
    neg_path = SENTIMENT_DICT_DIR / "negative_words.txt"

    positive = set()
    negative = set()

    if pos_path.exists():
        positive = {
            w.strip() for w in pos_path.read_text(encoding="utf-8").splitlines() if w.strip()
        }
    if neg_path.exists():
        negative = {
            w.strip() for w in neg_path.read_text(encoding="utf-8").splitlines() if w.strip()
        }

    return positive, negative


# 모듈 레벨에서 사전 로드
_positive_words, _negative_words = load_sentiment_dict()


def keyword_sentiment(text: str) -> float:
    """키워드 기반 감성 점수 (-1 ~ +1)"""
    if not text:
        return 0.0

    pos_count = sum(1 for w in _positive_words if w in text)
    neg_count = sum(1 for w in _negative_words if w in text)
    total = pos_count + neg_count

    if total == 0:
        return 0.0

    return (pos_count - neg_count) / total


def finbert_sentiment(text: str) -> float:
    """KR-FinBERT 기반 감성 점수 (-1 ~ +1)"""
    try:
        from transformers import pipeline as hf_pipeline
    except ImportError:
        print("  transformers 미설치 → 키워드 폴백 사용")
        return keyword_sentiment(text)

    try:
        classifier = _get_finbert_pipeline()
        # 텍스트 길이 제한 (모델 최대 512 토큰)
        text = text[:500]
        result = classifier(text)[0]
        label = result["label"]
        score = result["score"]

        # 레이블에 따른 점수 변환
        if label in ("positive", "긍정"):
            return score
        elif label in ("negative", "부정"):
            return -score
        else:
            return 0.0
    except Exception as e:
        print(f"  FinBERT 오류 → 키워드 폴백: {e}")
        return keyword_sentiment(text)


_finbert_pipeline = None


def _get_finbert_pipeline():
    """FinBERT 파이프라인 싱글톤"""
    global _finbert_pipeline
    if _finbert_pipeline is None:
        from transformers import pipeline as hf_pipeline
        _finbert_pipeline = hf_pipeline(
            "sentiment-analysis",
            model=FINBERT_MODEL,
            tokenizer=FINBERT_MODEL,
        )
    return _finbert_pipeline


def analyze_sentiment(text: str, use_finbert: bool | None = None) -> float:
    """텍스트 감성 분석 (-1 ~ +1)

    Args:
        text: 분석할 텍스트
        use_finbert: None이면 config 설정 따름
    """
    if use_finbert is None:
        use_finbert = USE_FINBERT

    if use_finbert:
        return finbert_sentiment(text)
    return keyword_sentiment(text)


def analyze_articles(articles: list[dict], use_finbert: bool | None = None) -> dict:
    """뉴스 기사 목록의 감성 분석 결과를 반환

    Returns:
        {
            "avg_sentiment": float,  # 평균 감성 점수
            "positive_ratio": float,  # 긍정 기사 비율
            "negative_ratio": float,  # 부정 기사 비율
            "neutral_ratio": float,  # 중립 기사 비율
            "article_count": int,
            "sentiments": [float, ...]  # 개별 점수
        }
    """
    if not articles:
        return {
            "avg_sentiment": 0.0,
            "positive_ratio": 0.0,
            "negative_ratio": 0.0,
            "neutral_ratio": 1.0,
            "article_count": 0,
            "sentiments": [],
        }

    sentiments = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        score = analyze_sentiment(text, use_finbert)
        sentiments.append(score)

    positive = sum(1 for s in sentiments if s > 0.1)
    negative = sum(1 for s in sentiments if s < -0.1)
    neutral = len(sentiments) - positive - negative

    total = len(sentiments)
    return {
        "avg_sentiment": round(sum(sentiments) / total, 4),
        "positive_ratio": round(positive / total, 4),
        "negative_ratio": round(negative / total, 4),
        "neutral_ratio": round(neutral / total, 4),
        "article_count": total,
        "sentiments": [round(s, 4) for s in sentiments],
    }


if __name__ == "__main__":
    # 테스트
    test_texts = [
        "코스피가 외국인 매수세에 힘입어 강세 반등에 성공했다",
        "미중 갈등 우려에 코스피 급락, 투자 심리 위축",
        "코스피 소폭 상승 마감, 관망세 지속",
    ]
    print("=== 키워드 기반 감성 분석 테스트 ===")
    for text in test_texts:
        score = keyword_sentiment(text)
        label = "긍정" if score > 0.1 else "부정" if score < -0.1 else "중립"
        print(f"  [{label}] {score:+.3f} | {text}")
