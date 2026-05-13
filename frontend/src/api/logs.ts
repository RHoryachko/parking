import { api } from "./client";
import type { AiLog, BarrierLog } from "../types";

export async function listBarrierLogs(params?: { parking_id?: number; skip?: number; limit?: number }) {
  const { data } = await api.get<BarrierLog[]>("/admin/logs/barrier", { params });
  return data;
}

export async function listAiLogs(params?: { parking_id?: number; skip?: number; limit?: number }) {
  const { data } = await api.get<AiLog[]>("/admin/logs/ai", { params });
  return data;
}
