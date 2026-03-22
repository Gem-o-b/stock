import type { Prediction, Accuracy, MarketData } from "./types";

const BASE_PATH = "/data";

export async function loadPredictions(): Promise<Prediction[]> {
  try {
    const res = await fetch(`${BASE_PATH}/predictions.json`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function loadAccuracy(): Promise<Accuracy> {
  try {
    const res = await fetch(`${BASE_PATH}/accuracy.json`);
    if (!res.ok) throw new Error();
    return await res.json();
  } catch {
    return {
      total_predictions: 0,
      evaluated_predictions: 0,
      correct_predictions: 0,
      accuracy_all: 0,
      accuracy_7d: 0,
      accuracy_30d: 0,
      last_updated: null,
    };
  }
}

export async function loadMarketData(): Promise<MarketData | null> {
  try {
    const res = await fetch(`${BASE_PATH}/latest_market.json`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export function getLatestPrediction(predictions: Prediction[]): Prediction | null {
  if (predictions.length === 0) return null;
  return predictions[predictions.length - 1];
}
