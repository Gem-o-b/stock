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
    MODEL_FILE,
    PREDICTIONS_FILE,
    WEB_PUBLIC_DATA_DIR,
    ensure_dirs,
    today_kst,
    KST,
)
from feature_engineering import FEATURE_COLUMNS, build_features
from sentiment import analyze_articles


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


def update_accuracy(predictions: list[dict]):
    """정확도 계산 및 저장"""
    evaluated = [p for p in predictions if p.get("actual") is not None]

    if not evaluated:
        accuracy_data = {
            "total_predictions": len(predictions),
            "evaluated_predictions": 0,
            "correct_predictions": 0,
            "accuracy_all": 0.0,
            "accuracy_7d": 0.0,
            "accuracy_30d": 0.0,
            "last_updated": today_kst(),
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
            "last_updated": today_kst(),
        }

    for path in [ACCURACY_FILE, WEB_PUBLIC_DATA_DIR / "accuracy.json"]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(accuracy_data, f, ensure_ascii=False, indent=2)

    print(f"정확도 업데이트: 전체 {accuracy_data['accuracy_all']:.1%}, "
          f"7일 {accuracy_data['accuracy_7d']:.1%}, "
          f"30일 {accuracy_data['accuracy_30d']:.1%}")


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
    if any(p["date"] == date for p in predictions):
        print(f"{date} 예측이 이미 존재합니다. 건너뜁니다.")
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

    # 5. 결과 저장
    print("\n[5/5] 결과 저장")
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
