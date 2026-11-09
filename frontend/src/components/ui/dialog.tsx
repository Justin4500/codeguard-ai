import { X } from "lucide-react";
import { useEffect, type ReactNode } from "react";

import { cn } from "@/lib/utils";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  className?: string;
}

export function Dialog({ open, onClose, title, description, children, footer, className }: DialogProps) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 sm:p-8">
      <div
        className="absolute inset-0"
        aria-hidden
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        className={cn(
          "relative z-10 my-8 w-full max-w-xl animate-fade-in rounded-lg border border-border bg-surface shadow-2xl",
          className,
        )}
      >
        <div className="flex items-start justify-between gap-4 border-b border-border px-5 py-4">
          <div>
            {title && <h2 className="text-sm font-semibold">{title}</h2>}
            {description && <p className="mt-1 text-[13px] text-muted">{description}</p>}
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted transition-colors hover:bg-elevated hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        {children && <div className="px-5 py-4">{children}</div>}
        {footer && <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">{footer}</div>}
      </div>
    </div>
  );
}
