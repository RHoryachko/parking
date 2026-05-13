import { api } from "./client";
import type { Tariff } from "../types";

export async function listTariffs(parkingId: number) {
  const { data } = await api.get<Tariff[]>(`/admin/parkings/${parkingId}/tariffs`);
  return data;
}

export async function createTariff(parkingId: number, price_per_hour: string) {
  const { data } = await api.post<Tariff>(`/admin/parkings/${parkingId}/tariffs`, {
    price_per_hour,
  });
  return data;
}

export async function updateTariff(parkingId: number, tariffId: number, price_per_hour: string) {
  const { data } = await api.patch<Tariff>(`/admin/parkings/${parkingId}/tariffs/${tariffId}`, {
    price_per_hour,
  });
  return data;
}

export async function deleteTariff(parkingId: number, tariffId: number) {
  await api.delete(`/admin/parkings/${parkingId}/tariffs/${tariffId}`);
}
