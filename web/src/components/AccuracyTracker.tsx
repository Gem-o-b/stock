"use client";

import type { Accuracy } from "@/lib/types";

interface Props {
  accuracy: Accuracy;
}

function AccuracyRing({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const percent = Math.round(value * 100);
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (value * circumference);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 -rotate-90" viewBox="0 0 96 96">
          <circle
            cx="48"
            cy="48"
            r="40"
            fill="none"
            stroke="var(--color-border)"
            strokeWidth="6"
          />
          <circle
            cx="48"
            cy="48"
            r="40"
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold">{percent}%</span>
        </div>
      </div>
      <span className="text-sm text-[var(--color-text-muted)]">{label}</span>
    </div>
  );
}

export default function AccuracyTracker({ accuracy }: Props) {
  return (
    <div className="rounded-2xl bg-[var(--color-card)] border border-[var(--color-border)] p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">적중률</h2>
        {accuracy.last_updated && (
          <span className="text-xs text-[var(--color-text-muted)]">
            {accuracy.last_updated} 기준
          </span>
        )}
      </div>

      <div className="flex justify-around">
        <AccuracyRing
          label="전체"
          value={accuracy.accuracy_all}
          color="var(--color-accent)"
        />
        <AccuracyRing
          label="최근 7일"
          value={accuracy.accuracy_7d}
          color="#a855f7"
        />
        <AccuracyRing
          label="최근 30일"
          value={accuracy.accuracy_30d}
          color="#f59e0b"
        />
      </div>

      {/* 누적 수익률 */}
      <div className="mt-5 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-[var(--color-text-muted)]">
            AI 추천 누적 수익률
          </span>
          <span
            className="text-2xl font-bold"
            style={{
              color:
                accuracy.cumulative_return > 0
                  ? "var(--color-long)"
                  : accuracy.cumulative_return < 0
                    ? "var(--color-short)"
                    : "var(--color-text-muted)",
            }}
          >
            {accuracy.cumulative_return > 0 ? "+" : ""}
            {(accuracy.cumulative_return * 100).toFixed(2)}%
          </span>
        </div>
        {accuracy.total_trades > 0 && (
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            {accuracy.total_trades}회 매매 기준
          </p>
        )}
      </div>

      <div className="mt-3 text-center text-sm text-[var(--color-text-muted)]">
        총 {accuracy.total_predictions}건 예측 / {accuracy.evaluated_predictions}건 평가 /{" "}
        {accuracy.correct_predictions}건 적중
      </div>
    </div>
  );
}
