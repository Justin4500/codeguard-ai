import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderGit2, Github, Plus, RefreshCw, Star, Trash2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { PageHeader } from "@/components/common/PageHeader";
import { SeverityBadge, ScanStatusBadge } from "@/components/common/StatusBadges";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Alert, EmptyState, ErrorState, Spinner } from "@/components/ui/feedback";
import { Input, Label } from "@/components/ui/input";
import { SkeletonTable } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { repoApi, scanApi } from "@/services/endpoints";
import type { Repository } from "@/types";
import { formatRelative } from "@/lib/utils";

export default function RepositoriesPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState<Repository | null>(null);
  const [scanningId, setScanningId] = useState<number | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["repositories"],
    queryFn: repoApi.list,
  });

  const startScan = useMutation({
    mutationFn: (repo: Repository) => scanApi.start(repo.id),
    onSuccess: (scan) => {
      toast({ title: "Scan queued", description: "Tracking progress now.", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["scans"] });
      navigate(`/scans/${scan.id}`);
    },
    onError: (err: Error) => toast({ title: "Scan failed to start", description: err.message, variant: "error" }),
    onSettled: () => setScanningId(null),
  });

  const removeRepo = useMutation({
    mutationFn: (id: number) => repoApi.remove(id),
    onSuccess: () => {
      toast({ title: "Repository removed", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
      setDeleting(null);
    },
    onError: (err: Error) => toast({ title: "Delete failed", description: err.message, variant: "error" }),
  });

  const onScan = (repo: Repository) => {
    setScanningId(repo.id);
    startScan.mutate(repo);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Repositories"
        description="Connect GitHub repositories and run real scans against them."
        actions={
          <>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Button size="sm" onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4" />
              Add repository
            </Button>
          </>
        }
      />

      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {isLoading && (
        <Card>
          <SkeletonTable rows={4} />
        </Card>
      )}

      {data && data.length === 0 && (
        <Card>
          <EmptyState
            icon={<FolderGit2 className="h-5 w-5" />}
            title="No repositories yet"
            description="Add a public GitHub repository (or a private one with an access token) to begin scanning."
            action={
              <Button size="sm" onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4" />
                Add repository
              </Button>
            }
          />
        </Card>
      )}

      {data && data.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {data.map((repo) => (
            <Card key={repo.id} className="flex flex-col p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <Link to={`/repositories/${repo.id}`} className="flex items-center gap-2 text-sm font-semibold hover:text-accent">
                    <Github className="h-4 w-4 shrink-0 text-muted" />
                    <span className="truncate">{repo.full_name}</span>
                  </Link>
                  <p className="mt-1 line-clamp-2 text-[13px] text-muted">{repo.description || "No description provided."}</p>
                </div>
                {repo.last_scan_status && <ScanStatusBadge status={repo.last_scan_status} />}
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-muted">
                {repo.language && <span>{repo.language}</span>}
                <span className="flex items-center gap-1">
                  <Star className="h-3.5 w-3.5" />
                  {repo.stars ?? 0}
                </span>
                <span className="mono">{repo.default_branch ?? "main"}</span>
                <span>Last scan {formatRelative(repo.last_scanned_at)}</span>
              </div>

              <div className="mt-4 flex items-center gap-2 text-[12px]">
                <span className="text-muted">Findings</span>
                <span className="tabular-nums font-medium">{repo.finding_count}</span>
                {repo.critical_count > 0 && <SeverityBadge severity="critical" />}
              </div>

              <div className="mt-auto flex items-center gap-2 pt-5">
                <Button size="sm" onClick={() => onScan(repo)} disabled={scanningId === repo.id}>
                  {scanningId === repo.id ? <Spinner /> : <RefreshCw className="h-4 w-4" />}
                  Scan now
                </Button>
                <Link to={`/repositories/${repo.id}`}>
                  <Button size="sm" variant="outline">
                    Details
                  </Button>
                </Link>
                <Link to={`/findings?repository_id=${repo.id}`}>
                  <Button size="sm" variant="ghost">
                    Findings
                  </Button>
                </Link>
                <Button
                  size="icon"
                  variant="ghost"
                  className="ml-auto text-muted hover:text-red-400"
                  onClick={() => setDeleting(repo)}
                  title="Remove repository"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <AddRepositoryDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />

      <Dialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        title="Remove repository"
        description={`This deletes "${deleting?.full_name}" and all of its scans and findings. This cannot be undone.`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleting(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={() => deleting && removeRepo.mutate(deleting.id)} disabled={removeRepo.isPending}>
              {removeRepo.isPending && <Spinner />}
              Remove
            </Button>
          </>
        }
      />
    </div>
  );
}

function AddRepositoryDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [url, setUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () =>
      repoApi.create({
        url: url.trim(),
        branch: branch.trim() || undefined,
        access_token: token.trim() || undefined,
      }),
    onSuccess: (repo) => {
      toast({ title: "Repository added", description: repo.full_name, variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
      setUrl("");
      setBranch("");
      setToken("");
      setError(null);
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    create.mutate();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Add repository"
      description="Paste a GitHub repository URL. Private repos require a read-only access token."
    >
      <form onSubmit={onSubmit} className="space-y-4" id="add-repo-form">
        {error && <Alert variant="error">{error}</Alert>}
        <div className="space-y-1.5">
          <Label htmlFor="repo-url">Repository URL</Label>
          <Input
            id="repo-url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="repo-branch">Branch (optional)</Label>
          <Input id="repo-branch" value={branch} onChange={(e) => setBranch(e.target.value)} placeholder="defaults to the repository default branch" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="repo-token">Access token (optional)</Label>
          <Input
            id="repo-token"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="ghp_… for private repositories"
          />
          <p className="text-[12px] text-muted">
            Stored only on your server and never returned to the browser. Used solely to clone the repository.
          </p>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending && <Spinner />}
            Add repository
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
