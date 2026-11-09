import { useMutation } from "@tanstack/react-query";
import { LogOut, Mail, ShieldCheck, User as UserIcon } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/feedback";
import { Input, Label } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/hooks/useAuth";
import { authApi } from "@/services/endpoints";
import { formatDate } from "@/lib/utils";

export default function ProfilePage() {
  const { user, setUser, logout } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");

  useEffect(() => {
    if (user) {
      setUsername(user.username);
      setFullName(user.full_name ?? "");
    }
  }, [user]);

  const save = useMutation({
    mutationFn: () => authApi.updateProfile({ username: username.trim(), full_name: fullName.trim() }),
    onSuccess: (updated) => {
      setUser(updated);
      toast({ title: "Profile updated", variant: "success" });
    },
    onError: (err: Error) => toast({ title: "Could not update profile", description: err.message, variant: "error" }),
  });

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    save.mutate();
  };

  if (!user) return null;

  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Manage your account details." />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Member since" value={formatDate(user.created_at).split(",")[0]} icon={UserIcon} />
        <StatCard label="Account ID" value={user.id} />
        <StatCard label="Plan" value="Free" hint="Offline analysis included" icon={ShieldCheck} tone="success" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Account details</CardTitle>
            <CardDescription>Update your display name and username.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="profile-email">Email</Label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
                  <Input id="profile-email" value={user.email} disabled className="pl-8" />
                </div>
                <p className="text-[12px] text-muted">Email cannot be changed.</p>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="profile-username">Username</Label>
                <Input id="profile-username" minLength={3} value={username} onChange={(e) => setUsername(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="profile-name">Full name</Label>
                <Input id="profile-name" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Optional" />
              </div>
              <Button type="submit" disabled={save.isPending}>
                {save.isPending && <Spinner />}
                Save changes
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session</CardTitle>
            <CardDescription>Signing out clears your local session token.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3 rounded-md border border-border bg-elevated p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/15 text-[14px] font-semibold uppercase text-accent">
                {user.username.slice(0, 2)}
              </div>
              <div className="min-w-0">
                <p className="truncate text-[13px] font-medium">{user.full_name || user.username}</p>
                <p className="truncate text-[12px] text-muted">{user.email}</p>
              </div>
            </div>
            <Button variant="destructive" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
