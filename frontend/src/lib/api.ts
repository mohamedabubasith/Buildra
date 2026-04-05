import type {
  LLMConfig,
  Project,
  Requirement,
  Architecture,
  Ticket,
  LogEntry,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${path}: ${res.status} — ${err}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Config ────────────────────────────────────────────────────────────────────
export const getConfig = () => apiFetch<LLMConfig | null>("/api/config");
export const saveConfig = (body: { api_endpoint: string; api_key: string; model: string }) =>
  apiFetch<LLMConfig>("/api/config", { method: "PUT", body: JSON.stringify(body) });

// ── Projects ──────────────────────────────────────────────────────────────────
export const getProjects = () => apiFetch<Project[]>("/api/projects");
export const createProject = (name: string) =>
  apiFetch<Project>("/api/projects", { method: "POST", body: JSON.stringify({ name }) });
export const getProject = (id: string) => apiFetch<Project>(`/api/projects/${id}`);
export const deleteProject = (id: string) =>
  apiFetch<void>(`/api/projects/${id}`, { method: "DELETE" });

// ── Workflow ──────────────────────────────────────────────────────────────────
export const submitRequirement = (projectId: string, text: string) =>
  apiFetch<Requirement>(`/api/projects/${projectId}/requirement`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });

export const answerClarification = (projectId: string, answer: string) =>
  apiFetch<Requirement>(`/api/projects/${projectId}/clarify`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });

export const getArchitecture = (projectId: string) =>
  apiFetch<Architecture | null>(`/api/projects/${projectId}/architecture`);

export const approveArchitecture = (projectId: string) =>
  apiFetch<{ message: string }>(`/api/projects/${projectId}/architecture/approve`, {
    method: "POST",
  });

// ── Tickets + Execution ───────────────────────────────────────────────────────
export const getTickets = (projectId: string) =>
  apiFetch<Ticket[]>(`/api/projects/${projectId}/tickets`);

export const executeProject = (projectId: string) =>
  apiFetch<{ message: string; task_count: number }>(`/api/projects/${projectId}/execute`, {
    method: "POST",
  });

export const getLogHistory = (projectId: string) =>
  apiFetch<LogEntry[]>(`/api/projects/${projectId}/logs/history`);

// ── SSE ───────────────────────────────────────────────────────────────────────
export const getSSEUrl = (projectId: string) =>
  `${BASE}/api/projects/${projectId}/logs`;
