import { useEffect, useState } from "react";
import { listActiveSessions, listWorkerParkings } from "../api/worker";
import type { Parking } from "../types";
import { Card } from "../components/Card";

export function WorkerDashboardPage() {
  const [activeCount, setActiveCount] = useState<number>(0);
  const [parkings, setParkings] = useState<Parking[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const [sessions, plist] = await Promise.all([listActiveSessions(), listWorkerParkings()]);
        setActiveCount(sessions.length);
        setParkings(plist);
      } catch {
        setActiveCount(0);
        setParkings([]);
      }
    })();
  }, []);

  return (
    <div className="space-y-4">
      <Card>
        <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Worker overview</div>
        <div className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900">{activeCount}</div>
        <div className="mt-2 text-sm text-zinc-600">Active sessions on your assigned parking(s).</div>
      </Card>
      <Card>
        <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Your parking</div>
        {parkings.length === 0 ? (
          <div className="mt-2 text-sm text-zinc-600">No parking assigned yet. Ask an admin to assign you in Workers.</div>
        ) : (
          <ul className="mt-3 list-inside list-disc text-sm text-zinc-800">
            {parkings.map((p) => (
              <li key={p.id}>
                {p.name} — {p.city} (#{p.id})
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
