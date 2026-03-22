"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { loadPredictions } from "@/lib/loadPredictions";
import type { Prediction } from "@/lib/types";

export default function HistoryPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPredictions().then((data) => {
      setPredictions([...data].reverse());
      setLoading(false);
    });
  }, []);

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
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">예측 히스토리</h1>

        {predictions.length === 0 ? (
          <p className="text-[var(--color-text-muted)] text-center py-12">
            예측 기록이 없습니다
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)] text-[var(--color-text-muted)]">
                  <th className="text-left py-3 px-4">날짜</th>
                  <th className="text-center py-3 px-4">예측</th>
                  <th className="text-center py-3 px-4">신뢰도</th>
                  <th className="text-right py-3 px-4">기준가</th>
                  <th className="text-center py-3 px-4">실제</th>
                  <th className="text-right py-3 px-4">실제 종가</th>
                  <th className="text-center py-3 px-4">결과</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((pred) => (
                  <tr
                    key={pred.date}
                    className="border-b border-[var(--color-border)] hover:bg-[var(--color-card-hover)] transition-colors"
                  >
                    <td className="py-3 px-4">{pred.date}</td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className="inline-block px-2 py-0.5 rounded text-xs font-semibold"
                        style={{
                          backgroundColor:
                            pred.prediction === "LONG"
                              ? "var(--color-long-bg)"
                              : "var(--color-short-bg)",
                          color:
                            pred.prediction === "LONG"
                              ? "var(--color-long)"
                              : "var(--color-short)",
                        }}
                      >
                        {pred.prediction === "LONG" ? "↑" : "↓"}{" "}
                        {pred.prediction}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {(pred.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-right">
                      {pred.kospi_close.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {pred.actual ? (
                        <span
                          style={{
                            color:
                              pred.actual === "LONG"
                                ? "var(--color-long)"
                                : "var(--color-short)",
                          }}
                        >
                          {pred.actual === "LONG" ? "↑" : "↓"} {pred.actual}
                        </span>
                      ) : (
                        <span className="text-[var(--color-text-muted)]">
                          대기중
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {pred.actual_close
                        ? pred.actual_close.toLocaleString()
                        : "-"}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {pred.is_correct === true && (
                        <span className="text-[var(--color-long)] font-semibold">
                          O
                        </span>
                      )}
                      {pred.is_correct === false && (
                        <span className="text-[var(--color-short)] font-semibold">
                          X
                        </span>
                      )}
                      {pred.is_correct === null && (
                        <span className="text-[var(--color-text-muted)]">
                          -
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 면책조항 */}
        <div className="mt-8 rounded-xl bg-[var(--color-card)] border border-[var(--color-border)] p-4 text-xs text-[var(--color-text-muted)] leading-relaxed">
          <p className="font-semibold mb-1">면책조항</p>
          <p>
            본 사이트의 예측은 AI 모델에 의한 참고 정보이며, 투자 권유가 아닙니다.
            주식 투자는 원금 손실의 위험이 있으며, 모든 투자 결정과 그에 따른 결과는
            투자자 본인의 책임입니다.
          </p>
        </div>
      </main>
    </>
  );
}
