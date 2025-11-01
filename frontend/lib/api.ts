import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000",
});

export type Session = {
  id: string;
  created_at?: string;
  updated_at?: string;
  status: string;
  has_transcript: boolean;
  title?: string;
};

export async function createSession() {
  const { data } = await api.post("/api/sessions");
  return data as { id: string; websocket_url: string; created_at: string };
}

export async function finalizeSession(id: string) {
  const { data } = await api.post(`/api/sessions/${id}/finalize`);
  return data as {
    id: string;
    status: string;
    transcript: string;
    summary: Record<string, unknown>;
    title?: string;
  };
}

export async function listSessions() {
  const { data } = await api.get("/api/sessions");
  return data as Session[];
}

export async function fetchSettings() {
  const { data } = await api.get("/api/settings");
  return data as { data: any };
}

export async function updateSettings(payload: any) {
  const { data } = await api.put("/api/settings", payload);
  return data as { data: any };
}

