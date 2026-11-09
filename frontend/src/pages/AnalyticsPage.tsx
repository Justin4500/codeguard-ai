import { useQuery } from "@tanstack/react-query";
import { BarChart3 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState } from "@/components/ui/feedback";
import { SkeletonCards } from "@/components/ui/skeleton";
import { dashboardApi } from "@/services/endpoints";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#f87171",
  high: "#fb923c",
  medium: "#fbbf24",
  low: "#60a5fa",
  informational: "#94a3b8",
};

const PALETTE = ["#4f7cff", "#22d3ee", "#a78bfa", "#34d399", "#fbbf24", "#f87171", "#94a3b8"];

const tooltipStyle = {
  background: "#14171c",
  border: "1px solid #23272e",
  borderRadius: 8,
  fontSize: 12,
} as const;

export default function AnalyticsPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["analytics"],
    queryFn: dashboardApi.analytics,
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" description="Trends and distribution across your findings." />

      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}
      {isLoading && <SkeletonCards count={4} />}

      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total findings" value={data.total_findings} />
            <StatCard label="Resolved" value={data.resolved_findings} tone="success" />
            <StatCard label="Resolution rate" value={`${Math.round(data.resolution_rate * 100)}%`} />
            <StatCard label="Languages" value={data.by_language.length} icon={BarChart3} />
          </div>

          {data.total_findings === 0 ? (
            <Card>
              <EmptyState
                icon={<BarChart3 className="h-5 w-5" />}
                title="Not enough data yet"
                description="Run scans and triage findings to build up analytics."
              />
            </Card>
          ) : (
            <>
              <div className="grid gap-4 lg:grid-cols-2">
                <ChartCard title="Findings over time">
                  <LineChart data={data.trend} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
                    <CartesianGrid stroke="#23272e" vertical={false} />
                    <XAxis dataKey="date" tick={{ fill: "#8b929e", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: "#8b929e", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: "#e6e8eb" }} />
                    <Line type="monotone" dataKey="count" stroke="#4f7cff" strokeWidth={2} dot={false} />
                  </LineChart>
                </ChartCard>

                <ChartCard title="Severity distribution">
                  <PieChart>
                    <Pie
                      data={data.by_severity}
                      dataKey="count"
                      nameKey="severity"
                      innerRadius={55}
                      outerRadius={90}
                      paddingAngle={2}
                    >
                      {data.by_severity.map((entry) => (
                        <Cell key={entry.severity} fill={SEVERITY_COLOR[entry.severity] ?? "#4f7cff"} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ChartCard>

                <ChartCard title="By category">
                  <BarChart data={data.by_category} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 24 }}>
                    <CartesianGrid stroke="#23272e" horizontal={false} />
                    <XAxis type="number" tick={{ fill: "#8b929e", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <YAxis type="category" dataKey="category" tick={{ fill: "#8b929e", fontSize: 11 }} axisLine={false} tickLine={false} width={90} />
                    <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]} fill="#4f7cff" />
                  </BarChart>
                </ChartCard>

                <ChartCard title="By repository">
                  <BarChart data={data.by_repository} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
                    <CartesianGrid stroke="#23272e" vertical={false} />
                    <XAxis dataKey="repository" tick={{ fill: "#8b929e", fontSize: 11 }} axisLine={false} tickLine={false} interval={0} angle={-12} textAnchor="end" height={50} />
                    <YAxis tick={{ fill: "#8b929e", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {data.by_repository.map((_, i) => (
                        <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ChartCard>
              </div>

              <ChartCard title="By language">
                <BarChart data={data.by_language} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
                  <CartesianGrid stroke="#23272e" vertical={false} />
                  <XAxis dataKey="language" tick={{ fill: "#8b929e", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#8b929e", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} fill="#22d3ee" />
                </BarChart>
              </ChartCard>
            </>
          )}
        </>
      )}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactElement }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
