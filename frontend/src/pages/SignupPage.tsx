import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { AuthShell } from "@/components/layout/AuthShell";
import { Button } from "@/components/ui/button";
import { Alert, Spinner } from "@/components/ui/feedback";
import { Input, Label } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";

export default function SignupPage() {
  const { signup, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!loading && isAuthenticated) return <Navigate to="/dashboard" replace />;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setSubmitting(true);
    try {
      await signup({
        email: email.trim(),
        username: username.trim(),
        password,
        full_name: fullName.trim() || undefined,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create your account.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell
      title="Create account"
      subtitle="Start scanning repositories in under a minute."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        {error && <Alert variant="error">{error}</Alert>}
        <div className="space-y-1.5">
          <Label htmlFor="full_name">Full name</Label>
          <Input
            id="full_name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Ada Lovelace"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="username">Username</Label>
          <Input
            id="username"
            required
            minLength={3}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="ada"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
          />
        </div>
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting && <Spinner />}
          Create account
        </Button>
      </form>
    </AuthShell>
  );
}
