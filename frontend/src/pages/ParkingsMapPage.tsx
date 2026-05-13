import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import iconUrl from "leaflet/dist/images/marker-icon.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";
import * as parkingsApi from "../api/parkings";
import type { Parking } from "../types";

// Fix default marker icons with Vite bundling
delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: boolean })._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl });

export function ParkingsMapPage() {
  const [rows, setRows] = useState<Parking[]>([]);

  useEffect(() => {
    parkingsApi.listParkings().then(setRows).catch(() => setRows([]));
  }, []);

  const center = useMemo((): [number, number] => {
    if (!rows.length) return [50.4501, 30.5234];
    const lat = rows.reduce((s, p) => s + p.latitude, 0) / rows.length;
    const lng = rows.reduce((s, p) => s + p.longitude, 0) / rows.length;
    return [lat, lng];
  }, [rows]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link className="text-sm font-semibold text-indigo-700 hover:underline" to="/admin/parkings">
            ← Back to list
          </Link>
          <div className="mt-2 text-2xl font-semibold tracking-tight text-zinc-900">Parkings map</div>
          <div className="mt-1 text-sm text-zinc-600">All lots with coordinates from the catalog.</div>
        </div>
      </div>
      <div className="h-[min(70vh,560px)] overflow-hidden rounded-2xl border border-black/10 shadow-sm">
        <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }} scrollWheelZoom>
          <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {rows.map((p) => (
            <Marker key={p.id} position={[p.latitude, p.longitude]}>
              <Popup>
                <div className="space-y-1 text-sm">
                  <div className="font-semibold">{p.name}</div>
                  <div>
                    {p.city} · {p.address}
                  </div>
                  <Link className="font-semibold text-indigo-700 hover:underline" to={`/admin/parkings/${p.id}`}>
                    Open details
                  </Link>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
