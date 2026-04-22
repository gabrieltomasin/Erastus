"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Upload, FileText, RotateCcw, RefreshCw } from "lucide-react";
import { apiFetch, apiUpload } from "@/lib/api";
import { SessionDetail } from "@/lib/types";
import { StatusBadge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { Dropzone } from "@/components/ui/dropzone";
import { Modal } from "@/components/ui/modal";
import { useSessionStatus } from "@/lib/hooks/use-session-status";

interface Props {
  sessionId: number;
}

export function SessionDetailView({ sessionId }: Props) {
  const { session, loading, refetch } = useSessionStatus(sessionId);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [replaceMode, setReplaceMode] = useState<"reuse" | "replace">("reuse");
  const [regenerateFiles, setRegenerateFiles] = useState<File[]>([]);
  const [regenerating, setRegenerating] = useState(false);

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

  async function handleRegenerate() {
    setRegenerating(true);
    try {
      if (replaceMode === "replace" && regenerateFiles.length > 0) {
        const formData = new FormData();
        for (const f of regenerateFiles) {
          formData.append("files", f);
        }
        await apiUpload(`/sessions/${sessionId}/upload`, formData);
      }
      await apiFetch(`/sessions/${sessionId}/regenerate`, { method: "POST" });
      setShowRegenerateModal(false);
      setRegenerateFiles([]);
      await refetch();
    } catch (err) {
      console.error("Regenerate failed:", err);
    } finally {
      setRegenerating(false);
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
  const canRegenerate = session.status === "ready" || session.status === "error";

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
          <h1 className="text-2xl font-bold">{session.title}</h1>
        </div>
        {hasSummary && (
          <Link href={`/sessions/${sessionId}/summary`}>
            <Button size="sm">
              <FileText className="h-4 w-4" />
              Editor de Resumo
            </Button>
          </Link>
        )}
        {canRegenerate && (
          <Button variant="secondary" size="sm" onClick={() => setShowRegenerateModal(true)}>
            <RefreshCw className="h-4 w-4" />
            Gerar Novamente
          </Button>
        )}
        {session.status === "error" && (
          <Button variant="secondary" size="sm" onClick={handleRetry}>
            <RotateCcw className="h-4 w-4" />
            Tentar Novamente
          </Button>
        )}
        <StatusBadge status={session.status} />
      </div>

      {/* Regenerate Modal */}
      <Modal
        open={showRegenerateModal}
        onClose={() => { setShowRegenerateModal(false); setRegenerateFiles([]); }}
        title="Gerar Novamente"
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Deseja reprocessar a transcrição e o resumo desta sessão?
          </p>

          {/* Audio file reuse options */}
          {session.audio_files && session.audio_files.length > 0 && (
            <div className="space-y-3">
              <div className="text-sm font-medium">Arquivos de áudio atuais:</div>
              <div className="space-y-1">
                {session.audio_files.map((af, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm rounded-lg border border-border px-3 py-1.5">
                    <span className="flex-1 truncate">{af.filename}</span>
                    <span className="text-muted-foreground text-xs">
                      {(af.size / 1024 / 1024).toFixed(1)} MB
                    </span>
                  </div>
                ))}
              </div>

              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-3 rounded-lg border border-border p-3 cursor-pointer hover:bg-muted/50 transition-colors">
                  <input
                    type="radio"
                    name="audio-option"
                    checked={replaceMode === "reuse"}
                    onChange={() => setReplaceMode("reuse")}
                    className="accent-primary"
                  />
                  <div>
                    <div className="text-sm font-medium">Reutilizar mesmos arquivos</div>
                    <div className="text-xs text-muted-foreground">Reprocessar com os áudios já enviados</div>
                  </div>
                </label>
                <label className="flex items-center gap-3 rounded-lg border border-border p-3 cursor-pointer hover:bg-muted/50 transition-colors">
                  <input
                    type="radio"
                    name="audio-option"
                    checked={replaceMode === "replace"}
                    onChange={() => setReplaceMode("replace")}
                    className="accent-primary"
                  />
                  <div>
                    <div className="text-sm font-medium">Substituir arquivos</div>
                    <div className="text-xs text-muted-foreground">Enviar novos áudios antes de reprocessar</div>
                  </div>
                </label>
              </div>

              {replaceMode === "replace" && (
                <Dropzone onFiles={setRegenerateFiles} />
              )}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="secondary"
              onClick={() => { setShowRegenerateModal(false); setRegenerateFiles([]); }}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleRegenerate}
              disabled={regenerating || (replaceMode === "replace" && regenerateFiles.length === 0)}
            >
              {regenerating ? (
                <>
                  <Spinner className="h-4 w-4" />
                  Processando...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Gerar Novamente
                </>
              )}
            </Button>
          </div>
        </div>
      </Modal>

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
