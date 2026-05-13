import type { ReactNode } from "react";

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger";
}) {
  const map = {
    neutral: "bg-zinc-100 text-zinc-800 ring-black/5",
    success: "bg-emerald-50 text-emerald-800 ring-emerald-500/10",
    warning: "bg-amber-50 text-amber-900 ring-amber-500/10",
    danger: "bg-red-50 text-red-800 ring-red-500/10",
  } as const;
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ${map[tone]}`}
    >
      {children}
    </span>
  );
}
