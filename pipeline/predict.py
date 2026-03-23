"""일일 예측 메인 스크립트

데이터 수집 → 뉴스 크롤링 → 감성 분석 → 피처 생성 → 예측 → JSON 저장 → 정확도 업데이트
"""
import json
import shutil
import sys
from datetime import datetime, timedelta

import joblib
import numpy as np

from collect_market_data import collect_all, save_latest_market_data
from collect_news import collect_news
from config import (
    ACCURACY_FILE,
    FEATURE_IMPORTANCE_FILE,
    MODEL_FILE,
    PREDICTIONS_FILE,
    WEB_PUBLIC_DATA_DIR,
    ensure_dirs,
    today_kst,
    KST,
)
from feature_engineering import FEATURE_COLUMNS, build_features
from sentiment import analyze_articles

# 피처명 → 한국어 설명 매핑
FEATURE_NAMES_KR = {
    "gold_return": "금 수익률",
    "volume_change": "거래량 변화",
    "usdkrw_change": "환율 변화",
    "wti_return": "유가 수익률",
    "sp500_return": "S&P500 수익률",
    "return_1d": "전일 수익률",
    "vix_change": "VIX 변화",
    "volatility_5d": "5일 변동성",
    "usdkrw_level": "환율 수준",
    "nasdaq_return": "나스닥 수익률",
    "volatility_20d": "20일 변동성",
    "vix_level": "VIX 수준",
    "ma5_ratio": "5일 이평 괴리율",
    "return_5d": "5일 수익률",
    "bb_upper": "볼린저밴드 상단",
    "return_20d": "20일 수익률",
    "ma60_ratio": "60일 이평 괴리율",
    "macd_signal": "MACD 시그널",
    "bb_lower": "볼린저밴드 하단",
    "macd": "MACD",
    "rsi_14": "RSI(14)",
    "ma20_ratio": "20일 이평 괴리율",
    "month": "월",
    "day_of_week": "요일",
    "trading_value_change": "거래대금 변화",
    "news_sentiment": "뉴스 감성",
    "news_positive_ratio": "뉴스 긍정 비율",
    "news_negative_ratio": "뉴스 부정 비율",
    "news_article_count": "뉴스 기사 수",
    "is_month_end": "월말 여부",
}

# 피처별 방향성 해석 (양수일 때 어떤 의미인지)
FEATURE_IMPACT_DESC = {
    "gold_return": ("금 가격 상승 → 안전자산 선호", "금 가격 하락 → 위험자산 회피 신호"),
    "volume_change": ("거래량 증가 → 시장 관심 상승", "거래량 감소 → 시장 관심 하락"),
    "usdkrw_change": ("원화 약세 → 외국인 매도 압력", "원화 강세 → 외국인 매수 유인"),
    "wti_return": ("유가 상승 → 인플레이션 우려", "유가 하락 → 비용 부담 완화"),
    "sp500_return": ("미국 증시 상승 → 긍정적 외부 환경", "미국 증시 하락 → 부정적 외부 환경"),
    "return_1d": ("전일 상승 → 모멘텀 지속", "전일 하락 → 하락 모멘텀"),
    "vix_change": ("공포지수 상승 → 불안 확대", "공포지수 하락 → 불안 완화"),
    "volatility_5d": ("단기 변동성 확대 → 불확실성 증가", "단기 변동성 축소 → 안정적"),
    "usdkrw_level": ("고환율 → 수출 유리/외인 매도", "저환율 → 외인 매수 유인"),
    "nasdaq_return": ("나스닥 상승 → 기술주 긍정적", "나스닥 하락 → 기술주 부정적"),
    "volatility_20d": ("장기 변동성 확대 → 불확실성", "장기 변동성 축소 → 안정 국면"),
    "vix_level": ("높은 공포지수 → 시장 불안", "낮은 공포지수 → 시장 안정"),
    "ma5_ratio": ("5일선 상회 → 단기 상승 추세", "5일선 하회 → 단기 하락 추세"),
    "return_5d": ("5일간 상승 → 상승 모멘텀", "5일간 하락 → 하락 모멘텀"),
    "return_20d": ("20일간 상승 → 중기 상승 추세", "20일간 하락 → 중기 하락 추세"),
    "ma60_ratio": ("60일선 상회 → 장기 상승 추세", "60일선 하회 → 장기 하락 추세"),
    "macd_signal": ("MACD 시그널 양수 → 매수 신호", "MACD 시그널 음수 → 매도 신호"),
    "macd": ("MACD 양수 → 상승 추세", "MACD 음수 → 하락 추세"),
    "rsi_14": ("RSI 높음 → 과매수 구간", "RSI 낮음 → 과매도 구간"),
    "ma20_ratio": ("20일선 상회 → 중기 상승", "20일선 하회 → 중기 하락"),
}


