import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as parkingsApi from "../api/parkings";
import * as spotsApi from "../api/spots";
import * as tariffsApi from "../api/tariffs";
import type { ParkingDetail, ParkingSpot, SpotStatus, Tariff, WorkMode } from "../types";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Input } from "../components/Input";
import { MapPicker } from "../components/MapPicker";
import { Modal } from "../components/Modal";
import { Table } from "../components/Table";

type Tab = "spots" | "tariffs" | "settings";

function ParkingGeoEditor({
  parkingId,
  initialLat,
  initialLng,
  onSaved,
}: {
  parkingId: number;
  initialLat: number;
  initialLng: number;
  onSaved: () => Promise<void>;
}) {
  const [lat, setLat] = useState(initialLat);
  const [lng, setLng] = useState(initialLng);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setLat(initialLat);
    setLng(initialLng);
  }, [initialLat, initialLng]);

  return (
    <div className="mt-4 space-y-3">
      <MapPicker
        center={[lat, lng]}
        marker={[lat, lng]}
        onMarkerChange={(la, ln) => {
          setLat(la);
          setLng(ln);
        }}
        height={260}
        zoom={15}
      />
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[120px] flex-1">
          <label className="mb-2 block text-xs font-semibold text-zinc-600">Latitude</label>
          <Input value={String(lat)} onChange={(e) => setLat(Number(e.target.value) || 0)} />
        </div>
        <div className="min-w-[120px] flex-1">
          <label className="mb-2 block text-xs font-semibold text-zinc-600">Longitude</label>
          <Input value={String(lng)} onChange={(e) => setLng(Number(e.target.value) || 0)} />
        </div>
        <Button
          type="button"
          disabled={saving}
          onClick={async () => {
            setSaving(true);
            try {
              await parkingsApi.updateParking(parkingId, { latitude: lat, longitude: lng });
              await onSaved();
            } finally {
              setSaving(false);
            }
          }}
        >
          Save location
        </Button>
      </div>
    </div>
  );
}

