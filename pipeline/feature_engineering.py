"""피처 엔지니어링 모듈 - 30개 기술적 지표 생성

기술적 지표 15개:
  - 수익률(1일, 5일, 20일), 이동평균(5일, 20일, 60일),
  - RSI(14), MACD, MACD Signal, 볼린저밴드(상/하), 변동성(5일, 20일),
  - 거래량 변화율, 거래대금 변화율

글로벌 시장 8개:
  - S&P500 수익률, NASDAQ 수익률, VIX, VIX 변화, 환율, 환율 변화, WTI 수익률, 금 수익률

뉴스 감성 4개:
  - 평균 감성점수, 긍정 비율, 부정 비율, 기사 수

캘린더 3개:
  - 요일, 월, 월말 여부
"""
import numpy as np
import pandas as pd


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """기술적 지표 15개 추가"""
    close = df["kospi_close"]
    high = df["kospi_high"]
    low = df["kospi_low"]
    volume = df["kospi_volume"]

    # 수익률
    df["return_1d"] = close.pct_change(1)
    df["return_5d"] = close.pct_change(5)
    df["return_20d"] = close.pct_change(20)

    # 이동평균 대비
    df["ma5_ratio"] = close / close.rolling(5).mean() - 1
    df["ma20_ratio"] = close / close.rolling(20).mean() - 1
    df["ma60_ratio"] = close / close.rolling(60).mean() - 1

    # RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    # 볼린저 밴드 (20일)
    ma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    df["bb_upper"] = (close - (ma20 + 2 * std20)) / close  # 상단 대비 위치
    df["bb_lower"] = (close - (ma20 - 2 * std20)) / close  # 하단 대비 위치

    # 변동성
    df["volatility_5d"] = close.pct_change().rolling(5).std()
    df["volatility_20d"] = close.pct_change().rolling(20).std()

    # 거래량 변화율
    df["volume_change"] = volume.pct_change(1)

    # 거래대금 변화율 (있는 경우)
    if "kospi_trading_value" in df.columns:
        df["trading_value_change"] = df["kospi_trading_value"].pct_change(1)
    else:
        df["trading_value_change"] = 0.0

    return df


def add_global_features(df: pd.DataFrame) -> pd.DataFrame:
    """글로벌 시장 피처 8개 추가"""
    # S&P500 수익률
    if "sp500" in df.columns:
        df["sp500_return"] = df["sp500"].pct_change(1)
    else:
        df["sp500_return"] = 0.0

    # NASDAQ 수익률
    if "nasdaq" in df.columns:
        df["nasdaq_return"] = df["nasdaq"].pct_change(1)
    else:
        df["nasdaq_return"] = 0.0

    # VIX
    if "vix" in df.columns:
        df["vix_level"] = df["vix"]
        df["vix_change"] = df["vix"].pct_change(1)
    else:
        df["vix_level"] = 0.0
        df["vix_change"] = 0.0

    # 환율
    if "usdkrw" in df.columns:
        df["usdkrw_level"] = df["usdkrw"]
        df["usdkrw_change"] = df["usdkrw"].pct_change(1)
    else:
        df["usdkrw_level"] = 0.0
        df["usdkrw_change"] = 0.0

    # WTI 수익률
    if "wti" in df.columns:
        df["wti_return"] = df["wti"].pct_change(1)
    else:
        df["wti_return"] = 0.0

    # 금 수익률
    if "gold" in df.columns:
        df["gold_return"] = df["gold"].pct_change(1)
    else:
        df["gold_return"] = 0.0

    return df


def add_sentiment_features(df: pd.DataFrame, sentiment_data: dict | None = None) -> pd.DataFrame:
    """뉴스 감성 피처 4개 추가"""
    if sentiment_data:
        df["news_sentiment"] = sentiment_data.get("avg_sentiment", 0.0)
        df["news_positive_ratio"] = sentiment_data.get("positive_ratio", 0.0)
        df["news_negative_ratio"] = sentiment_data.get("negative_ratio", 0.0)
        df["news_article_count"] = sentiment_data.get("article_count", 0)
    else:
        df["news_sentiment"] = 0.0
        df["news_positive_ratio"] = 0.0
        df["news_negative_ratio"] = 0.0
        df["news_article_count"] = 0

    return df


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """캘린더 피처 3개 추가"""
    df["day_of_week"] = df.index.dayofweek  # 0=월 ~ 4=금
    df["month"] = df.index.month
    df["is_month_end"] = df.index.is_month_end.astype(int)
    return df


def add_target(df: pd.DataFrame) -> pd.DataFrame:
    """타겟 변수 생성: 다음날 종가 > 오늘 종가 → 1 (LONG), 아니면 0 (SHORT)"""
    df["target"] = (df["kospi_close"].shift(-1) > df["kospi_close"]).astype(int)
    return df


# 학습에 사용할 피처 목록
FEATURE_COLUMNS = [
    # 기술적 지표 (15)
    "return_1d", "return_5d", "return_20d",
    "ma5_ratio", "ma20_ratio", "ma60_ratio",
    "rsi_14", "macd", "macd_signal",
    "bb_upper", "bb_lower",
    "volatility_5d", "volatility_20d",
    "volume_change", "trading_value_change",
    # 글로벌 시장 (8)
    "sp500_return", "nasdaq_return",
    "vix_level", "vix_change",
    "usdkrw_level", "usdkrw_change",
    "wti_return", "gold_return",
    # 뉴스 감성 (4)
    "news_sentiment", "news_positive_ratio",
    "news_negative_ratio", "news_article_count",
    # 캘린더 (3)
    "day_of_week", "month", "is_month_end",
]


def build_features(
    market_df: pd.DataFrame,
    sentiment_data: dict | None = None,
    include_target: bool = True,
) -> pd.DataFrame:
    """전체 피처 생성 파이프라인

    Args:
        market_df: 시장 데이터 DataFrame
        sentiment_data: 감성 분석 결과 dict
        include_target: 타겟 변수 포함 여부 (예측 시 False)

    Returns:
        피처 DataFrame
    """
    df = market_df.copy()

    df = add_technical_indicators(df)
    df = add_global_features(df)
    df = add_sentiment_features(df, sentiment_data)
    df = add_calendar_features(df)

    if include_target:
        df = add_target(df)

    # 무한대 → NaN 변환 후 결측 제거
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=FEATURE_COLUMNS)

    if include_target:
        df = df.dropna(subset=["target"])

    print(f"피처 생성 완료: {len(df)}행, 피처 {len(FEATURE_COLUMNS)}개")
    return df


if __name__ == "__main__":
    # 테스트: 더미 데이터로 피처 생성
    from collect_market_data import collect_all

    market_df = collect_all()
    featured_df = build_features(market_df)
    print(f"\n피처 컬럼: {FEATURE_COLUMNS}")
    print(f"\n최근 5일:")
    print(featured_df[FEATURE_COLUMNS].tail())
