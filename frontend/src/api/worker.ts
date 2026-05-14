import { api } from "./client";
import type {
  Booking,
  BookingWithPayments,
  ParkingDetail,
  ParkingSession,
  Vehicle,
  WorkerEntryRequest,
  WorkerExitRequest,
  WorkerSpotBoardItem,
  Parking,
} from "../types";

export async function listWorkerParkings() {
  const { data } = await api.get<Parking[]>("/worker/parkings");
  return data;
}

export async function getWorkerParkingDetail(parkingId: number) {
  const { data } = await api.get<ParkingDetail>(`/worker/parkings/${parkingId}`);
  return data;
}

export async function getWorkerSpotBoard(parkingId: number) {
  const { data } = await api.get<WorkerSpotBoardItem[]>(`/worker/parkings/${parkingId}/spot-board`);
  return data;
}

export async function searchVehiclesByPlate(plate: string) {
  const { data } = await api.get<Vehicle[]>("/worker/vehicles/search", { params: { plate } });
  return data;
}

export async function workerCreateBooking(body: {
  user_id: number;
  vehicle_id: number;
  parking_id: number;
  spot_id: number;
  tariff_id: number;
  planned_start_time: string;
  planned_end_time: string;
}) {
  const { data } = await api.post<BookingWithPayments>("/worker/bookings", body);
  return data;
}

export async function workerPayBooking(bookingId: number) {
  const { data } = await api.post<Booking>(`/worker/bookings/${bookingId}/pay`);
  return data;
}

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

export async function registerExitByPlate(body: WorkerEntryRequest) {
  const { data } = await api.post<ParkingSession>("/worker/exit-by-plate", body);
  return data;
}

export async function barrierAction(body: { parking_id: number; action: "open" | "close"; vehicle_id?: number }) {
  const { data } = await api.post<{ ok: boolean }>("/worker/barrier", body);
  return data;
}
