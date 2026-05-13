import { useEffect, useState } from "react";
import { barrierAction, listActiveSessions, registerEntry, registerExit } from "../api/worker";
import type { ParkingSession } from "../types";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Input } from "../components/Input";
import { Table } from "../components/Table";

export function WorkerSessionsPage() {
  const [sessions, setSessions] = useState<ParkingSession[]>([]);
  const [parkingId, setParkingId] = useState("1");
  const [plateNumber, setPlateNumber] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    const parking = Number(parkingId || "0");
    const data = await listActiveSessions(Number.isFinite(parking) && parking > 0 ? parking : undefined);
    setSessions(data);
  }

  useEffect(() => {
    reload().catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <Card>
        <div className="mb-4 text-sm font-semibold text-zinc-900">Start session (entry)</div>
        <form
          className="grid gap-3 md:grid-cols-3"
          onSubmit={async (e) => {
            e.preventDefault();
            setError(null);
            try {
              await registerEntry({
                parking_id: Number(parkingId),
                plate_number: plateNumber,
              });
              setPlateNumber("");
              await reload();
            } catch {
              setError("Cannot register entry. Check paid booking, plate, and assignment.");
            }
          }}
        >
          <Input value={parkingId} onChange={(e) => setParkingId(e.target.value)} placeholder="Parking ID" required />
          <Input value={plateNumber} onChange={(e) => setPlateNumber(e.target.value)} placeholder="Plate number" required />
          <Button type="submit">Register entry</Button>
        </form>
        {error ? <div className="mt-3 text-sm text-red-600">{error}</div> : null}
      </Card>

      <Card>
        <div className="mb-4 flex items-center justify-between">
          <div className="text-sm font-semibold text-zinc-900">Active sessions</div>
          <Button type="button" variant="ghost" onClick={() => reload()}>
            Refresh
          </Button>
        </div>
        <Table
          headers={["Session", "Booking", "Entry time", "Action"]}
          rows={sessions.map((s) => [
            String(s.id),
            String(s.booking_id),
            new Date(s.entry_time).toLocaleString(),
            <div key={s.id} className="flex flex-wrap gap-2">
              <Button
                type="button"
                className="!px-3 !py-1 text-xs"
                onClick={async () => {
                  await registerExit({ session_id: s.id });
                  await reload();
                }}
              >
                End session
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="!px-3 !py-1 text-xs"
                onClick={async () => {
                  await barrierAction({ parking_id: Number(parkingId), action: "open" });
                }}
              >
                Open barrier
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="!px-3 !py-1 text-xs"
                onClick={async () => {
                  await barrierAction({ parking_id: Number(parkingId), action: "close" });
                }}
              >
                Close barrier
              </Button>
            </div>,
          ])}
        />
      </Card>
    </div>
  );
}
