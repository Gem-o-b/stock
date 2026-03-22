"use client";

interface Props {
  sentiment: {
    avg_score: number;
    positive_ratio: number;
    negative_ratio: number;
    article_count: number;
  } | null;
}

export default function NewsSentimentBar({ sentiment }: Props) {
  if (!sentiment) {
    return (
      <div className="rounded-2xl bg-[var(--color-card)] border border-[var(--color-border)] p-6">
        <h2 className="text-lg font-semibold mb-4">뉴스 감성</h2>
        <p className="text-[var(--color-text-muted)] text-center">데이터 없음</p>
      </div>
    );
  }

  const neutralRatio = Math.max(
    0,
    1 - sentiment.positive_ratio - sentiment.negative_ratio
  );
  const scoreColor =
    sentiment.avg_score > 0.05
      ? "var(--color-long)"
      : sentiment.avg_score < -0.05
        ? "var(--color-short)"
        : "var(--color-neutral)";
  const scoreLabel =
    sentiment.avg_score > 0.05
      ? "긍정적"
      : sentiment.avg_score < -0.05
        ? "부정적"
        : "중립";

  return (
    <div className="rounded-2xl bg-[var(--color-card)] border border-[var(--color-border)] p-6">
      <h2 className="text-lg font-semibold mb-4">뉴스 감성</h2>

      {/* 감성 점수 */}
      <div className="flex items-center justify-center gap-3 mb-4">
        <span className="text-3xl font-bold" style={{ color: scoreColor }}>
          {sentiment.avg_score > 0 ? "+" : ""}
          {sentiment.avg_score.toFixed(2)}
        </span>
        <span className="text-sm" style={{ color: scoreColor }}>
          {scoreLabel}
        </span>
      </div>

      {/* 비율 바 */}
      <div className="h-4 rounded-full overflow-hidden flex mb-2">
        <div
          className="transition-all duration-500"
          style={{
            width: `${sentiment.positive_ratio * 100}%`,
            backgroundColor: "var(--color-long)",
          }}
        />
        <div
          className="transition-all duration-500"
          style={{
            width: `${neutralRatio * 100}%`,
            backgroundColor: "var(--color-neutral)",
          }}
        />
        <div
          className="transition-all duration-500"
          style={{
            width: `${sentiment.negative_ratio * 100}%`,
            backgroundColor: "var(--color-short)",
          }}
        />
      </div>

      <div className="flex justify-between text-xs text-[var(--color-text-muted)]">
        <span style={{ color: "var(--color-long)" }}>
          긍정 {(sentiment.positive_ratio * 100).toFixed(0)}%
        </span>
        <span>
          중립 {(neutralRatio * 100).toFixed(0)}%
        </span>
        <span style={{ color: "var(--color-short)" }}>
          부정 {(sentiment.negative_ratio * 100).toFixed(0)}%
        </span>
      </div>

      <p className="text-xs text-[var(--color-text-muted)] mt-3 text-center">
        분석 기사 {sentiment.article_count}건
      </p>
    </div>
  );
}
