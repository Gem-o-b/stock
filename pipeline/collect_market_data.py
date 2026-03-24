"""시장 데이터 수집 모듈

FinanceDataReader: KOSPI, 환율
yfinance: S&P500, NASDAQ, VIX, WTI, 금, 달러인덱스
"""
import json
from datetime import datetime, timedelta

import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf

from config import (
    DATA_DIR,
    DATA_LOOKBACK_DAYS,
    GLOBAL_TICKERS,
    KOSPI_TICKER,
    KST,
    MARKET_FILE,
    USD_KRW_TICKER,
    WEB_PUBLIC_DATA_DIR,
    ensure_dirs,
    today_kst,
)


def get_date_range() -> tuple[str, str]:
    """데이터 수집 기간 반환"""
    end = datetime.now(KST)
    start = end - timedelta(days=DATA_LOOKBACK_DAYS)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def collect_kospi(start: str, end: str) -> pd.DataFrame:
    """KOSPI 지수 데이터 수집 (FinanceDataReader)"""
    print("[1/3] KOSPI 지수 수집 중...")
    df = fdr.DataReader(KOSPI_TICKER, start, end)
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={
        "Open": "kospi_open",
        "High": "kospi_high",
        "Low": "kospi_low",
        "Close": "kospi_close",
        "Volume": "kospi_volume",
    })
    # Change 컬럼이 있으면 제거
    df = df[["kospi_open", "kospi_high", "kospi_low", "kospi_close", "kospi_volume"]]
    return df


def collect_usdkrw(start: str, end: str) -> pd.DataFrame:
    """USD/KRW 환율 수집"""
    print("[2/3] USD/KRW 환율 수집 중...")
    df = fdr.DataReader(USD_KRW_TICKER, start, end)
    df.index = pd.to_datetime(df.index)
    df = df[["Close"]].rename(columns={"Close": "usdkrw"})
    return df


def collect_global_markets(start: str, end: str) -> pd.DataFrame:
    """글로벌 시장 데이터 수집 (yfinance)"""
    print("[3/3] 글로벌 시장 데이터 수집 중...")
    frames = {}
    for name, ticker in GLOBAL_TICKERS.items():
        try:
            data = yf.download(ticker, start=start, end=end, progress=False)
            if not data.empty:
                # yfinance MultiIndex 처리
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                frames[name.lower()] = data["Close"]
        except Exception as e:
            print(f"  경고: {name}({ticker}) 수집 실패: {e}")

    if frames:
        df = pd.DataFrame(frames)
        df.index = pd.to_datetime(df.index)
        return df
    return pd.DataFrame()


def collect_all() -> pd.DataFrame:
    """모든 시장 데이터를 수집하여 하나의 DataFrame으로 병합"""
    ensure_dirs()
    start, end = get_date_range()
    print(f"데이터 수집 기간: {start} ~ {end}")

    kospi = collect_kospi(start, end)
    usdkrw = collect_usdkrw(start, end)
    global_markets = collect_global_markets(start, end)

    # 날짜 기준 병합
    df = kospi.copy()
    for other in [usdkrw, global_markets]:
        if not other.empty:
            df = df.join(other, how="left")

    # 결측 처리: 전일값으로 채움
    df = df.ffill()
    df = df.dropna()

    print(f"최종 데이터: {len(df)}행, {len(df.columns)}열")
    print(f"컬럼: {list(df.columns)}")

    return df


def save_latest_market_data(df: pd.DataFrame):
    """최신 시장 데이터를 JSON으로 저장"""
    if df.empty:
        return

    latest = df.iloc[-1]
    market_data = {
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "kospi_close": round(float(latest.get("kospi_close", 0)), 2),
        "kospi_open": round(float(latest.get("kospi_open", 0)), 2),
        "kospi_high": round(float(latest.get("kospi_high", 0)), 2),
        "kospi_low": round(float(latest.get("kospi_low", 0)), 2),
        "kospi_volume": int(latest.get("kospi_volume", 0)),
        "usdkrw": round(float(latest.get("usdkrw", 0)), 2),
        "sp500": round(float(latest.get("sp500", 0)), 2),
        "nasdaq": round(float(latest.get("nasdaq", 0)), 2),
        "vix": round(float(latest.get("vix", 0)), 2),
        "wti": round(float(latest.get("wti", 0)), 2),
        "gold": round(float(latest.get("gold", 0)), 2),
        "dxy": round(float(latest.get("dxy", 0)), 2),
    }

    # 최근 30일 캔들스틱 데이터
    candles = []
    for idx, row in df.tail(60).iterrows():
        candles.append({
            "time": idx.strftime("%Y-%m-%d"),
            "open": round(float(row.get("kospi_open", 0)), 2),
            "high": round(float(row.get("kospi_high", 0)), 2),
            "low": round(float(row.get("kospi_low", 0)), 2),
            "close": round(float(row.get("kospi_close", 0)), 2),
        })
    market_data["candles"] = candles

    for path in [MARKET_FILE, WEB_PUBLIC_DATA_DIR / "latest_market.json"]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(market_data, f, ensure_ascii=False, indent=2)

    print(f"시장 데이터 저장 완료: {MARKET_FILE}")


if __name__ == "__main__":
    df = collect_all()
    save_latest_market_data(df)
    print("\n최근 5일:")
    print(df.tail())