def load_feature_importance() -> dict:
    """피처 중요도 로드"""
    if FEATURE_IMPORTANCE_FILE.exists():
        with open(FEATURE_IMPORTANCE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_reasons(featured_df, prediction_direction: str,
                  articles: list[dict] | None = None,
                  sentiment_result: dict | None = None) -> dict:
    """예측 근거 데이터 생성

    Args:
        featured_df: 피처가 생성된 DataFrame
        prediction_direction: "LONG" 또는 "SHORT"
        articles: 수집된 뉴스 기사 목록
        sentiment_result: 감성 분석 결과

    Returns:
        reasons dict (top_factors + market_summary + summary + news_headlines)
    """
    importance = load_feature_importance()
    latest = featured_df[FEATURE_COLUMNS].iloc[-1]

    # 피처 중요도 × 실제값 부호로 기여도 계산
    contributions = []
    for col in FEATURE_COLUMNS:
        imp = importance.get(col, 0)
        val = float(latest[col])
        if imp == 0:
            continue
        # 기여도 = 중요도 × |값| (방향성은 값의 부호로 판단)
        contribution = imp * abs(val)
        # 값의 부호에 따라 impact 방향 결정
        if val > 0:
            impact = "LONG" if col not in ("vix_level", "vix_change", "usdkrw_change", "usdkrw_level") else "SHORT"
        elif val < 0:
            impact = "SHORT" if col not in ("vix_level", "vix_change", "usdkrw_change", "usdkrw_level") else "LONG"
        else:
            impact = "NEUTRAL"

        # 설명 생성
        desc_pair = FEATURE_IMPACT_DESC.get(col)
        if desc_pair:
            description = desc_pair[0] if val >= 0 else desc_pair[1]
        else:
            description = f"{FEATURE_NAMES_KR.get(col, col)}: {val:.4f}"

        contributions.append({
            "name": FEATURE_NAMES_KR.get(col, col),
            "feature": col,
            "value": round(val, 6),
            "importance": imp,
            "contribution": round(contribution, 4),
            "impact": impact,
            "description": description,
        })

    # 기여도 상위 5개
    contributions.sort(key=lambda x: x["contribution"], reverse=True)
    top_factors = contributions[:5]

    # 시장 상태 요약
    rsi = float(latest.get("rsi_14", 50))
    macd_val = float(latest.get("macd", 0))
    macd_sig = float(latest.get("macd_signal", 0))
    vix = float(latest.get("vix_level", 0))
    ma5 = float(latest.get("ma5_ratio", 0))

    if rsi >= 70:
        rsi_signal = "과매수"
    elif rsi <= 30:
        rsi_signal = "과매도"
    elif rsi >= 60:
        rsi_signal = "강세"
    elif rsi <= 40:
        rsi_signal = "약세"
    else:
        rsi_signal = "중립"

    if macd_val > macd_sig:
        macd_signal_text = "매수"
    else:
        macd_signal_text = "매도"

    if vix >= 30:
        vix_status = "공포"
    elif vix >= 20:
        vix_status = "불안"
    else:
        vix_status = "안정"

    if ma5 > 0:
        trend = "5일 이동평균 상회"
    else:
        trend = "5일 이동평균 하회"

    market_summary = {
        "rsi_14": round(rsi, 2),
        "rsi_signal": rsi_signal,
        "macd_signal": macd_signal_text,
        "vix_level": round(vix, 2),
        "vix_status": vix_status,
        "trend": trend,
    }

    # --- 초보자용 요약 문장 생성 ---
    direction_kr = "상승(LONG)" if prediction_direction == "LONG" else "하락(SHORT)"

    # 1) 뉴스 파트
    news_headlines = []
    news_summary = ""
    if articles:
        news_headlines = [
            {"title": a["title"], "press": a.get("press", "")}
            for a in articles[:5]
        ]
        if sentiment_result and sentiment_result.get("article_count", 0) > 0:
            avg = sentiment_result["avg_sentiment"]
            pos_r = sentiment_result["positive_ratio"]
            neg_r = sentiment_result["negative_ratio"]
            if avg > 0.1:
                news_summary = (
                    f"오늘 뉴스는 전반적으로 긍정적입니다. "
                    f"수집된 {sentiment_result['article_count']}건의 기사 중 "
                    f"긍정 {pos_r:.0%}, 부정 {neg_r:.0%}로 "
                    f"시장에 호재성 소식이 많았습니다."
                )
            elif avg < -0.1:
                news_summary = (
                    f"오늘 뉴스는 전반적으로 부정적입니다. "
                    f"수집된 {sentiment_result['article_count']}건의 기사 중 "
                    f"부정 {neg_r:.0%}, 긍정 {pos_r:.0%}로 "
                    f"시장에 악재성 소식이 많았습니다."
                )
            else:
                news_summary = (
                    f"오늘 뉴스는 뚜렷한 방향성 없이 중립적입니다. "
                    f"수집된 {sentiment_result['article_count']}건의 기사 중 "
                    f"긍정 {pos_r:.0%}, 부정 {neg_r:.0%}입니다."
                )
        else:
            news_summary = "오늘은 주요 뉴스가 수집되지 않았습니다."
    else:
        news_summary = "오늘은 주요 뉴스가 수집되지 않았습니다."

    # 2) 기술 지표 파트 (쉬운 말)
    usdkrw = float(latest.get("usdkrw_level", 0))
    sp500_ret = float(latest.get("sp500_return", 0))
    nasdaq_ret = float(latest.get("nasdaq_return", 0))

    tech_parts = []
    # 환율
    if usdkrw > 0:
        if usdkrw >= 1400:
            tech_parts.append(f"원/달러 환율이 {usdkrw:,.0f}원으로 높은 편이라 외국인 투자자의 매도 압력이 있을 수 있습니다")
        elif usdkrw <= 1200:
            tech_parts.append(f"원/달러 환율이 {usdkrw:,.0f}원으로 낮은 편이라 외국인 투자자의 매수 유인이 있습니다")
    # VIX
    if vix >= 30:
        tech_parts.append(f"공포지수(VIX)가 {vix:.1f}로 매우 높아 글로벌 시장의 불안감이 큽니다")
    elif vix >= 20:
        tech_parts.append(f"공포지수(VIX)가 {vix:.1f}로 다소 불안한 수준입니다")
    else:
        tech_parts.append(f"공포지수(VIX)가 {vix:.1f}로 시장이 비교적 안정적입니다")
    # 미국 시장
    if abs(sp500_ret) > 0.001 or abs(nasdaq_ret) > 0.001:
        us_dir = "상승" if sp500_ret > 0 else "하락"
        tech_parts.append(
            f"미국 증시가 전일 {us_dir}하여 "
            f"(S&P500 {sp500_ret:+.1%}, 나스닥 {nasdaq_ret:+.1%}) "
            f"국내 시장에 {'긍정적' if sp500_ret > 0 else '부정적'}인 영향을 줄 수 있습니다"
        )
    # RSI
    if rsi >= 70:
        tech_parts.append("RSI 지표가 과매수 구간으로, 단기 조정 가능성이 있습니다")
    elif rsi <= 30:
        tech_parts.append("RSI 지표가 과매도 구간으로, 반등 가능성이 있습니다")
    # 추세
    if ma5 > 0.01:
        tech_parts.append("최근 주가가 단기 평균선 위에 있어 상승 흐름을 유지하고 있습니다")
    elif ma5 < -0.01:
        tech_parts.append("최근 주가가 단기 평균선 아래로 내려와 하락 흐름입니다")

    tech_summary = ". ".join(tech_parts) + "." if tech_parts else ""

    # 3) 종합
    summary = (
        f"AI 모델은 내일 KOSPI가 {direction_kr}할 것으로 예측했습니다.\n\n"
        f"[뉴스 동향] {news_summary}\n\n"
        f"[시장 상황] {tech_summary}"
    )

    return {
        "top_factors": top_factors,
        "market_summary": market_summary,
        "summary": summary,
        "news_headlines": news_headlines,
    }


def load_model():
    """학습된 모델 로드"""
    if not MODEL_FILE.exists():
        print(f"모델 파일 없음: {MODEL_FILE}")
        print("먼저 train_model.py를 실행하세요.")
        sys.exit(1)
    return joblib.load(MODEL_FILE)


def load_predictions() -> list[dict]:
    """기존 예측 데이터 로드"""
    if PREDICTIONS_FILE.exists():
        with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_predictions(predictions: list[dict]):
    """예측 데이터 저장 (data/ + web/public/data/)"""
    for path in [PREDICTIONS_FILE, WEB_PUBLIC_DATA_DIR / "predictions.json"]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)


