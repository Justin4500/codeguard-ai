import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Alert({
  variant = "default",
  className,
  children,
  ...props
}: { variant?: "default" | "error" | "warning" | "success" } & HTMLAttributes<HTMLDivElement>) {
  const styles = {
    default: "border-border bg-elevated text-foreground",
    error: "border-red-500/30 bg-red-500/10 text-red-300",
    warning: "border-amber-500/30 bg-amber-500/10 text-amber-200",
    success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
  }[variant];
  return (
    <div className={cn("rounded-md border px-4 py-3 text-[13px]", styles, className)} {...props}>
      {children}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 px-6 py-16 text-center", className)}>
      {icon && <div className="flex h-11 w-11 items-center justify-center rounded-full border border-border bg-elevated text-muted">{icon}</div>}
      <div>
        <p className="text-sm font-medium">{title}</p>
        {description && <p className="mt-1 max-w-md text-[13px] text-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
      <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-[13px] text-red-300">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="text-[13px] text-accent hover:underline">
          Try again
        </button>
      )}
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent align-[-2px]",
        className,
      )}
    />
  );
}
