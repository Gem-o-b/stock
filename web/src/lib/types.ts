export interface ReasonFactor {
  name: string;
  feature: string;
  value: number;
  importance: number;
  contribution: number;
  impact: "LONG" | "SHORT" | "NEUTRAL";
  description: string;
}

export interface MarketSummary {
  rsi_14: number;
  rsi_signal: string;
  macd_signal: string;
  vix_level: number;
  vix_status: string;
  trend: string;
}

export interface NewsHeadline {
  title: string;
  press: string;
}

export interface PredictionReasons {
  top_factors: ReasonFactor[];
  market_summary: MarketSummary;
  summary?: string;
  news_headlines?: NewsHeadline[];
}

export interface Prediction {
  date: string;
  target_date?: string;
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
  reasons?: PredictionReasons;
  actual: "LONG" | "SHORT" | null;
  actual_close: number | null;
  is_correct: boolean | null;
}

export interface DailyReturn {
  date: string;
  return: number;
}

export interface Accuracy {
  total_predictions: number;
  evaluated_predictions: number;
  correct_predictions: number;
  accuracy_all: number;
  accuracy_7d: number;
  accuracy_30d: number;
  cumulative_return: number;
  total_trades: number;
  daily_returns: DailyReturn[];
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
