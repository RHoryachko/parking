import { api } from "./client";
import type { AdminStats } from "../types";

export async function fetchStats() {
  const { data } = await api.get<AdminStats>("/admin/stats");
  return data;
}
