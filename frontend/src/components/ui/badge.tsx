import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";
import type { Severity } from "@/types";

type Variant = "default" | "outline" | "severity" | "success" | "warning" | "danger" | "muted";

const variants: Record<Variant, string> = {
  default: "bg-elevated text-foreground border border-border",
  outline: "border border-border text-muted",
  severity: "",
  success: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  danger: "bg-red-500/10 text-red-400 border border-red-500/20",
  muted: "bg-elevated text-muted border border-border",
};

const severityClasses: Record<Severity, string> = {
  critical: "bg-red-500/15 text-red-400 border border-red-500/25",
  high: "bg-orange-500/15 text-orange-400 border border-orange-500/25",
  medium: "bg-amber-500/15 text-amber-400 border border-amber-500/25",
  low: "bg-blue-500/15 text-blue-400 border border-blue-500/25",
  informational: "bg-slate-500/15 text-slate-300 border border-slate-500/25",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
  severity?: Severity;
}

export function Badge({ className, variant = "default", severity, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        variants[variant],
        severity && severityClasses[severity],
        className,
      )}
      {...props}
    />
  );
}
