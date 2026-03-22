"""LightGBM 모델 학습 모듈

- 이진 분류: LONG(1) vs SHORT(0)
- TimeSeriesSplit 5-fold 교차검증
- 모델 + 피처 중요도 저장
"""
import json

import joblib
import lightgbm as lgb
import numpy as np
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import TimeSeriesSplit

from collect_market_data import collect_all, save_latest_market_data
from config import (
    CV_SPLITS,
    FEATURE_IMPORTANCE_FILE,
    LGBM_PARAMS,
    MODEL_FILE,
    TARGET_COL,
    ensure_dirs,
)
from feature_engineering import FEATURE_COLUMNS, build_features


def train_model():
    """모델 학습 메인 함수"""
    ensure_dirs()

    # 1. 데이터 수집
    print("=" * 60)
    print("1단계: 데이터 수집")
    print("=" * 60)
    market_df = collect_all()
    save_latest_market_data(market_df)

    # 2. 피처 생성
    print("\n" + "=" * 60)
    print("2단계: 피처 생성")
    print("=" * 60)
    df = build_features(market_df, include_target=True)

    X = df[FEATURE_COLUMNS].values
    y = df[TARGET_COL].values

    print(f"학습 데이터: {X.shape[0]}행, {X.shape[1]}열")
    print(f"LONG 비율: {y.mean():.2%}, SHORT 비율: {1 - y.mean():.2%}")

    # 3. 시계열 교차검증
    print("\n" + "=" * 60)
    print("3단계: 시계열 교차검증")
    print("=" * 60)
    tscv = TimeSeriesSplit(n_splits=CV_SPLITS)
    cv_scores = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        model = lgb.LGBMClassifier(**LGBM_PARAMS)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.log_evaluation(0)],
        )

        y_pred = model.predict(X_val)
        acc = accuracy_score(y_val, y_pred)
        cv_scores.append(acc)
        print(f"  Fold {fold}: 정확도 {acc:.4f} (학습: {len(train_idx)}, 검증: {len(val_idx)})")

    mean_acc = np.mean(cv_scores)
    std_acc = np.std(cv_scores)
    print(f"\n  CV 평균 정확도: {mean_acc:.4f} (+/- {std_acc:.4f})")

    # 4. 최종 모델 학습 (전체 데이터)
    print("\n" + "=" * 60)
    print("4단계: 최종 모델 학습")
    print("=" * 60)
    final_model = lgb.LGBMClassifier(**LGBM_PARAMS)
    final_model.fit(X, y)

    # 5. 모델 저장
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, MODEL_FILE)
    print(f"모델 저장: {MODEL_FILE}")

    # 6. 피처 중요도 저장
    importance = dict(zip(FEATURE_COLUMNS, final_model.feature_importances_.tolist()))
    importance_sorted = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

    with open(FEATURE_IMPORTANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(importance_sorted, f, ensure_ascii=False, indent=2)

    print(f"\n피처 중요도 Top 10:")
    for i, (feat, imp) in enumerate(list(importance_sorted.items())[:10], 1):
        print(f"  {i}. {feat}: {imp}")

    # 7. 최종 평가
    print("\n" + "=" * 60)
    print("최종 결과")
    print("=" * 60)
    y_final_pred = final_model.predict(X)
    print(classification_report(y, y_final_pred, target_names=["SHORT", "LONG"]))
    print(f"CV 정확도: {mean_acc:.4f}")

    return final_model, mean_acc


if __name__ == "__main__":
    train_model()
