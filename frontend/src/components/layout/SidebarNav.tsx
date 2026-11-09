import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";

export interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  end?: boolean;
}

export function SidebarNav({ items, onNavigate }: { items: NavItem[]; onNavigate?: () => void }) {
  return (
    <nav className="flex flex-1 flex-col gap-1 px-3">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-[13px] font-medium transition-colors",
              isActive ? "bg-accent/15 text-accent" : "text-muted hover:bg-elevated hover:text-foreground",
            )
          }
        >
          <item.icon className="h-4 w-4 shrink-0" />
          <span className="truncate">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
