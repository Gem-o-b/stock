"use client";

import type { MarketData } from "@/lib/types";

interface Props {
  market: MarketData | null;
}

interface IndicatorCardProps {
  label: string;
  value: string;
  sub?: string;
}

function IndicatorCard({ label, value, sub }: IndicatorCardProps) {
  return (
    <div className="rounded-xl bg-[var(--color-bg)] border border-[var(--color-border)] p-4">
      <p className="text-xs text-[var(--color-text-muted)] mb-1">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      {sub && (
        <p className="text-xs text-[var(--color-text-muted)]">{sub}</p>
      )}
    </div>
  );
}

export default function MarketIndicators({ market }: Props) {
  if (!market) {
    return (
      <div className="rounded-2xl bg-[var(--color-card)] border border-[var(--color-border)] p-6">
        <h2 className="text-lg font-semibold mb-4">시장 지표</h2>
        <p className="text-[var(--color-text-muted)] text-center">데이터 없음</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-[var(--color-card)] border border-[var(--color-border)] p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">시장 지표</h2>
        <span className="text-xs text-[var(--color-text-muted)]">
          {market.date}
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <IndicatorCard
          label="KOSPI"
          value={market.kospi_close.toLocaleString()}
          sub="종가"
        />
        <IndicatorCard
          label="S&P 500"
          value={market.sp500.toLocaleString()}
        />
        <IndicatorCard
          label="NASDAQ"
          value={market.nasdaq.toLocaleString()}
        />
        <IndicatorCard
          label="VIX (공포지수)"
          value={market.vix.toFixed(2)}
        />
        <IndicatorCard
          label="USD/KRW"
          value={market.usdkrw.toFixed(2)}
          sub="원"
        />
        <IndicatorCard
          label="WTI 원유"
          value={`$${market.wti.toFixed(2)}`}
        />
      </div>
    </div>
  );
}
