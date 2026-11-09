export type Severity = "critical" | "high" | "medium" | "low" | "informational";
export type FindingStatus = "open" | "confirmed" | "false_positive" | "fix_proposed" | "fixed" | "ignored";
export type ScanStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Repository {
  id: number;
  url: string;
  full_name: string;
  owner: string;
  name: string;
  description?: string | null;
  language?: string | null;
  default_branch?: string | null;
  visibility: string;
  stars?: number | null;
  size_kb?: number | null;
  last_scanned_at?: string | null;
  created_at: string;
  scan_count: number;
  finding_count: number;
  critical_count: number;
  last_scan_status?: string | null;
}

export interface Scan {
  id: number;
  repository_id: number;
  repository_full_name?: string | null;
  branch?: string | null;
  commit_sha?: string | null;
  commit_message?: string | null;
  status: ScanStatus;
  stage?: string | null;
  progress: number;
  total_findings: number;
  files_scanned: number;
  tools_used?: string[] | null;
  tools_skipped?: { tool: string; reason: string; purpose?: string }[] | null;
  languages?: { language: string; files: number }[] | null;
  error_message?: string | null;
  ai_summary?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds?: number | null;
  created_at: string;
}

export interface Finding {
  id: number;
  scan_id: number;
  repository_id: number;
  title: string;
  description?: string | null;
  severity: Severity;
  category: string;
  file_path?: string | null;
  line_number?: number | null;
  end_line?: number | null;
  code_excerpt?: string | null;
  tool: string;
  rule_id?: string | null;
  cwe?: string | null;
  remediation?: string | null;
  confidence?: number | null;
  status: FindingStatus;
  kind: string;
  created_at: string;
}

export interface FindingList {
  items: Finding[];
  total: number;
  page: number;
  page_size: number;
  severity_counts: Record<string, number>;
}

export interface FixProposal {
  id: number;
  finding_id: number;
  file_path: string;
  language?: string | null;
  original_code: string;
  proposed_code: string;
  diff: string;
  explanation?: string | null;
  generator: string;
  status: string;
  validation_output?: string | null;
  applied_at?: string | null;
  created_at: string;
}

export interface ApproveResult {
  proposal: FixProposal;
  validation_output?: string | null;
  message: string;
}

export interface DashboardStats {
  repositories: number;
  scans: number;
  findings: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  informational: number;
  resolved: number;
  open: number;
  recent_scans: {
    id: number;
    repository_id: number;
    repository: string;
    branch?: string | null;
    status: ScanStatus;
    stage?: string | null;
    progress: number;
    total_findings: number;
    created_at?: string | null;
  }[];
  severity_distribution: { severity: string; count: number }[];
  category_distribution: { category: string; count: number }[];
  repository_activity: { repository_id: number; repository: string; findings: number }[];
}

export interface Analytics {
  by_severity: { severity: string; count: number }[];
  by_category: { category: string; count: number }[];
  by_language: { language: string; count: number }[];
  by_repository: { repository: string; count: number }[];
  trend: { date: string; count: number }[];
  resolution_rate: number;
  total_findings: number;
  resolved_findings: number;
}

export interface AppSettings {
  ai_enabled: boolean;
  ai_provider?: string | null;
  ai_base_url?: string | null;
  ai_model?: string | null;
  allow_external_code: boolean;
}

export interface ExplainResult {
  finding_id: number;
  ai_available: boolean;
  provider?: string | null;
  explanation: string;
  source: "ai" | "offline";
}

export interface ToolStatus {
  builtin: { tool: string; available: boolean; purpose: string };
  available: string[];
  unavailable: { tool: string; purpose: string }[];
}
