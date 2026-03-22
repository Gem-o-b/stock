"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-card)]">
      <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-2xl font-bold text-[var(--color-accent)]">
            KOSPI AI
          </span>
          <span className="text-sm text-[var(--color-text-muted)]">예측</span>
        </Link>
        <nav className="flex gap-4">
          <Link
            href="/"
            className={`text-sm px-3 py-1.5 rounded-lg transition-colors ${
              pathname === "/"
                ? "bg-[var(--color-accent)] text-white"
                : "text-[var(--color-text-muted)] hover:text-white"
            }`}
          >
            대시보드
          </Link>
          <Link
            href="/history"
            className={`text-sm px-3 py-1.5 rounded-lg transition-colors ${
              pathname === "/history"
                ? "bg-[var(--color-accent)] text-white"
                : "text-[var(--color-text-muted)] hover:text-white"
            }`}
          >
            히스토리
          </Link>
        </nav>
      </div>
    </header>
  );
}
