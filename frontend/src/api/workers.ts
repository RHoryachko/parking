import { api } from "./client";
import type { User } from "../types";

export async function listWorkers() {
  const { data } = await api.get<User[]>("/admin/workers");
  return data;
}

export async function createWorker(body: {
  full_name: string;
  email: string;
  phone?: string | null;
  password: string;
}) {
  const { data } = await api.post<User>("/admin/workers", body);
  return data;
}

export async function updateWorker(
  workerId: number,
  body: Partial<{ full_name: string; phone: string | null; password: string }>,
) {
  const { data } = await api.patch<User>(`/admin/workers/${workerId}`, body);
  return data;
}

export async function deleteWorker(workerId: number) {
  await api.delete(`/admin/workers/${workerId}`);
}

export async function assignWorker(workerId: number, parking_id: number) {
  await api.post(`/admin/workers/${workerId}/assign`, { parking_id });
}

export async function blockWorker(workerId: number, is_blocked: boolean) {
  const { data } = await api.patch<User>(`/admin/workers/${workerId}/block`, { is_blocked });
  return data;
}
