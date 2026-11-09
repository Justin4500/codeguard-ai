import type { LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  hint,
  tone = "default",
}: {
  label: string;
  value: number | string;
  icon?: LucideIcon;
  hint?: string;
  tone?: "default" | "critical" | "high" | "medium" | "low" | "success";
}) {
  const toneClass = {
    default: "text-foreground",
    critical: "text-red-400",
    high: "text-orange-400",
    medium: "text-amber-400",
    low: "text-blue-400",
    success: "text-emerald-400",
  }[tone];

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[12px] font-medium uppercase tracking-wide text-muted">{label}</p>
          <p className={cn("mt-2 text-2xl font-semibold tabular-nums", toneClass)}>{value}</p>
          {hint && <p className="mt-1 text-[12px] text-muted">{hint}</p>}
        </div>
        {Icon && (
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border bg-elevated text-muted">
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>
    </Card>
  );
}
