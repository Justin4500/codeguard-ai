import {
  Bug,
  FileSearch,
  GitBranch,
  Lock,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";

const FEATURES = [
  {
    icon: FileSearch,
    title: "Real repository scanning",
    body: "Clones your GitHub repo with Git, then runs real static analysis: built-in rules plus Ruff, Bandit, Semgrep, ESLint, npm audit and pip-audit when available.",
  },
  {
    icon: Bug,
    title: "Actionable findings",
    body: "Secrets, injection sinks, insecure crypto, SQL building and more — each finding carries severity, CWE, file, line and remediation guidance.",
  },
  {
    icon: Wrench,
    title: "Controlled fixes",
    body: "Generate a fix, review a real unified diff, approve to validate in an isolated copy, then revert at any time. Your repository is never modified or pushed.",
  },
  {
    icon: Sparkles,
    title: "Works without an API key",
    body: "A deterministic offline analyzer always produces real results. Bring your own OpenAI-compatible key (DeepSeek, Qwen, SiliconFlow, Gemini) for richer explanations.",
  },
];

const STEPS = [
  { icon: GitBranch, title: "Connect a repo", body: "Paste a GitHub URL and pick a branch." },
  { icon: ScanLine, title: "Run a scan", body: "Tools run in the background with live progress." },
  { icon: Lock, title: "Triage findings", body: "Filter by severity, confirm or mark false positives." },
  { icon: Wrench, title: "Apply fixes safely", body: "Approve diffs that validate before they land." },
];

export default function LandingPage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-accent/15 text-accent">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <span className="text-sm font-semibold">CodeGuard AI</span>
          </div>
          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <Link to="/dashboard">
                <Button size="sm">Go to dashboard</Button>
              </Link>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm">
                    Sign in
                  </Button>
                </Link>
                <Link to="/signup">
                  <Button size="sm">Get started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
        <div className="max-w-3xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-elevated px-3 py-1 text-[12px] text-muted">
            <Sparkles className="h-3.5 w-3.5 text-accent" />
            Free-first · works fully offline
          </span>
          <h1 className="mt-5 text-balance text-4xl font-semibold tracking-tight sm:text-5xl">
            Understand your code. Catch bugs before they ship.
          </h1>
          <p className="mt-5 text-[15px] leading-relaxed text-muted">
            CodeGuard AI scans real GitHub repositories with genuine static-analysis tooling, explains every
            finding, and proposes reviewable fixes — without ever modifying your repository or pushing to GitHub.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to={isAuthenticated ? "/dashboard" : "/signup"}>
              <Button size="lg">
                {isAuthenticated ? "Open dashboard" : "Start reviewing free"}
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline">
                I already have an account
              </Button>
            </Link>
          </div>
          <p className="mt-4 text-[12px] text-muted">
            No credit card. No AI key required. Optional provider key unlocks AI explanations.
          </p>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-4 pb-8 sm:px-6 lg:px-8">
        <div className="grid gap-4 sm:grid-cols-2">
          {FEATURES.map((f) => (
            <Card key={f.title} className="p-5">
              <div className="flex h-9 w-9 items-center justify-center rounded-md border border-border bg-elevated text-accent">
                <f.icon className="h-4 w-4" />
              </div>
              <h2 className="mt-4 text-sm font-semibold">{f.title}</h2>
              <p className="mt-2 text-[13px] leading-relaxed text-muted">{f.body}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2 className="text-lg font-semibold tracking-tight">How it works</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s, i) => (
            <div key={s.title} className="rounded-lg border border-border bg-surface p-5">
              <div className="flex items-center justify-between">
                <div className="flex h-9 w-9 items-center justify-center rounded-md border border-border bg-elevated text-accent">
                  <s.icon className="h-4 w-4" />
                </div>
                <span className="text-[12px] font-medium text-muted">0{i + 1}</span>
              </div>
              <h3 className="mt-4 text-sm font-semibold">{s.title}</h3>
              <p className="mt-2 text-[13px] text-muted">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-border bg-surface p-6 sm:p-8">
          <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <h2 className="text-lg font-semibold tracking-tight">Ready to review your first repository?</h2>
              <p className="mt-1 text-[13px] text-muted">
                Create a free account and run a scan in under a minute.
              </p>
            </div>
            <Link to={isAuthenticated ? "/repositories" : "/signup"}>
              <Button size="lg">Add a repository</Button>
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-6 text-[12px] text-muted sm:px-6 lg:px-8">
          <span>CodeGuard AI</span>
          <span>Built with real scanners · your code stays on your machine</span>
        </div>
      </footer>
    </div>
  );
}
