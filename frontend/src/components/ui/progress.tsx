import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Progress({ value, className, ...props }: { value: number } & HTMLAttributes<HTMLDivElement>) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-elevated", className)} {...props}>
      <div
        className="h-full rounded-full bg-accent transition-all duration-500"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

export function Separator({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("h-px w-full bg-border", className)} {...props} />;
}
