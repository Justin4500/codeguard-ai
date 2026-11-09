import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Cpu, Plug, ShieldAlert, Sparkles, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/common/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, ErrorState, Spinner } from "@/components/ui/feedback";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { settingsApi } from "@/services/endpoints";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const settingsQuery = useQuery({ queryKey: ["settings"], queryFn: settingsApi.get });
  const aiStatusQuery = useQuery({ queryKey: ["ai-status"], queryFn: settingsApi.aiStatus });
  const toolsQuery = useQuery({ queryKey: ["tools"], queryFn: settingsApi.tools });

  const [aiEnabled, setAiEnabled] = useState(false);
  const [allowExternal, setAllowExternal] = useState(false);

  useEffect(() => {
    if (settingsQuery.data) {
      setAiEnabled(settingsQuery.data.ai_enabled);
      setAllowExternal(settingsQuery.data.allow_external_code);
    }
  }, [settingsQuery.data]);

  const save = useMutation({
    mutationFn: () => settingsApi.update({ ai_enabled: aiEnabled, allow_external_code: allowExternal }),
    onSuccess: () => {
      toast({ title: "Settings saved", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["ai-status"] });
    },
    onError: (err: Error) => toast({ title: "Could not save", description: err.message, variant: "error" }),
  });

  const testAi = useMutation({
    mutationFn: () => settingsApi.testAi(),
    onSuccess: (res) => toast({ title: `${res.provider} responded`, description: res.reply.slice(0, 140), variant: "success" }),
    onError: (err: Error) => toast({ title: "AI test failed", description: err.message, variant: "error" }),
  });

  const aiStatus = aiStatusQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Configure AI assistance and review scanner availability." />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>AI assistance</CardTitle>
            <CardDescription>
              CodeGuard AI works fully offline. Enable AI to add richer explanations and fix suggestions.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {settingsQuery.isError && (
              <ErrorState message={(settingsQuery.error as Error).message} onRetry={() => settingsQuery.refetch()} />
            )}

            {settingsQuery.isLoading ? (
              <Skeleton className="h-24 w-full" />
            ) : (
              <>
                <ToggleRow
                  title="Enable AI features"
                  description="Use the configured provider for explanations and fix generation."
                  checked={aiEnabled}
                  onChange={setAiEnabled}
                />
                <ToggleRow
                  title="Allow sending code to the AI provider"
                  description="Required for AI code analysis. When off, only metadata is shared. Your code is never sent without this consent."
                  checked={allowExternal}
                  onChange={setAllowExternal}
                />
                <Button size="sm" onClick={() => save.mutate()} disabled={save.isPending}>
                  {save.isPending && <Spinner />}
                  Save settings
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Provider status</CardTitle>
            <CardDescription>Configured on the backend via environment variables.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {aiStatusQuery.isLoading ? (
              <Skeleton className="h-24 w-full" />
            ) : aiStatus ? (
              <>
                <div className="flex items-center gap-3">
                  {aiStatus.ai_configured ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  ) : (
                    <XCircle className="h-5 w-5 text-muted" />
                  )}
                  <div className="text-[13px]">
                    <p className="font-medium">
                      {aiStatus.ai_configured ? `Provider: ${aiStatus.provider}` : "Offline mode"}
                    </p>
                    {aiStatus.ai_configured && <p className="text-muted">Model: {aiStatus.model}</p>}
                  </div>
                </div>
                {aiStatus.note && <Alert>{aiStatus.note}</Alert>}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => testAi.mutate()}
                  disabled={!aiStatus.ai_configured || testAi.isPending}
                >
                  {testAi.isPending ? <Spinner /> : <Plug className="h-4 w-4" />}
                  Test connection
                </Button>
              </>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Scanner availability</CardTitle>
          <CardDescription>External tools are detected at runtime. Scans run with whatever is installed.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {toolsQuery.isError && <ErrorState message={(toolsQuery.error as Error).message} onRetry={() => toolsQuery.refetch()} />}
          {toolsQuery.isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : toolsQuery.data ? (
            <>
              <div className="space-y-2">
                <p className="text-[12px] font-medium uppercase tracking-wide text-muted">Available</p>
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="success">
                    <Cpu className="h-3 w-3" />
                    {toolsQuery.data.builtin.tool}
                  </Badge>
                  {toolsQuery.data.available.map((tool) => (
                    <Badge key={tool} variant="success">
                      {tool}
                    </Badge>
                  ))}
                </div>
              </div>
              {toolsQuery.data.unavailable.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[12px] font-medium uppercase tracking-wide text-muted">Not installed (skipped)</p>
                  <div className="space-y-1.5">
                    {toolsQuery.data.unavailable.map((t) => (
                      <div key={t.tool} className="flex items-start gap-2 text-[13px]">
                        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-400/70" />
                        <span>
                          <span className="font-medium">{t.tool}</span>
                          <span className="text-muted"> — {t.purpose}</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function ToggleRow({
  title,
  description,
  checked,
  onChange,
}: {
  title: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className="flex w-full items-start justify-between gap-4 rounded-md border border-border bg-elevated px-4 py-3 text-left transition-colors hover:border-accent/40"
    >
      <div className="min-w-0">
        <p className="flex items-center gap-2 text-[13px] font-medium">
          <Sparkles className="h-3.5 w-3.5 text-accent" />
          {title}
        </p>
        <p className="mt-1 text-[12px] text-muted">{description}</p>
      </div>
      <span
        className={`relative mt-0.5 h-5 w-9 shrink-0 rounded-full transition-colors ${
          checked ? "bg-accent" : "bg-border"
        }`}
      >
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all ${
            checked ? "left-4" : "left-0.5"
          }`}
        />
      </span>
    </button>
  );
}
