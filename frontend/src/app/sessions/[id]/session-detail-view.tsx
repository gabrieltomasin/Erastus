"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Upload, FileText, RotateCcw } from "lucide-react";
import { apiFetch, apiUpload } from "@/lib/api";
import { SessionDetail } from "@/lib/types";
import { StatusBadge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { Dropzone } from "@/components/ui/dropzone";
import { useSessionStatus } from "@/lib/hooks/use-session-status";

interface Props {
  sessionId: number;
}

export function SessionDetailView({ sessionId }: Props) {
  const { session, loading, refetch } = useSessionStatus(sessionId);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handleUpload(files: File[]) {
    setUploading(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      for (const f of files) {
        formData.append("files", f);
      }
      await apiUpload<SessionDetail>(`/sessions/${sessionId}/upload`, formData);
      await refetch();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );
  }

  if (!session) {
    return <p className="text-center py-20 text-muted-foreground">Sessão não encontrada</p>;
  }

  const canUpload = session.status === "pending" || session.status === "error";
  const hasSummary = session.final_summary || session.raw_summary;

  async function handleRetry() {
    await apiFetch(`/sessions/${sessionId}/retry`, { method: "POST" });
    await refetch();
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link
          href={`/campaigns/${session.campaign_id}`}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">#{session.session_number} — {session.title}</h1>
        </div>
        {hasSummary && (
          <Link href={`/sessions/${sessionId}/summary`}>
            <Button size="sm">
              <FileText className="h-4 w-4" />
              Editor de Resumo
            </Button>
          </Link>
        )}
        {session.status === "error" && (
          <Button variant="secondary" size="sm" onClick={handleRetry}>
            <RotateCcw className="h-4 w-4" />
            Tentar Novamente
          </Button>
        )}
        <StatusBadge status={session.status} />
      </div>

      {canUpload && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-muted-foreground mb-2">Upload de Áudio</h2>
          <Dropzone onFiles={handleUpload} disabled={uploading} />
          {uploading && (
            <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
              <Spinner className="h-4 w-4" />
              Enviando arquivos...
            </div>
          )}
          {uploadError && (
            <p className="mt-2 text-sm text-red-400">{uploadError}</p>
          )}
        </div>
      )}

      {session.audio_files && session.audio_files.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-muted-foreground mb-2">Arquivos de Áudio</h2>
          <div className="space-y-1">
            {session.audio_files.map((af, i) => (
              <div key={i} className="flex items-center gap-2 text-sm rounded-lg border border-border px-3 py-1.5">
                <span className="flex-1 truncate">{af.filename}</span>
                <span className="text-muted-foreground text-xs">
                  {(af.size / 1024 / 1024).toFixed(1)} MB
                  {af.duration ? ` • ${Math.round(af.duration / 60)} min` : ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {session.processing_logs.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-muted-foreground mb-2">Logs de Processamento</h2>
          <div className="rounded-xl border border-border bg-card p-4 space-y-1.5 font-mono text-xs">
            {session.processing_logs.map((log) => (
              <div key={log.id} className="flex gap-2">
                <span className="text-muted-foreground shrink-0">
                  {new Date(log.timestamp).toLocaleTimeString("pt-BR")}
                </span>
                <span className={log.level === "error" ? "text-red-400" : ""}>{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {session.error_message && (
        <div className="mb-6 rounded-xl border border-destructive/50 bg-destructive/10 p-4 text-sm text-red-400">
          {session.error_message}
        </div>
      )}

      {session.transcription && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-muted-foreground mb-2">Transcrição</h2>
          <div className="rounded-xl border border-border bg-card p-4 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
            {session.transcription}
          </div>
        </div>
      )}

      {session.final_summary && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-muted-foreground mb-2">Resumo</h2>
          <div className="rounded-xl border border-border bg-card p-4 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
            {session.final_summary}
          </div>
        </div>
      )}
    </div>
  );
}
