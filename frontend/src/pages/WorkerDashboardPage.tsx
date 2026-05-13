import { useEffect, useState } from "react";
import { listActiveSessions } from "../api/worker";
import { Card } from "../components/Card";

export function WorkerDashboardPage() {
  const [activeCount, setActiveCount] = useState<number>(0);

  useEffect(() => {
    (async () => {
      try {
        const sessions = await listActiveSessions();
        setActiveCount(sessions.length);
      } catch {
        setActiveCount(0);
      }
    })();
  }, []);

  return (
    <Card>
      <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Worker overview</div>
      <div className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900">{activeCount}</div>
      <div className="mt-2 text-sm text-zinc-600">Active sessions available for your assigned parkings.</div>
    </Card>
  );
}
