export interface Prediction {
  date: string;
  prediction: "LONG" | "SHORT";
  confidence: number;
  probability_long: number;
  probability_short: number;
  kospi_close: number;
  sentiment: {
    avg_score: number;
    positive_ratio: number;
    negative_ratio: number;
    article_count: number;
  };
  actual: "LONG" | "SHORT" | null;
  actual_close: number | null;
  is_correct: boolean | null;
}

export interface Accuracy {
  total_predictions: number;
  evaluated_predictions: number;
  correct_predictions: number;
  accuracy_all: number;
  accuracy_7d: number;
  accuracy_30d: number;
  last_updated: string | null;
}

export interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface MarketData {
  date: string;
  kospi_close: number;
  kospi_open: number;
  kospi_high: number;
  kospi_low: number;
  kospi_volume: number;
  usdkrw: number;
  sp500: number;
  nasdaq: number;
  vix: number;
  wti: number;
  gold: number;
  dxy: number;
  candles: CandleData[];
}
