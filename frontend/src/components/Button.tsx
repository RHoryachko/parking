import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

export function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode; variant?: Variant }) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none";
  const styles: Record<Variant, string> = {
    primary:
      "bg-zinc-900 text-white shadow-sm hover:bg-zinc-800 ring-1 ring-black/5",
    secondary:
      "bg-white/80 text-zinc-900 ring-1 ring-black/10 backdrop-blur hover:bg-white",
    ghost: "text-zinc-700 hover:bg-black/5",
    danger: "bg-red-600 text-white hover:bg-red-700 ring-1 ring-black/5",
  };
  return (
    <button className={`${base} ${styles[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
