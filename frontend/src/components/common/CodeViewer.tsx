import Editor, { DiffEditor, type BeforeMount } from "@monaco-editor/react";

import { cn } from "@/lib/utils";
import "@/lib/monaco-setup";

const EXT_LANG: Record<string, string> = {
  py: "python",
  js: "javascript",
  jsx: "javascript",
  ts: "typescript",
  tsx: "typescript",
  json: "json",
  yaml: "yaml",
  yml: "yaml",
  sh: "shell",
  bash: "shell",
  go: "go",
  java: "java",
  rb: "ruby",
  php: "php",
  cs: "csharp",
  c: "c",
  cpp: "cpp",
  h: "cpp",
  html: "html",
  css: "css",
  sql: "sql",
  xml: "xml",
  md: "markdown",
};

export function languageFromPath(path?: string | null): string {
  if (!path) return "plaintext";
  const ext = path.split(".").pop()?.toLowerCase() ?? "";
  return EXT_LANG[ext] ?? "plaintext";
}

const defineTheme: BeforeMount = (monaco) => {
  monaco.editor.defineTheme("codeguard", {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: {
      "editor.background": "#101318",
      "editor.lineHighlightBackground": "#14171c",
      "editorLineNumber.foreground": "#4b5159",
      "editorGutter.background": "#101318",
    },
  });
};

export function CodeViewer({
  value,
  language,
  path,
  height = 320,
  readOnly = true,
  className,
}: {
  value: string;
  language?: string;
  path?: string | null;
  height?: number | string;
  readOnly?: boolean;
  className?: string;
}) {
  return (
    <div className={cn("overflow-hidden rounded-md border border-border", className)}>
      <Editor
        height={height}
        theme="codeguard"
        beforeMount={defineTheme}
        language={language ?? languageFromPath(path)}
        value={value}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 12.5,
          fontFamily: "JetBrains Mono, ui-monospace, Consolas, monospace",
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          renderLineHighlight: readOnly ? "none" : "line",
          wordWrap: "on",
          tabSize: 2,
          padding: { top: 10, bottom: 10 },
          scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
        }}
        loading={<div className="flex h-full items-center justify-center text-[13px] text-muted">Loading editor…</div>}
      />
    </div>
  );
}

export function DiffViewer({
  original,
  modified,
  language,
  height = 360,
  className,
}: {
  original: string;
  modified: string;
  language?: string;
  height?: number | string;
  className?: string;
}) {
  return (
    <div className={cn("overflow-hidden rounded-md border border-border", className)}>
      <DiffEditor
        height={height}
        theme="codeguard"
        beforeMount={defineTheme}
        language={language ?? "plaintext"}
        original={original}
        modified={modified}
        options={{
          readOnly: true,
          renderSideBySide: true,
          minimap: { enabled: false },
          fontSize: 12.5,
          fontFamily: "JetBrains Mono, ui-monospace, Consolas, monospace",
          scrollBeyondLastLine: false,
          wordWrap: "on",
          padding: { top: 10, bottom: 10 },
          scrollbar: { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
        }}
        loading={<div className="flex h-full items-center justify-center text-[13px] text-muted">Loading diff…</div>}
      />
    </div>
  );
}
