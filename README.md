# KOSPI AI 예측

AI 기반 코스피 방향(LONG/SHORT) 예측 대시보드

## 구조

```
stock/
├── pipeline/          # Python ML 파이프라인
├── web/               # Next.js 프론트엔드
├── data/              # JSON 데이터
└── .github/workflows/ # 자동화
```

## 시작하기

### 1. Python 파이프라인

```bash
cd pipeline
pip install -r requirements.txt

# 모델 학습
python train_model.py

# 일일 예측
python predict.py
```

### 2. 웹 프론트엔드

```bash
cd web
npm install
npm run dev
```

http://localhost:3000 에서 대시보드 확인

## 자동화

- **daily-prediction.yml**: 매일 KST 08:00 자동 예측
- **retrain-model.yml**: 매월 1일 모델 재학습

## 기술 스택

| 구분 | 선택 |
|------|------|
| 데이터 수집 | FinanceDataReader + pykrx + yfinance |
| ML 모델 | LightGBM |
| 감성 분석 | KR-FinBERT / 키워드 폴백 |
| 프론트엔드 | Next.js + TailwindCSS |
| 차트 | Lightweight Charts |
| 자동화 | GitHub Actions |
| 배포 | Vercel |

## 면책조항

본 프로젝트의 예측은 AI 모델에 의한 참고 정보이며, 투자 권유가 아닙니다.
