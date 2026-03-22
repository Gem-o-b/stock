"use client";

import { useEffect, useRef } from "react";
import type { CandleData } from "@/lib/types";

interface Props {
  candles: CandleData[];
}

export default function KospiChart({ candles }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof import("lightweight-charts").createChart> | null>(null);

  useEffect(() => {
    if (!containerRef.current || candles.length === 0) return;

    let disposed = false;

    import("lightweight-charts").then(({ createChart }) => {
      if (disposed || !containerRef.current) return;

      // 기존 차트 제거
      if (chartRef.current) {
        chartRef.current.remove();
      }

      const chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height: 300,
        layout: {
          background: { color: "#1e293b" },
          textColor: "#94a3b8",
        },
        grid: {
          vertLines: { color: "#334155" },
          horzLines: { color: "#334155" },
        },
        timeScale: {
          borderColor: "#334155",
        },
        rightPriceScale: {
          borderColor: "#334155",
        },
      });

      const series = chart.addCandlestickSeries({
        upColor: "#16a34a",
        downColor: "#dc2626",
        borderUpColor: "#16a34a",
        borderDownColor: "#dc2626",
        wickUpColor: "#16a34a",
        wickDownColor: "#dc2626",
      });

      series.setData(candles as any);
      chart.timeScale().fitContent();
      chartRef.current = chart;

      const handleResize = () => {
        if (containerRef.current && chartRef.current) {
          chartRef.current.applyOptions({
            width: containerRef.current.clientWidth,
          });
        }
      };

      window.addEventListener("resize", handleResize);

      return () => {
        window.removeEventListener("resize", handleResize);
      };
    });

    return () => {
      disposed = true;
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [candles]);

  return (
    <div className="rounded-2xl bg-[var(--color-card)] border border-[var(--color-border)] p-6">
      <h2 className="text-lg font-semibold mb-4">KOSPI 차트</h2>
      <div ref={containerRef} className="w-full" />
    </div>
  );
}
