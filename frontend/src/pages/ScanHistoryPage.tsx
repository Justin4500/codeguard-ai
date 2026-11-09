import { useQuery } from "@tanstack/react-query";
import { History, RefreshCw } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { PageHeader } from "@/components/common/PageHeader";
import { ScanStatusBadge } from "@/components/common/StatusBadges";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState, ErrorState } from "@/components/ui/feedback";
import { Select } from "@/components/ui/input";
import { SkeletonTable } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { repoApi, scanApi } from "@/services/endpoints";
import { duration, formatRelative, shortSha } from "@/lib/utils";

const STATUSES = ["queued", "running", "completed", "failed", "cancelled"];

export default function ScanHistoryPage() {
  const [repositoryId, setRepositoryId] = useState("");
  const [status, setStatus] = useState("");

  const reposQuery = useQuery({ queryKey: ["repositories"], queryFn: repoApi.list });

  const scansQuery = useQuery({
    queryKey: ["scans", { repository_id: repositoryId, status }],
    queryFn: () =>
      scanApi.list({
        repository_id: repositoryId ? Number(repositoryId) : undefined,
        status: status || undefined,
      }),
    refetchInterval: (query) => {
      const hasActive = query.state.data?.some((s) => s.status === "running" || s.status === "queued");
      return hasActive ? 2000 : false;
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scan history"
        description="Every scan across all of your repositories."
        actions={
          <>
            <Select value={repositoryId} onChange={(e) => setRepositoryId(e.target.value)} className="w-48">
              <option value="">All repositories</option>
              {reposQuery.data?.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.full_name}
                </option>
              ))}
            </Select>
            <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-36">
              <option value="">Any status</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
            <Button variant="outline" size="sm" onClick={() => scansQuery.refetch()}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </>
        }
      />

      {scansQuery.isError && (
        <ErrorState message={(scansQuery.error as Error).message} onRetry={() => scansQuery.refetch()} />
      )}

      <Card>
        {scansQuery.isLoading ? (
          <SkeletonTable rows={6} />
        ) : !scansQuery.data || scansQuery.data.length === 0 ? (
          <EmptyState
            icon={<History className="h-5 w-5" />}
            title="No scans found"
            description="Run a scan from a repository page to populate your history."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Scan</TableHead>
                <TableHead>Repository</TableHead>
                <TableHead>Branch</TableHead>
                <TableHead>Commit</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Findings</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Started</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {scansQuery.data.map((scan) => (
                <TableRow key={scan.id}>
                  <TableCell>
                    <Link to={`/scans/${scan.id}`} className="font-medium hover:text-accent">
                      #{scan.id}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Link to={`/repositories/${scan.repository_id}`} className="hover:text-accent">
                      {scan.repository_full_name ?? `Repository #${scan.repository_id}`}
                    </Link>
                  </TableCell>
                  <TableCell className="mono text-muted">{scan.branch ?? "—"}</TableCell>
                  <TableCell className="mono text-muted">{shortSha(scan.commit_sha)}</TableCell>
                  <TableCell>
                    <ScanStatusBadge status={scan.status} />
                  </TableCell>
                  <TableCell className="tabular-nums">{scan.total_findings}</TableCell>
                  <TableCell className="text-[12px] text-muted">{duration(scan.duration_seconds)}</TableCell>
                  <TableCell className="text-[12px] text-muted">{formatRelative(scan.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
