"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import PredictionCard from "@/components/PredictionCard";
import PredictionReasons from "@/components/PredictionReasons";
import KospiChart from "@/components/KospiChart";
import AccuracyTracker from "@/components/AccuracyTracker";
import NewsSentimentBar from "@/components/NewsSentimentBar";
import MarketIndicators from "@/components/MarketIndicators";
import {
  loadPredictions,
  loadAccuracy,
  loadMarketData,
  getLatestPrediction,
} from "@/lib/loadPredictions";
import type { Prediction, Accuracy, MarketData } from "@/lib/types";

export default function Home() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [accuracy, setAccuracy] = useState<Accuracy | null>(null);
  const [market, setMarket] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      const [preds, acc, mkt] = await Promise.all([
        loadPredictions(),
        loadAccuracy(),
        loadMarketData(),
      ]);
      setPredictions(preds);
      setAccuracy(acc);
      setMarket(mkt);
      setLoading(false);
    }
    fetchData();
  }, []);

  const latest = getLatestPrediction(predictions);

  if (loading) {
    return (
      <>
        <Header />
        <main className="mx-auto max-w-6xl px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin h-8 w-8 border-4 border-[var(--color-accent)] border-t-transparent rounded-full" />
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <Header />
      <main className="mx-auto max-w-6xl px-4 py-8 space-y-6">
        {/* 상단: 예측 + 적중률 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PredictionCard prediction={latest} />
          {accuracy && <AccuracyTracker accuracy={accuracy} />}
        </div>

        {/* 예측 근거 */}
        {latest?.reasons && (
          <PredictionReasons reasons={latest.reasons} />
        )}

        {/* 중간: 차트 */}
        {market && market.candles.length > 0 && (
          <KospiChart candles={market.candles} />
        )}

        {/* 하단: 감성 + 시장지표 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <NewsSentimentBar sentiment={latest?.sentiment ?? null} />
          <MarketIndicators market={market} />
        </div>

        {/* 면책조항 */}
        <div className="rounded-xl bg-[var(--color-card)] border border-[var(--color-border)] p-4 text-xs text-[var(--color-text-muted)] leading-relaxed">
          <p className="font-semibold mb-1">면책조항</p>
          <p>
            본 사이트의 예측은 AI 모델에 의한 참고 정보이며, 투자 권유가 아닙니다.
            주식 투자는 원금 손실의 위험이 있으며, 모든 투자 결정과 그에 따른 결과는
            투자자 본인의 책임입니다. 과거의 예측 성과가 미래의 수익을 보장하지 않습니다.
          </p>
        </div>
      </main>
    </>
  );
}
