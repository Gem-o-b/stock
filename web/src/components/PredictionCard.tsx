"use client";

import type { Prediction } from "@/lib/types";

interface Props {
  prediction: Prediction | null;
}

export default function PredictionCard({ prediction }: Props) {
  if (!prediction) {
    return (
      <div className="rounded-2xl bg-[var(--color-card)] border border-[var(--color-border)] p-6">
        <p className="text-[var(--color-text-muted)] text-center">
          예측 데이터가 없습니다
        </p>
      </div>
    );
  }

  const isLong = prediction.prediction === "LONG";
  const directionColor = isLong ? "var(--color-long)" : "var(--color-short)";
  const directionBg = isLong ? "var(--color-long-bg)" : "var(--color-short-bg)";
  const arrow = isLong ? "↑" : "↓";
  const confidencePercent = (prediction.confidence * 100).toFixed(1);

  return (
    <div className="rounded-2xl bg-[var(--color-card)] border border-[var(--color-border)] p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">오늘의 예측</h2>
        <span className="text-sm text-[var(--color-text-muted)]">
          {prediction.date}
        </span>
      </div>

      {/* 메인 예측 */}
      <div className="flex items-center justify-center gap-4 py-6">
        <div
          className="flex items-center gap-3 px-8 py-4 rounded-xl"
          style={{ backgroundColor: directionBg }}
        >
          <span className="text-5xl font-bold" style={{ color: directionColor }}>
            {arrow}
          </span>
          <div>
            <p
              className="text-3xl font-bold"
              style={{ color: directionColor }}
            >
              {prediction.prediction}
            </p>
            <p className="text-sm" style={{ color: directionColor, opacity: 0.8 }}>
              신뢰도 {confidencePercent}%
            </p>
          </div>
        </div>
      </div>

      {/* 확률 바 */}
      <div className="mt-4">
        <div className="flex justify-between text-sm mb-1">
          <span style={{ color: "var(--color-long)" }}>
            LONG {(prediction.probability_long * 100).toFixed(1)}%
          </span>
          <span style={{ color: "var(--color-short)" }}>
            SHORT {(prediction.probability_short * 100).toFixed(1)}%
          </span>
        </div>
        <div className="h-3 rounded-full overflow-hidden flex bg-gray-700">
          <div
            className="transition-all duration-500"
            style={{
              width: `${prediction.probability_long * 100}%`,
              backgroundColor: "var(--color-long)",
            }}
          />
          <div
            className="transition-all duration-500"
            style={{
              width: `${prediction.probability_short * 100}%`,
              backgroundColor: "var(--color-short)",
            }}
          />
        </div>
      </div>

      {/* 기준 종가 */}
      <p className="text-sm text-[var(--color-text-muted)] mt-4 text-center">
        기준 KOSPI: {prediction.kospi_close.toLocaleString()} pt
      </p>

      {/* 결과 (있는 경우) */}
      {prediction.actual && (
        <div
          className="mt-4 p-3 rounded-lg text-center text-sm"
          style={{
            backgroundColor: prediction.is_correct
              ? "rgba(22,163,74,0.15)"
              : "rgba(220,38,38,0.15)",
            color: prediction.is_correct
              ? "var(--color-long)"
              : "var(--color-short)",
          }}
        >
          결과: {prediction.actual} ({prediction.actual_close?.toLocaleString()} pt)
          {" — "}
          {prediction.is_correct ? "적중!" : "빗나감"}
        </div>
      )}
    </div>
  );
}
