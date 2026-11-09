import { forwardRef, type ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type Variant = "default" | "secondary" | "outline" | "ghost" | "destructive" | "success";
type Size = "default" | "sm" | "lg" | "icon";

const variants: Record<Variant, string> = {
  default: "bg-accent text-accent-foreground hover:bg-accent/90 shadow-sm",
  secondary: "bg-elevated text-foreground hover:bg-elevated/80 border border-border",
  outline: "border border-border bg-transparent hover:bg-elevated",
  ghost: "bg-transparent hover:bg-elevated",
  destructive: "bg-red-600 text-white hover:bg-red-600/90",
  success: "bg-emerald-600 text-white hover:bg-emerald-600/90",
};

const sizes: Record<Size, string> = {
  default: "h-9 px-4 text-sm",
  sm: "h-8 px-3 text-[13px]",
  lg: "h-11 px-6 text-sm",
  icon: "h-9 w-9",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
