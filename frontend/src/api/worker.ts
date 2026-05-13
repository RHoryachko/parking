import { api } from "./client";
import type { ParkingSession, WorkerEntryRequest, WorkerExitRequest } from "../types";

export async function listActiveSessions(parking_id?: number) {
  const { data } = await api.get<ParkingSession[]>("/worker/sessions/active", {
    params: parking_id ? { parking_id } : undefined,
  });
  return data;
}

export async function registerEntry(body: WorkerEntryRequest) {
  const { data } = await api.post<ParkingSession>("/worker/entry", body);
  return data;
}

export async function registerExit(body: WorkerExitRequest) {
  const { data } = await api.post<ParkingSession>("/worker/exit", body);
  return data;
}

export async function barrierAction(body: { parking_id: number; action: "open" | "close"; vehicle_id?: number }) {
  const { data } = await api.post<{ ok: boolean }>("/worker/barrier", body);
  return data;
}
