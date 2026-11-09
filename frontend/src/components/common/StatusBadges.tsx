import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ScanStatus, Severity } from "@/types";

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  informational: "Info",
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  return (
    <Badge variant="severity" severity={severity} className={className}>
      {SEVERITY_LABEL[severity] ?? severity}
    </Badge>
  );
}

const SCAN_STATUS_STYLE: Record<string, string> = {
  queued: "bg-slate-500/15 text-slate-300 border border-slate-500/25",
  running: "bg-blue-500/15 text-blue-300 border border-blue-500/25",
  completed: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25",
  failed: "bg-red-500/15 text-red-400 border border-red-500/25",
  cancelled: "bg-amber-500/15 text-amber-400 border border-amber-500/25",
};

export function ScanStatusBadge({ status, className }: { status: ScanStatus | string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        SCAN_STATUS_STYLE[status] ?? "bg-elevated text-muted border border-border",
        className,
      )}
    >
      {status === "running" && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
      {status}
    </span>
  );
}

const FINDING_STATUS_STYLE: Record<string, string> = {
  open: "bg-orange-500/15 text-orange-400 border border-orange-500/25",
  confirmed: "bg-red-500/15 text-red-400 border border-red-500/25",
  false_positive: "bg-slate-500/15 text-slate-300 border border-slate-500/25",
  fix_proposed: "bg-blue-500/15 text-blue-300 border border-blue-500/25",
  fixed: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25",
  ignored: "bg-slate-500/15 text-slate-400 border border-slate-500/25",
};

export function FindingStatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium tracking-wide",
        FINDING_STATUS_STYLE[status] ?? "bg-elevated text-muted border border-border",
        className,
      )}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
