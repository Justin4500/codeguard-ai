import { CheckCircle2, Info, X, XCircle } from "lucide-react";
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

type ToastVariant = "success" | "error" | "info";
interface Toast {
  id: number;
  title: string;
  description?: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toast: (t: { title: string; description?: string; variant?: ToastVariant }) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((t: { title: string; description?: string; variant?: ToastVariant }) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, variant: t.variant ?? "info", title: t.title, description: t.description }]);
    setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== id)), 5200);
  }, []);

  const dismiss = (id: number) => setToasts((prev) => prev.filter((x) => x.id !== id));

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-[360px] max-w-[calc(100vw-2rem)] flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto flex items-start gap-3 rounded-lg border bg-surface px-4 py-3 shadow-xl animate-fade-in",
              t.variant === "success" && "border-emerald-500/30",
              t.variant === "error" && "border-red-500/30",
              t.variant === "info" && "border-border",
            )}
          >
            {t.variant === "success" && <CheckCircle2 className="mt-0.5 h-4 w-4 text-emerald-400" />}
            {t.variant === "error" && <XCircle className="mt-0.5 h-4 w-4 text-red-400" />}
            {t.variant === "info" && <Info className="mt-0.5 h-4 w-4 text-accent" />}
            <div className="flex-1">
              <p className="text-[13px] font-medium">{t.title}</p>
              {t.description && <p className="mt-0.5 text-[12px] text-muted">{t.description}</p>}
            </div>
            <button onClick={() => dismiss(t.id)} className="text-muted hover:text-foreground">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
