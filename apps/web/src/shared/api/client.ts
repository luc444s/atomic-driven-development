import { useAuthStore } from "../../features/auth/store";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export type PluginManifest = {
  id: string;
  name: string;
  version: string;
  api_version: string;
  requires: string[];
  backend_entrypoint: string;
  frontend_entrypoint: string;
  permissions: string[];
  events: string[];
  description: string;
};

export type PluginRuntimeRecord = {
  id: string;
  plugin_id: string;
  name: string;
  version: string;
  api_version: string;
  state: string;
  is_enabled: boolean;
  backend_entrypoint: string | null;
  frontend_entrypoint: string | null;
  requires_json: string[];
  permissions_json: string[];
  events_json: string[];
  description: string | null;
  migration_version: string | null;
  installed_at: string | null;
  enabled_at: string | null;
  disabled_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

function buildUrl(path: string) {
  return `${getApiBaseUrl()}${path}`;
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const token = useAuthStore.getState().token;
  const headers = new Headers(init?.headers);
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;

  if (!headers.has("Content-Type") && init?.body && !isFormData) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(buildUrl(path), {
    ...init,
    headers,
  });

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    const message =
      payload?.detail ?? payload?.error?.message ?? `HTTP ${response.status} al consultar la API`;
    throw new ApiError(String(message), response.status);
  }

  return payload as T;
}
