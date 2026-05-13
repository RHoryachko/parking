import { api } from "./client";
import type { ParkingSpot, SpotStatus } from "../types";

export async function listSpots(parkingId: number) {
  const { data } = await api.get<ParkingSpot[]>(`/admin/parkings/${parkingId}/spots`);
  return data;
}

export async function createSpot(parkingId: number, body: { code: string; status?: SpotStatus }) {
  const { data } = await api.post<ParkingSpot>(`/admin/parkings/${parkingId}/spots`, body);
  return data;
}

export async function updateSpot(
  parkingId: number,
  spotId: number,
  body: Partial<{ code: string; status: SpotStatus }>,
) {
  const { data } = await api.patch<ParkingSpot>(
    `/admin/parkings/${parkingId}/spots/${spotId}`,
    body,
  );
  return data;
}

export async function deleteSpot(parkingId: number, spotId: number) {
  await api.delete(`/admin/parkings/${parkingId}/spots/${spotId}`);
}
