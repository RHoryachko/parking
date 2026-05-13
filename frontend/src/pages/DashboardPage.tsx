import { useEffect, useState } from "react";
import { fetchStats } from "../api/stats";
import type { AdminStats } from "../types";
import { Badge } from "../components/Badge";
import { Card } from "../components/Card";

export function DashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setStats(await fetchStats());
      } catch {
        setError("Could not load stats.");
      }
    })();
  }, []);

  if (error) {
    return <div className="text-sm text-red-600">{error}</div>;
  }

  if (!stats) {
    return <div className="text-sm text-zinc-600">Loading stats…</div>;
  }

  const items = [
    { label: "Parkings", value: stats.parkings_count, hint: "Total configured lots" },
    { label: "Spots", value: stats.spots_total, hint: "Across all parkings" },
    { label: "Bookings", value: stats.bookings_total, hint: "All time" },
    { label: "Active sessions", value: stats.active_sessions, hint: "Cars inside now" },
    { label: "Revenue today", value: `${stats.revenue_today} UAH`, hint: "Paid payments (mock)" },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((it) => (
        <Card key={it.label}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">{it.label}</div>
              <div className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900">{it.value}</div>
              <div className="mt-2 text-sm text-zinc-600">{it.hint}</div>
            </div>
            <Badge tone="neutral">Live</Badge>
          </div>
        </Card>
      ))}
    </div>
  );
}
