import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Bug, FolderGit2, History, ShieldAlert, ShieldCheck } from "lucide-react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router-dom";

import { PageHeader } from "@/components/common/PageHeader";
import { ScanStatusBadge, SeverityBadge } from "@/components/common/StatusBadges";
import { StatCard } from "@/components/common/StatCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState } from "@/components/ui/feedback";
import { Progress } from "@/components/ui/progress";
import { SkeletonCards, SkeletonTable } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { dashboardApi } from "@/services/endpoints";
import { formatRelative } from "@/lib/utils";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#f87171",
  high: "#fb923c",
  medium: "#fbbf24",
  low: "#60a5fa",
  informational: "#94a3b8",
};

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: dashboardApi.stats,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="A live overview of your repositories, scans and findings."
        actions={
          <Link to="/repositories">
            <Button size="sm">
              <FolderGit2 className="h-4 w-4" />
              Repositories
            </Button>
          </Link>
        }
      />

      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {isLoading && (
        <>
          <SkeletonCards count={4} />
          <Card>
            <SkeletonTable rows={4} />
          </Card>
        </>
      )}

      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Repositories" value={data.repositories} icon={FolderGit2} />
            <StatCard label="Scans run" value={data.scans} icon={History} />
            <StatCard label="Open findings" value={data.open} icon={Bug} tone={data.critical > 0 ? "critical" : "default"} />
            <StatCard label="Resolved" value={data.resolved} icon={ShieldCheck} tone="success" />
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Findings by severity</CardTitle>
              </CardHeader>
              <CardContent className="h-64">
                {data.severity_distribution.length === 0 ? (
                  <EmptyState icon={<ShieldCheck className="h-5 w-5" />} title="No findings yet" description="Run a scan to populate this chart." />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.severity_distribution} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
                      <XAxis dataKey="severity" tick={{ fill: "#8b929e", fontSize: 12 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "#8b929e", fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <Tooltip
                        cursor={{ fill: "rgba(255,255,255,0.04)" }}
                        contentStyle={{ background: "#14171c", border: "1px solid #23272e", borderRadius: 8, fontSize: 12 }}
                        labelStyle={{ color: "#e6e8eb" }}
                      />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {data.severity_distribution.map((entry) => (
                          <Cell key={entry.severity} fill={SEVERITY_COLOR[entry.severity] ?? "#4f7cff"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Severity breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {(["critical", "high", "medium", "low", "informational"] as const).map((sev) => {
                  const count = data[sev] ?? 0;
                  const total = data.findings || 1;
                  return (
                    <div key={sev} className="space-y-1.5">
                      <div className="flex items-center justify-between text-[12px]">
                        <SeverityBadge severity={sev} />
                        <span className="tabular-nums text-muted">{count}</span>
                      </div>
                      <Progress value={(count / total) * 100} className="h-1.5" />
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>Recent scans</CardTitle>
              <Link to="/scans" className="text-[13px] text-accent hover:underline">
                View all
              </Link>
            </CardHeader>
            <CardContent className="p-0 pb-1">
              {data.recent_scans.length === 0 ? (
                <EmptyState
                  icon={<History className="h-5 w-5" />}
                  title="No scans yet"
                  description="Add a repository and run your first scan to see results here."
                  action={
                    <Link to="/repositories">
                      <Button size="sm">Add a repository</Button>
                    </Link>
                  }
                />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Repository</TableHead>
                      <TableHead>Branch</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Findings</TableHead>
                      <TableHead>Started</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.recent_scans.map((scan) => (
                      <TableRow key={scan.id}>
                        <TableCell>
                          <Link to={`/scans/${scan.id}`} className="font-medium hover:text-accent">
                            {scan.repository}
                          </Link>
                        </TableCell>
                        <TableCell className="mono text-muted">{scan.branch ?? "—"}</TableCell>
                        <TableCell>
                          <ScanStatusBadge status={scan.status} />
                        </TableCell>
                        <TableCell>
                          {scan.status === "running" ? (
                            <span className="text-[12px] text-muted">{scan.stage ?? "working"} · {scan.progress}%</span>
                          ) : (
                            <span className="tabular-nums">{scan.total_findings}</span>
                          )}
                        </TableCell>
                        <TableCell className="text-[12px] text-muted">{formatRelative(scan.created_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {data.critical > 0 && (
            <Card className="border-red-500/25 bg-red-500/5">
              <CardContent className="flex items-center gap-3">
                <ShieldAlert className="h-5 w-5 text-red-400" />
                <div className="flex-1 text-[13px]">
                  <p className="font-medium text-red-300">
                    {data.critical} critical finding{data.critical === 1 ? "" : "s"} need attention
                  </p>
                  <p className="text-muted">Review and triage high-impact issues first.</p>
                </div>
                <Link to="/findings?severity=critical">
                  <Button size="sm" variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    Review
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
