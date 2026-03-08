const BASE = "";

export async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`);
  return res.json();
}

export async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path}: ${res.status}`);
  return res.json();
}

export interface Device {
  udid: string;
  name: string;
  model: string;
  ios_version: string;
  status: string;
  last_seen: string;
}

export interface Task {
  id: number;
  name: string;
  script_name: string;
  status: string;
  device_udid: string | null;
  result: string | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export function connectWebSocket(onMessage: (event: unknown) => void): WebSocket {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
}
