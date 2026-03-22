"""전역 설정"""
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 경로
ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT_DIR / "pipeline"
DATA_DIR = ROOT_DIR / "data"
WEB_PUBLIC_DATA_DIR = ROOT_DIR / "web" / "public" / "data"
MODELS_DIR = PIPELINE_DIR / "models"
SENTIMENT_DICT_DIR = PIPELINE_DIR / "sentiment_dict"

# 데이터 파일 경로
PREDICTIONS_FILE = DATA_DIR / "predictions" / "predictions.json"
ACCURACY_FILE = DATA_DIR / "accuracy" / "accuracy.json"
MARKET_FILE = DATA_DIR / "market" / "latest_market.json"

# 한국 시간대
KST = timezone(timedelta(hours=9))

# 데이터 수집 설정
KOSPI_TICKER = "KS11"
DATA_LOOKBACK_DAYS = 365 * 3  # 3년치 데이터

# 글로벌 티커
GLOBAL_TICKERS = {
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "VIX": "^VIX",
    "WTI": "CL=F",
    "GOLD": "GC=F",
    "DXY": "DX-Y.NYB",
}

# 환율
USD_KRW_TICKER = "USD/KRW"

# 뉴스 설정
NEWS_SEARCH_QUERIES = ["코스피", "증시", "주식시장"]
NEWS_MAX_ARTICLES = 30

# 모델 설정
MODEL_FILE = MODELS_DIR / "lgbm_model.pkl"
FEATURE_IMPORTANCE_FILE = MODELS_DIR / "feature_importance.json"
TARGET_COL = "target"  # 1 = LONG (상승), 0 = SHORT (하락)
TEST_SIZE = 0.2
CV_SPLITS = 5

# LightGBM 하이퍼파라미터
LGBM_PARAMS = {
    "objective": "binary",
    "metric": "binary_logloss",
    "boosting_type": "gbdt",
    "num_leaves": 31,
    "learning_rate": 0.05,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "n_estimators": 300,
    "verbose": -1,
    "random_state": 42,
}

# 감성 분석 설정
FINBERT_MODEL = "snunlp/KR-FinBert-SC"
USE_FINBERT = True  # False면 키워드 폴백만 사용

def today_kst() -> str:
    """오늘 날짜(KST)를 YYYY-MM-DD 형식으로 반환"""
    return datetime.now(KST).strftime("%Y-%m-%d")

def ensure_dirs():
    """필요한 디렉토리 생성"""
    for d in [
        DATA_DIR / "predictions",
        DATA_DIR / "accuracy",
        DATA_DIR / "market",
        MODELS_DIR,
        WEB_PUBLIC_DATA_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
