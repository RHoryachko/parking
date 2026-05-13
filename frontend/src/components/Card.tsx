import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-2xl border border-black/5 bg-white/80 p-6 shadow-glass backdrop-blur-xl ${className}`}
    >
      {children}
    </div>
  );
}
