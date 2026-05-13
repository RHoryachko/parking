import { api } from "./client";
import type { Parking, ParkingDetail, WorkMode } from "../types";

export async function listParkings() {
  const { data } = await api.get<Parking[]>("/admin/parkings");
  return data;
}

export async function getParking(id: number) {
  const { data } = await api.get<ParkingDetail>(`/admin/parkings/${id}`);
  return data;
}

export async function createParking(body: {
  name: string;
  city: string;
  address: string;
  capacity: number;
  latitude: number;
  longitude: number;
  work_mode?: WorkMode;
}) {
  const { data } = await api.post<Parking>("/admin/parkings", body);
  return data;
}

export async function updateParking(
  id: number,
  body: Partial<{
    name: string;
    city: string;
    address: string;
    capacity: number;
    latitude: number;
    longitude: number;
    work_mode: WorkMode;
  }>,
) {
  const { data } = await api.patch<Parking>(`/admin/parkings/${id}`, body);
  return data;
}

export async function deleteParking(id: number) {
  await api.delete(`/admin/parkings/${id}`);
}

export async function setWorkMode(id: number, work_mode: WorkMode) {
  const { data } = await api.patch<Parking>(`/admin/parkings/${id}/work-mode`, { work_mode });
  return data;
}
