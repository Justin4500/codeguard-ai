import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const base =
  "w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted/70 " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 disabled:opacity-50";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => <input ref={ref} className={cn(base, "h-9", className)} {...props} />,
);
Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => <textarea ref={ref} className={cn(base, "min-h-[90px]", className)} {...props} />,
);
Textarea.displayName = "Textarea";

export function Label({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn("text-[13px] font-medium text-foreground/90", className)} {...props} />;
}

export const Select = forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select ref={ref} className={cn(base, "h-9 cursor-pointer appearance-none pr-8", className)} {...props}>
      {children}
    </select>
  ),
);
Select.displayName = "Select";