export function ParkingDetailsPage() {
  const { id } = useParams();
  const parkingId = Number(id);
  const [tab, setTab] = useState<Tab>("spots");
  const [parking, setParking] = useState<ParkingDetail | null>(null);
  const [spots, setSpots] = useState<ParkingSpot[]>([]);
  const [tariffs, setTariffs] = useState<Tariff[]>([]);

  const [spotOpen, setSpotOpen] = useState(false);
  const [spotCode, setSpotCode] = useState("");

  const [tariffOpen, setTariffOpen] = useState(false);
  const [price, setPrice] = useState("50");

  const title = useMemo(() => parking?.name ?? "Parking", [parking]);

  async function reloadAll() {
    const p = await parkingsApi.getParking(parkingId);
    setParking(p);
    setSpots(await spotsApi.listSpots(parkingId));
    setTariffs(await tariffsApi.listTariffs(parkingId));
  }

  useEffect(() => {
    if (!Number.isFinite(parkingId)) return;
    reloadAll().catch(() => {});
  }, [parkingId]);

  if (!Number.isFinite(parkingId)) {
    return <div className="text-sm text-red-600">Invalid parking id.</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link className="text-sm font-semibold text-indigo-700 hover:underline" to="/admin/parkings">
            ← Back to parkings
          </Link>
          <div className="mt-2 text-2xl font-semibold tracking-tight text-zinc-900">{title}</div>
          <div className="mt-1 text-sm text-zinc-600">
            {parking?.city} · {parking?.address}
          </div>
        </div>
        <Badge tone="neutral">{parking?.work_mode ?? "…"}</Badge>
      </div>

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["spots", "Spots"],
            ["tariffs", "Tariffs"],
            ["settings", "Settings"],
          ] as const
        ).map(([k, label]) => (
          <Button
            key={k}
            type="button"
            variant={tab === k ? "primary" : "secondary"}
            onClick={() => setTab(k)}
          >
            {label}
          </Button>
        ))}
      </div>

      {tab === "spots" ? (
        <Card>
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="text-sm font-semibold text-zinc-900">Spots</div>
            <Button type="button" onClick={() => setSpotOpen(true)}>
              Add spot
            </Button>
          </div>
          <Table
            headers={["Code", "Status", ""]}
            rows={spots.map((s) => [
              <span key="c" className="font-mono font-semibold">
                {s.code}
              </span>,
              <Badge key="st" tone={s.status === "free" ? "success" : "warning"}>
                {s.status}
              </Badge>,
              <div key="a" className="flex flex-wrap gap-2">
                {(["free", "reserved", "occupied", "inactive"] as SpotStatus[]).map((st) => (
                  <Button
                    key={st}
                    type="button"
                    variant="ghost"
                    className="!px-3 !py-1 text-xs"
                    onClick={async () => {
                      await spotsApi.updateSpot(parkingId, s.id, { status: st });
                      await reloadAll();
                    }}
                  >
                    {st}
                  </Button>
                ))}
                <Button
                  type="button"
                  variant="danger"
                  className="!px-3 !py-1 text-xs"
                  onClick={async () => {
                    await spotsApi.deleteSpot(parkingId, s.id);
                    await reloadAll();
                  }}
                >
                  Delete
                </Button>
              </div>,
            ])}
          />
        </Card>
      ) : null}

      {tab === "tariffs" ? (
        <Card>
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="text-sm font-semibold text-zinc-900">Tariffs</div>
            <Button type="button" onClick={() => setTariffOpen(true)}>
              Add tariff
            </Button>
          </div>
          <Table
            headers={["ID", "Price / hour", ""]}
            rows={tariffs.map((t) => [
              String(t.id),
              `${t.price_per_hour} UAH`,
              <Button
                key="d"
                type="button"
                variant="danger"
                className="!px-3 !py-1 text-xs"
                onClick={async () => {
                  await tariffsApi.deleteTariff(parkingId, t.id);
                  await reloadAll();
                }}
              >
                Delete
              </Button>,
            ])}
          />
        </Card>
      ) : null}

      {tab === "settings" ? (
        <Card>
          <div className="text-sm font-semibold text-zinc-900">Work mode</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {(["manual", "ai"] as WorkMode[]).map((m) => (
              <Button
                key={m}
                type="button"
                variant={parking?.work_mode === m ? "primary" : "secondary"}
                onClick={async () => {
                  await parkingsApi.setWorkMode(parkingId, m);
                  await reloadAll();
                }}
              >
                {m}
              </Button>
            ))}
          </div>
          <div className="mt-8 text-sm font-semibold text-zinc-900">Map location</div>
          <div className="mt-2 text-xs text-zinc-600">Click the map to move the pin, then save coordinates.</div>
          {parking ? (
            <ParkingGeoEditor
              parkingId={parkingId}
              initialLat={parking.latitude}
              initialLng={parking.longitude}
              onSaved={reloadAll}
            />
          ) : null}
          <div className="mt-6 text-xs text-zinc-500">
            This toggles how the lot is operated in the MVP (AI endpoint vs manual worker flows).
          </div>
        </Card>
      ) : null}

      <Modal open={spotOpen} title="Add spot" onClose={() => setSpotOpen(false)}>
        <form
          className="space-y-3"
          onSubmit={async (e) => {
            e.preventDefault();
            await spotsApi.createSpot(parkingId, { code: spotCode });
            setSpotOpen(false);
            setSpotCode("");
            await reloadAll();
          }}
        >
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Code</label>
            <Input value={spotCode} onChange={(e) => setSpotCode(e.target.value)} placeholder="B1" required />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setSpotOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Modal>

      <Modal open={tariffOpen} title="Add tariff" onClose={() => setTariffOpen(false)}>
        <form
          className="space-y-3"
          onSubmit={async (e) => {
            e.preventDefault();
            await tariffsApi.createTariff(parkingId, price);
            setTariffOpen(false);
            setPrice("50");
            await reloadAll();
          }}
        >
          <div>
            <label className="mb-2 block text-xs font-semibold text-zinc-600">Price per hour</label>
            <Input value={price} onChange={(e) => setPrice(e.target.value)} required />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setTariffOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
