import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as parkingsApi from "../api/parkings";
import type { Parking, WorkMode } from "../types";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { MapPicker } from "../components/MapPicker";
import { Modal } from "../components/Modal";
import { Table } from "../components/Table";

const DEFAULT_LAT = 50.4501;
const DEFAULT_LNG = 30.5234;

export function ParkingsListPage() {
  const [rows, setRows] = useState<Parking[]>([]);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [address, setAddress] = useState("");
  const [capacity, setCapacity] = useState("50");
  const [workMode, setWorkMode] = useState<WorkMode>("manual");
  const [lat, setLat] = useState(DEFAULT_LAT);
  const [lng, setLng] = useState(DEFAULT_LNG);

  async function reload() {
    setRows(await parkingsApi.listParkings());
  }

  useEffect(() => {
    reload().catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm text-zinc-600">Manage lots, capacity metadata, and navigation into details.</div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Link
            to="/admin/parkings/map"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-white/80 px-5 py-2.5 text-sm font-medium text-zinc-900 ring-1 ring-black/10 backdrop-blur transition hover:bg-white active:scale-[0.98]"
          >
            Open map
          </Link>
          <Button type="button" onClick={() => setOpen(true)}>
            New parking
          </Button>
        </div>
      </div>

      <Table
        headers={["Name", "City", "Capacity", "Mode", ""]}
        rows={rows.map((p) => [
          <div key="n" className="font-medium text-zinc-900">
            {p.name}
          </div>,
          p.city,
          String(p.capacity),
          <Badge key="m" tone="neutral">
            {p.work_mode}
          </Badge>,
          <Link key="l" className="text-sm font-semibold text-indigo-700 hover:underline" to={`/admin/parkings/${p.id}`}>
            Open
          </Link>,
        ])}
      />

      <Modal open={open} title="Create parking" onClose={() => setOpen(false)}>
        <form
          className="space-y-3"
          onSubmit={async (e) => {
            e.preventDefault();
            await parkingsApi.createParking({
              name,
              city,
              address,
              capacity: Number(capacity || "1"),
              latitude: lat,
              longitude: lng,
              work_mode: workMode,
            });
            setOpen(false);
            setName("");
            setCity("");
            setAddress("");
            setCapacity("50");
            setWorkMode("manual");
            setLat(DEFAULT_LAT);
            setLng(DEFAULT_LNG);
            await reload();
          }}
        >
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-2 block text-xs font-semibold text-zinc-600">City</label>
              <Input value={city} onChange={(e) => setCity(e.target.value)} required />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold text-zinc-600">Capacity</label>
              <Input value={capacity} onChange={(e) => setCapacity(e.target.value)} inputMode="numeric" required />
            </div>
          </div>
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Address</label>
            <Input value={address} onChange={(e) => setAddress(e.target.value)} required />
          </div>
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Location on map</label>
            <MapPicker
              center={[lat, lng]}
              marker={[lat, lng]}
              onMarkerChange={(la, ln) => {
                setLat(la);
                setLng(ln);
              }}
              height={240}
            />
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              <div className="text-xs text-zinc-600">
                Lat: <span className="font-mono text-zinc-900">{lat.toFixed(6)}</span>
              </div>
              <div className="text-xs text-zinc-600">
                Lng: <span className="font-mono text-zinc-900">{lng.toFixed(6)}</span>
              </div>
            </div>
          </div>
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Work mode</label>
            <select
              className="w-full rounded-xl border border-black/10 bg-white/90 px-4 py-3 text-sm"
              value={workMode}
              onChange={(e) => setWorkMode(e.target.value as WorkMode)}
            >
              <option value="manual">manual</option>
              <option value="ai">ai</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
