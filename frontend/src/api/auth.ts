import { api, setToken } from "./client";
import type { User } from "../types";

export async function login(email: string, password: string) {
  const { data } = await api.post<{ access_token: string; token_type: string }>(
    "/auth/login",
    { email, password },
  );
  setToken(data.access_token);
  return data.access_token;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export function logout() {
  setToken(null);
}