def calc_cumulative_return(predictions: list[dict]) -> dict:
    """예측 기반 누적 수익률 계산

    예측 방향대로 매매했을 때의 누적 수익률.
    - LONG 예측: (actual_close - kospi_close) / kospi_close
    - SHORT 예측: (kospi_close - actual_close) / kospi_close
    """
    evaluated = [
        p for p in predictions
        if p.get("actual") is not None and p.get("actual_close") is not None
    ]
    # 날짜순 정렬
    evaluated.sort(key=lambda p: p["date"])

    cumulative = 1.0
    daily_returns = []

    for p in evaluated:
        base = p["kospi_close"]
        actual = p["actual_close"]
        if base == 0:
            continue

        if p["prediction"] == "LONG":
            daily_ret = (actual - base) / base
        else:  # SHORT
            daily_ret = (base - actual) / base

        daily_returns.append({
            "date": p["date"],
            "return": round(daily_ret, 6),
        })
        cumulative *= (1 + daily_ret)

    return {
        "cumulative_return": round((cumulative - 1), 6),
        "total_trades": len(daily_returns),
        "daily_returns": daily_returns,
    }


def update_accuracy(predictions: list[dict]):
    """정확도 계산 및 저장"""
    evaluated = [p for p in predictions if p.get("actual") is not None]
    returns = calc_cumulative_return(predictions)

    if not evaluated:
        accuracy_data = {
            "total_predictions": len(predictions),
            "evaluated_predictions": 0,
            "correct_predictions": 0,
            "accuracy_all": 0.0,
            "accuracy_7d": 0.0,
            "accuracy_30d": 0.0,
            "cumulative_return": 0.0,
            "total_trades": 0,
            "daily_returns": [],
            "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        }
    else:
        correct = sum(1 for p in evaluated if p["prediction"] == p["actual"])
        now = datetime.now(KST)

        # 최근 7일
        recent_7d = [
            p for p in evaluated
            if (now - datetime.strptime(p["date"], "%Y-%m-%d").replace(
                tzinfo=KST
            )).days <= 7
        ]
        correct_7d = sum(1 for p in recent_7d if p["prediction"] == p["actual"])

        # 최근 30일
        recent_30d = [
            p for p in evaluated
            if (now - datetime.strptime(p["date"], "%Y-%m-%d").replace(
                tzinfo=KST
            )).days <= 30
        ]
        correct_30d = sum(1 for p in recent_30d if p["prediction"] == p["actual"])

        accuracy_data = {
            "total_predictions": len(predictions),
            "evaluated_predictions": len(evaluated),
            "correct_predictions": correct,
            "accuracy_all": round(correct / len(evaluated), 4) if evaluated else 0.0,
            "accuracy_7d": round(correct_7d / len(recent_7d), 4) if recent_7d else 0.0,
            "accuracy_30d": round(correct_30d / len(recent_30d), 4) if recent_30d else 0.0,
            "cumulative_return": returns["cumulative_return"],
            "total_trades": returns["total_trades"],
            "daily_returns": returns["daily_returns"],
            "last_updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        }

    for path in [ACCURACY_FILE, WEB_PUBLIC_DATA_DIR / "accuracy.json"]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(accuracy_data, f, ensure_ascii=False, indent=2)

    print(f"정확도 업데이트: 전체 {accuracy_data['accuracy_all']:.1%}, "
          f"7일 {accuracy_data['accuracy_7d']:.1%}, "
          f"30일 {accuracy_data['accuracy_30d']:.1%}, "
          f"누적 수익률 {accuracy_data['cumulative_return']:.2%}")


def evaluate_previous_predictions(predictions: list[dict], market_df) -> list[dict]:
    """이전 예측의 실제 결과를 업데이트"""
    if market_df.empty:
        return predictions

    for pred in predictions:
        if pred.get("actual") is not None:
            continue  # 이미 평가됨

        pred_date = pred["date"]
        # 예측 다음 거래일의 종가와 비교
        try:
            pred_dt = datetime.strptime(pred_date, "%Y-%m-%d")
            # 해당 날짜 이후 데이터 찾기
            future = market_df.loc[market_df.index > pred_dt.strftime("%Y-%m-%d")]
            if len(future) >= 1:
                # 예측 당일 종가
                if pred_dt.strftime("%Y-%m-%d") in market_df.index.strftime("%Y-%m-%d"):
                    base_close = market_df.loc[
                        market_df.index.strftime("%Y-%m-%d") == pred_dt.strftime("%Y-%m-%d"),
                        "kospi_close"
                    ].iloc[0]
                    next_close = future.iloc[0]["kospi_close"]

                    actual = "LONG" if next_close > base_close else "SHORT"
                    pred["actual"] = actual
                    pred["actual_close"] = round(float(next_close), 2)
                    pred["is_correct"] = pred["prediction"] == actual
        except Exception:
            continue

    return predictions


def is_trading_day(date_str: str) -> bool:
    """주말 여부 확인 (토/일이면 False)"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.weekday() < 5  # 0=월 ~ 4=금


def get_next_trading_date() -> str:
    """다음 거래일(평일) 반환"""
    now = datetime.now(KST)
    # 오늘이 평일이면 오늘, 아니면 다음 월요일
    while now.weekday() >= 5:
        now += timedelta(days=1)
    return now.strftime("%Y-%m-%d")


def run_prediction():
    """일일 예측 메인 함수"""
    ensure_dirs()
    date = today_kst()

    # 주말 체크: 토/일이면 다음 월요일 예측
    if not is_trading_day(date):
        next_day = get_next_trading_date()
        print(f"오늘({date})은 주말입니다. 다음 거래일({next_day})로 예측합니다.")
        date = next_day

    print("=" * 60)
    print(f"KOSPI 방향 예측 - {date}")
    print("=" * 60)

    # 기존 예측 로드
    predictions = load_predictions()

    # 이미 오늘 예측이 있는지 확인
    existing = next((p for p in predictions if p["date"] == date), None)
    existing_reasons = existing.get("reasons") if existing else None
    if existing and existing_reasons and existing_reasons.get("summary"):
        print(f"{date} 예측이 이미 존재합니다. 건너뜁니다.")
        # 정확도/갱신 시각은 항상 업데이트
        update_accuracy(predictions)
        copy_data_to_web()
        return

    # 1. 시장 데이터 수집
    print("\n[1/5] 시장 데이터 수집")
    market_df = collect_all()
    save_latest_market_data(market_df)

    # 2. 이전 예측 평가
    print("\n[2/5] 이전 예측 평가")
    predictions = evaluate_previous_predictions(predictions, market_df)

    # 3. 뉴스 수집 + 감성 분석
    print("\n[3/5] 뉴스 수집 및 감성 분석")
    articles = collect_news()
    sentiment_result = analyze_articles(articles, use_finbert=False)  # 경량 모드
    print(f"  감성 점수: {sentiment_result['avg_sentiment']:.3f} "
          f"(긍정 {sentiment_result['positive_ratio']:.0%} / "
          f"부정 {sentiment_result['negative_ratio']:.0%})")

    # 4. 피처 생성 + 예측
    print("\n[4/5] 피처 생성 및 예측")
    featured_df = build_features(market_df, sentiment_result, include_target=False)

    model = load_model()
    latest_features = featured_df[FEATURE_COLUMNS].iloc[-1:].values

    prediction_proba = model.predict_proba(latest_features)[0]
    prediction_class = int(model.predict(latest_features)[0])
    direction = "LONG" if prediction_class == 1 else "SHORT"
    confidence = float(max(prediction_proba))

    print(f"  예측: {direction} (신뢰도: {confidence:.1%})")
    print(f"  확률: LONG {prediction_proba[1]:.1%} / SHORT {prediction_proba[0]:.1%}")

    # 예측 근거 생성
    reasons = build_reasons(featured_df, direction, articles, sentiment_result)
    print(f"  주요 기여 요인: {', '.join(f['name'] for f in reasons['top_factors'])}")

    # 5. 결과 저장
    print("\n[5/5] 결과 저장")

    if existing:
        # 기존 예측에 reasons만 보강
        existing["reasons"] = reasons
        print(f"  기존 예측에 근거 데이터 추가")
    else:
        new_prediction = {
            "date": date,
            "prediction": direction,
            "confidence": round(confidence, 4),
            "probability_long": round(float(prediction_proba[1]), 4),
            "probability_short": round(float(prediction_proba[0]), 4),
            "kospi_close": round(float(market_df.iloc[-1]["kospi_close"]), 2),
            "sentiment": {
                "avg_score": sentiment_result["avg_sentiment"],
                "positive_ratio": sentiment_result["positive_ratio"],
                "negative_ratio": sentiment_result["negative_ratio"],
                "article_count": sentiment_result["article_count"],
            },
            "reasons": reasons,
            "actual": None,
            "actual_close": None,
            "is_correct": None,
        }
        predictions.append(new_prediction)
    save_predictions(predictions)
    update_accuracy(predictions)

    # web/public/data/에도 복사
    copy_data_to_web()

    print("\n" + "=" * 60)
    print(f"예측 완료: {date} → {direction} (신뢰도 {confidence:.1%})")
    print("=" * 60)


def copy_data_to_web():
    """data/ 파일들을 web/public/data/에 복사"""
    WEB_PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for src in [PREDICTIONS_FILE, ACCURACY_FILE]:
        if src.exists():
            dst = WEB_PUBLIC_DATA_DIR / src.name
            shutil.copy2(src, dst)


if __name__ == "__main__":
    run_prediction()
