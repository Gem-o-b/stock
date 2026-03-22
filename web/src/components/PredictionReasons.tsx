"use client";

import { useState } from "react";
import type { PredictionReasons as PredictionReasonsType } from "@/lib/types";

interface Props {
  reasons: PredictionReasonsType | undefined;
}

function ImpactBadge({ impact }: { impact: "LONG" | "SHORT" | "NEUTRAL" }) {
  const styles: Record<string, { bg: string; color: string; label: string }> = {
    LONG: { bg: "var(--color-long-bg)", color: "var(--color-long)", label: "LONG" },
    SHORT: { bg: "var(--color-short-bg)", color: "var(--color-short)", label: "SHORT" },
    NEUTRAL: { bg: "rgba(156,163,175,0.2)", color: "var(--color-text-muted)", label: "-" },
  };
  const s = styles[impact];
  return (
    <span
      className="px-2 py-0.5 rounded text-xs font-semibold"
      style={{ backgroundColor: s.bg, color: s.color }}
    >
      {s.label}
    </span>
  );
}

function SignalDot({ status }: { status: string }) {
  let color: string;
  switch (status) {
    case "과매수":
    case "공포":
    case "매도":
      color = "var(--color-short)";
      break;
    case "과매도":
    case "안정":
    case "매수":
      color = "var(--color-long)";
      break;
    default:
      color = "#facc15"; // yellow
  }
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full mr-2"
      style={{ backgroundColor: color }}
    />
  );
}

export default function PredictionReasons({ reasons }: Props) {
  const [open, setOpen] = useState(false);

  if (!reasons) return null;

  const { top_factors, market_summary } = reasons;

  return (
    <div className="rounded-2xl bg-[var(--color-card)] border border-[var(--color-border)] overflow-hidden">
      {/* 토글 헤더 */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left hover:bg-[var(--color-bg)] transition-colors"
      >
        <h2 className="text-lg font-semibold">예측 근거</h2>
        <span
          className="text-[var(--color-text-muted)] transition-transform duration-200"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)" }}
        >
          &#9660;
        </span>
      </button>

      {/* 접이식 내용 */}
      {open && (
        <div className="px-5 pb-5 space-y-5">
          {/* 상위 기여 요인 */}
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text-muted)] mb-3">
              주요 기여 요인
            </h3>
            <div className="space-y-2">
              {top_factors.map((factor, i) => (
                <div
                  key={factor.feature}
                  className="flex items-start gap-3 rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3"
                >
                  <span className="text-lg font-bold text-[var(--color-text-muted)] w-6 text-center shrink-0">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm">{factor.name}</span>
                      <ImpactBadge impact={factor.impact} />
                    </div>
                    <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
                      {factor.description}
                    </p>
                  </div>
                  <span className="text-xs text-[var(--color-text-muted)] shrink-0 tabular-nums">
                    {factor.value >= 0 ? "+" : ""}
                    {factor.value < 0.01 && factor.value > -0.01
                      ? factor.value.toFixed(4)
                      : factor.value.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 시장 상태 요약 */}
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text-muted)] mb-3">
              시장 상태 요약
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3">
                <p className="text-xs text-[var(--color-text-muted)] mb-1">RSI(14)</p>
                <div className="flex items-center">
                  <SignalDot status={market_summary.rsi_signal} />
                  <span className="font-semibold">{market_summary.rsi_14}</span>
                </div>
                <p className="text-xs text-[var(--color-text-muted)] mt-1">
                  {market_summary.rsi_signal}
                </p>
              </div>

              <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3">
                <p className="text-xs text-[var(--color-text-muted)] mb-1">MACD</p>
                <div className="flex items-center">
                  <SignalDot status={market_summary.macd_signal} />
                  <span className="font-semibold">{market_summary.macd_signal}</span>
                </div>
                <p className="text-xs text-[var(--color-text-muted)] mt-1">
                  시그널 대비
                </p>
              </div>

              <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3">
                <p className="text-xs text-[var(--color-text-muted)] mb-1">VIX</p>
                <div className="flex items-center">
                  <SignalDot status={market_summary.vix_status} />
                  <span className="font-semibold">{market_summary.vix_level}</span>
                </div>
                <p className="text-xs text-[var(--color-text-muted)] mt-1">
                  {market_summary.vix_status}
                </p>
              </div>

              <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-3 col-span-2 sm:col-span-3">
                <p className="text-xs text-[var(--color-text-muted)] mb-1">추세</p>
                <p className="font-semibold text-sm">{market_summary.trend}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
