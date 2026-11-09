import { api } from "@/lib/api";
import type {
  Analytics,
  AppSettings,
  ApproveResult,
  DashboardStats,
  ExplainResult,
  Finding,
  FindingList,
  FixProposal,
  Repository,
  Scan,
  TokenResponse,
  ToolStatus,
  User,
} from "@/types";

export const authApi = {
  signup: (body: { email: string; username: string; password: string; full_name?: string }) =>
    api.post<TokenResponse>("/api/auth/signup", body),
  login: (body: { email: string; password: string }) => api.post<TokenResponse>("/api/auth/login", body),
  me: () => api.get<User>("/api/auth/me"),
  updateProfile: (body: { username?: string; full_name?: string }) => api.patch<User>("/api/auth/me", body),
};

export const repoApi = {
  list: () => api.get<Repository[]>("/api/repositories"),
  get: (id: number) => api.get<Repository>(`/api/repositories/${id}`),
  create: (body: { url: string; branch?: string; access_token?: string }) =>
    api.post<Repository>("/api/repositories", body),
  remove: (id: number) => api.del<void>(`/api/repositories/${id}`),
  branches: (id: number) => api.get<{ branches: string[]; default_branch?: string }>(`/api/repositories/${id}/branches`),
};

export const scanApi = {
  start: (repoId: number, branch?: string) =>
    api.post<Scan>(`/api/repositories/${repoId}/scan${branch ? `?branch=${encodeURIComponent(branch)}` : ""}`),
  list: (params?: { repository_id?: number; status?: string }) => api.get<Scan[]>("/api/scans", params),
  get: (id: number) => api.get<Scan>(`/api/scans/${id}`),
  status: (id: number) =>
    api.get<{ id: number; status: string; stage?: string; progress: number; total_findings: number; files_scanned: number; error_message?: string | null }>(
      `/api/scans/${id}/status`,
    ),
  cancel: (id: number) => api.post<Scan>(`/api/scans/${id}/cancel`),
};

export const findingApi = {
  list: (params?: {
    repository_id?: number;
    scan_id?: number;
    severity?: string;
    category?: string;
    status?: string;
    tool?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) => api.get<FindingList>("/api/findings", params),
  get: (id: number) => api.get<Finding>(`/api/findings/${id}`),
  update: (id: number, body: { status?: string; severity?: string }) => api.patch<Finding>(`/api/findings/${id}`, body),
  explain: (id: number, question?: string) => api.post<ExplainResult>(`/api/findings/${id}/explain`, { question }),
};

export const fixApi = {
  propose: (findingId: number) => api.post<FixProposal>(`/api/findings/${findingId}/propose-fix`),
  list: (findingId: number) => api.get<FixProposal[]>(`/api/findings/${findingId}/fixes`),
  get: (id: number) => api.get<FixProposal>(`/api/fixes/${id}`),
  approve: (id: number) => api.post<ApproveResult>(`/api/fixes/${id}/approve`),
  reject: (id: number) => api.post<FixProposal>(`/api/fixes/${id}/reject`),
  revert: (id: number) => api.post<FixProposal>(`/api/fixes/${id}/revert`),
};

export const dashboardApi = {
  stats: () => api.get<DashboardStats>("/api/dashboard/stats"),
  analytics: () => api.get<Analytics>("/api/dashboard/analytics"),
};

export const settingsApi = {
  get: () => api.get<AppSettings>("/api/settings"),
  update: (body: Partial<AppSettings>) => api.patch<AppSettings>("/api/settings", body),
  aiStatus: () =>
    api.get<{ ai_configured: boolean; ai_enabled: boolean; provider?: string | null; model?: string | null; base_url?: string | null; note?: string | null }>(
      "/api/settings/ai/status",
    ),
  testAi: () => api.post<{ ok: boolean; provider: string; model: string; reply: string }>("/api/settings/ai/test"),
  tools: () => api.get<ToolStatus>("/api/tools"),
};

export function reportDownloadPath(scanId: number, format: "html" | "json" | "csv" | "pdf"): string {
  return `/api/reports/${scanId}/export?format=${format}`;
}

export function reportFilename(fullName: string, scanId: number, format: "html" | "json" | "csv" | "pdf"): string {
  return `codeguard-${fullName.replace("/", "-")}-scan${scanId}.${format}`;
}
