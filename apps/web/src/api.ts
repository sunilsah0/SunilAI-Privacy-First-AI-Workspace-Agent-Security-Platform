let token: string | null = null;            // memory only. Gone after a page refresh.
let onUnauthorized: (() => void) | null = null;

export function setToken(t: string | null) { token = t; }
export function setUnauthorizedHandler(fn: () => void) { onUnauthorized = fn; }

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function errorText(e: unknown): string {
  return e instanceof ApiError ? e.message : "Could not reach the server. Is the API running?";
}

type Options = { method?: string; body?: unknown; form?: FormData };

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let body: BodyInit | undefined;
  if (options.form) {
    body = options.form;                    // the browser sets the upload header itself
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }

  const res = await fetch(`/api${path}`, { method: options.method ?? "GET", headers, body });
  if (res.status === 401 && token && onUnauthorized) onUnauthorized();   // expired login
  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data && typeof data.detail === "string" ? data.detail : "Please check your input";
    throw new ApiError(res.status, detail);
  }
  return data as T;
}