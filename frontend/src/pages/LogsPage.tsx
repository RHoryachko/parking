import { useEffect, useState } from "react";
import * as logsApi from "../api/logs";
import type { AiLog, BarrierLog } from "../types";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Table } from "../components/Table";

type Tab = "barrier" | "ai";

export function LogsPage() {
  const [tab, setTab] = useState<Tab>("barrier");
  const [barrier, setBarrier] = useState<BarrierLog[]>([]);
  const [ai, setAi] = useState<AiLog[]>([]);

  async function reload() {
    setBarrier(await logsApi.listBarrierLogs({ limit: 100 }));
    setAi(await logsApi.listAiLogs({ limit: 100 }));
  }

  useEffect(() => {
    reload().catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant={tab === "barrier" ? "primary" : "secondary"} onClick={() => setTab("barrier")}>
          Barrier logs
        </Button>
        <Button type="button" variant={tab === "ai" ? "primary" : "secondary"} onClick={() => setTab("ai")}>
          AI logs
        </Button>
        <Button type="button" variant="ghost" onClick={() => reload()}>
          Refresh
        </Button>
      </div>

      {tab === "barrier" ? (
        <Card>
          <div className="mb-3 text-sm font-semibold text-zinc-900">Barrier</div>
          <Table
            headers={["Time", "Parking", "Worker", "Vehicle", "Action"]}
            rows={barrier.map((l) => [
              new Date(l.created_at).toLocaleString(),
              String(l.parking_id),
              l.worker_id ? String(l.worker_id) : "—",
              l.vehicle_id ? String(l.vehicle_id) : "—",
              <Badge key="a" tone="neutral">
                {l.action}
              </Badge>,
            ])}
          />
        </Card>
      ) : (
        <Card>
          <div className="mb-3 text-sm font-semibold text-zinc-900">AI</div>
          <Table
            headers={["Time", "Parking", "Plate", "Vehicle", "Allowed"]}
            rows={ai.map((l) => [
              new Date(l.created_at).toLocaleString(),
              String(l.parking_id),
              <span key="p" className="font-mono">
                {l.recognized_plate}
              </span>,
              l.vehicle_id ? String(l.vehicle_id) : "—",
              <Badge key="al" tone={l.access_allowed ? "success" : "danger"}>
                {String(l.access_allowed)}
              </Badge>,
            ])}
          />
        </Card>
      )}
    </div>
  );
}
