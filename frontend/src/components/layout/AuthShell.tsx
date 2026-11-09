import { ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-6 flex items-center justify-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent/15 text-accent">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <span className="text-base font-semibold">CodeGuard AI</span>
        </Link>
        <div className="rounded-lg border border-border bg-surface p-6">
          <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
          <p className="mt-1 text-[13px] text-muted">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </div>
        <div className="mt-4 text-center text-[13px] text-muted">{footer}</div>
      </div>
    </div>
  );
}
