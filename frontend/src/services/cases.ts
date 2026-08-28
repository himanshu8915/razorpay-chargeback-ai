import { apiFetch } from "./api";

export interface HealthResponse {
  status: string;
}

export interface ReadyResponse {
  status: string;
  database: string;
}

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function getReady(): Promise<ReadyResponse> {
  return apiFetch<ReadyResponse>("/ready");
}
