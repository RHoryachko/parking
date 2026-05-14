import { useEffect, useState } from "react";
import * as parkingsApi from "../api/parkings";
import * as workersApi from "../api/workers";
import type { Parking, User } from "../types";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { Modal } from "../components/Modal";
import { Table } from "../components/Table";

export function WorkersPage() {
  const [workers, setWorkers] = useState<User[]>([]);
  const [parkings, setParkings] = useState<Parking[]>([]);
  const [open, setOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState<User | null>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("worker123");
  const [assignParkingId, setAssignParkingId] = useState<number | "">("");

  async function reload() {
    setWorkers(await workersApi.listWorkers());
    setParkings(await parkingsApi.listParkings());
  }

  useEffect(() => {
    reload().catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-zinc-600">
          Create workers, assign each to exactly one parking (new assignment replaces the previous), and block access.
        </div>
        <Button type="button" onClick={() => setOpen(true)}>
          New worker
        </Button>
      </div>

      <Table
        headers={["Name", "Email", "Parking(s)", "Status", ""]}
        rows={workers.map((w) => {
          const assignedNames = (w.assigned_parking_ids ?? [])
            .map((id) => parkings.find((p) => p.id === id)?.name ?? `#${id}`)
            .join(", ");
          return [
            w.full_name,
            w.email,
            assignedNames || "—",
            <Badge key="b" tone={w.is_blocked ? "danger" : "success"}>
              {w.is_blocked ? "blocked" : "active"}
            </Badge>,
            <div key="a" className="flex flex-wrap gap-2">
              <Button type="button" variant="secondary" className="!px-3 !py-1 text-xs" onClick={() => setAssignOpen(w)}>
                Assign
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="!px-3 !py-1 text-xs"
                onClick={async () => {
                  await workersApi.blockWorker(w.id, !w.is_blocked);
                  await reload();
                }}
              >
                Toggle block
              </Button>
              <Button
                type="button"
                variant="danger"
                className="!px-3 !py-1 text-xs"
                onClick={async () => {
                  await workersApi.deleteWorker(w.id);
                  await reload();
                }}
              >
                Delete
              </Button>
            </div>,
          ];
        })}
      />

      <Modal open={open} title="Create worker" onClose={() => setOpen(false)}>
        <form
          className="space-y-3"
          onSubmit={async (e) => {
            e.preventDefault();
            await workersApi.createWorker({ full_name: fullName, email, password });
            setOpen(false);
            setFullName("");
            setEmail("");
            setPassword("worker123");
            await reload();
          }}
        >
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Full name</label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </div>
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Email</label>
            <Input value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Password</label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Modal>

      <Modal open={!!assignOpen} title="Assign worker to one parking" onClose={() => setAssignOpen(null)}>
        <form
          className="space-y-3"
          onSubmit={async (e) => {
            e.preventDefault();
            if (!assignOpen) return;
            if (assignParkingId === "") return;
            await workersApi.assignWorker(assignOpen.id, Number(assignParkingId));
            setAssignOpen(null);
            setAssignParkingId("");
            await reload();
          }}
        >
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Parking</label>
            <select
              className="w-full rounded-xl border border-black/10 bg-white/90 px-4 py-3 text-sm"
              value={assignParkingId === "" ? "" : String(assignParkingId)}
              onChange={(e) => setAssignParkingId(e.target.value ? Number(e.target.value) : "")}
              required
            >
              <option value="" disabled>
                Select…
              </option>
              {parkings.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.city})
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setAssignOpen(null)}>
              Cancel
            </Button>
            <Button type="submit">Assign</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
