import { useQuery } from "@tanstack/react-query";
import { Bug, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { PageHeader } from "@/components/common/PageHeader";
import { FindingStatusBadge, SeverityBadge } from "@/components/common/StatusBadges";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState, ErrorState } from "@/components/ui/feedback";
import { Input, Select } from "@/components/ui/input";
import { SkeletonTable } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { findingApi, repoApi } from "@/services/endpoints";
import type { Severity } from "@/types";

const SEVERITIES: Severity[] = ["critical", "high", "medium", "low", "informational"];
const STATUSES = ["open", "confirmed", "false_positive", "fix_proposed", "fixed", "ignored"];
const PAGE_SIZE = 20;

export default function FindingsPage() {
  const [params, setParams] = useSearchParams();

  const [severity, setSeverity] = useState(params.get("severity") ?? "");
  const [status, setStatus] = useState(params.get("status") ?? "");
  const [repositoryId, setRepositoryId] = useState(params.get("repository_id") ?? "");
  const [search, setSearch] = useState(params.get("search") ?? "");
  const [searchInput, setSearchInput] = useState(params.get("search") ?? "");
  const [page, setPage] = useState(1);

  const scanId = params.get("scan_id") ? Number(params.get("scan_id")) : undefined;

  // Keep the URL in sync so views can be shared / linked from other pages.
  useEffect(() => {
    const next = new URLSearchParams();
    if (severity) next.set("severity", severity);
    if (status) next.set("status", status);
    if (repositoryId) next.set("repository_id", repositoryId);
    if (search) next.set("search", search);
    if (scanId) next.set("scan_id", String(scanId));
    setParams(next, { replace: true });
    setPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [severity, status, repositoryId, search, scanId]);

  const reposQuery = useQuery({ queryKey: ["repositories"], queryFn: repoApi.list });

  const findingsQuery = useQuery({
    queryKey: ["findings", { severity, status, repositoryId, search, scanId, page }],
    queryFn: () =>
      findingApi.list({
        severity: severity || undefined,
        status: status || undefined,
        repository_id: repositoryId ? Number(repositoryId) : undefined,
        scan_id: scanId,
        search: search || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  const data = findingsQuery.data;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const repoNameById = useMemo(() => {
    const map = new Map<number, string>();
    reposQuery.data?.forEach((r) => map.set(r.id, r.full_name));
    return map;
  }, [reposQuery.data]);

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput.trim());
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Findings"
        description={data ? `${data.total} finding${data.total === 1 ? "" : "s"} matching your filters.` : "All findings across your scans."}
        actions={
          <form onSubmit={submitSearch} className="flex items-center gap-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
              <Input
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search title, file, rule…"
                className="w-56 pl-8"
              />
            </div>
            <Button type="submit" size="sm" variant="outline">
              Search
            </Button>
          </form>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <Select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="w-40"
        >
          <option value="">All severities</option>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </Select>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-40">
          <option value="">Any status</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace(/_/g, " ")}
            </option>
          ))}
        </Select>
        <Select value={repositoryId} onChange={(e) => setRepositoryId(e.target.value)} className="w-52">
          <option value="">All repositories</option>
          {reposQuery.data?.map((r) => (
            <option key={r.id} value={r.id}>
              {r.full_name}
            </option>
          ))}
        </Select>
        {scanId && (
          <span className="rounded-full border border-border bg-elevated px-3 py-1 text-[12px] text-muted">
            Scan #{scanId} ·{" "}
            <button className="text-accent hover:underline" onClick={() => setParams(new URLSearchParams(severity ? { severity } : {}))}>
              clear
            </button>
          </span>
        )}
      </div>

      {findingsQuery.isError && (
        <ErrorState message={(findingsQuery.error as Error).message} onRetry={() => findingsQuery.refetch()} />
      )}

      <Card className="overflow-hidden">
        {findingsQuery.isLoading ? (
          <SkeletonTable rows={8} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            icon={<Bug className="h-5 w-5" />}
            title="No findings match"
            description="Try relaxing your filters, or run a new scan."
          />
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Severity</TableHead>
                  <TableHead>Finding</TableHead>
                  <TableHead>Repository</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Tool</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((f) => (
                  <TableRow key={f.id}>
                    <TableCell>
                      <SeverityBadge severity={f.severity} />
                    </TableCell>
                    <TableCell className="max-w-md">
                      <Link to={`/findings/${f.id}`} className="font-medium hover:text-accent">
                        {f.title}
                      </Link>
                      {f.rule_id && <span className="ml-2 text-[11px] text-muted">{f.rule_id}</span>}
                    </TableCell>
                    <TableCell className="text-[12px] text-muted">
                      {repoNameById.get(f.repository_id) ?? `#${f.repository_id}`}
                    </TableCell>
                    <TableCell className="mono max-w-xs truncate text-muted" title={f.file_path ?? undefined}>
                      {f.file_path ?? "—"}
                      {f.line_number ? `:${f.line_number}` : ""}
                    </TableCell>
                    <TableCell className="text-[12px] text-muted">{f.tool}</TableCell>
                    <TableCell>
                      <FindingStatusBadge status={f.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t border-border px-5 py-3">
                <span className="text-[12px] text-muted">
                  Page {data.page} of {totalPages}
                </span>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                    <ChevronLeft className="h-4 w-4" />
                    Prev
                  </Button>
                  <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
