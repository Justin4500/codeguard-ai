import {
  BarChart3,
  Bug,
  FolderGit2,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  ShieldCheck,
  User as UserIcon,
  X,
} from "lucide-react";
import { useState } from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";

import { SidebarNav, type NavItem } from "@/components/layout/SidebarNav";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

export const APP_NAV: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/repositories", label: "Repositories", icon: FolderGit2 },
  { to: "/scans", label: "Scan history", icon: History },
  { to: "/findings", label: "Findings", icon: Bug },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

const ACCOUNT_NAV: NavItem[] = [
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/profile", label: "Profile", icon: UserIcon },
];

function Brand() {
  return (
    <Link to="/dashboard" className="flex items-center gap-2 px-5 py-4">
      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-accent/15 text-accent">
        <ShieldCheck className="h-5 w-5" />
      </div>
      <div className="leading-tight">
        <p className="text-sm font-semibold">CodeGuard AI</p>
        <p className="text-[11px] text-muted">Code review & bug detection</p>
      </div>
    </Link>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const sidebar = (
    <div className="flex h-full flex-col">
      <Brand />
      <div className="flex-1 overflow-y-auto pb-4">
        <SidebarNav items={APP_NAV} onNavigate={() => setMobileOpen(false)} />
        <div className="mt-4 px-3">
          <p className="px-3 pb-2 text-[11px] font-medium uppercase tracking-wide text-muted">Account</p>
          <SidebarNav items={ACCOUNT_NAV} onNavigate={() => setMobileOpen(false)} />
        </div>
      </div>
      <div className="border-t border-border p-3">
        <div className="flex items-center gap-3 rounded-md px-2 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-elevated text-[12px] font-semibold uppercase">
            {user?.username?.slice(0, 2) ?? "?"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-medium">{user?.username}</p>
            <p className="truncate text-[11px] text-muted">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-md p-1.5 text-muted hover:bg-elevated hover:text-foreground"
            title="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <aside className="hidden w-64 shrink-0 border-r border-border bg-surface md:block">{sidebar}</aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <aside className="relative z-10 h-full w-64 border-r border-border bg-surface">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-3 rounded-md p-1 text-muted hover:bg-elevated"
            >
              <X className="h-4 w-4" />
            </button>
            {sidebar}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center gap-3 border-b border-border bg-surface px-4 md:hidden">
          <Button variant="ghost" size="icon" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
            <Menu className="h-5 w-5" />
          </Button>
          <span className="text-sm font-semibold">CodeGuard AI</span>
        </header>
        <main className={cn("flex-1 overflow-y-auto")}>
          <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
