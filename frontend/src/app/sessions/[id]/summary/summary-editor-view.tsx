"use client";

import Link from "next/link";
import { ArrowLeft, FileText } from "lucide-react";
import { useSessionStatus } from "@/lib/hooks/use-session-status";
import { StatusBadge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { SummaryEditor } from "@/components/session/summary-editor";

interface Props {
  sessionId: number;
}

export function SummaryEditorView({ sessionId }: Props) {
  const { session, loading, refetch } = useSessionStatus(sessionId);

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

  const hasSummary = session.final_summary || session.raw_summary;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link
          href={`/sessions/${session.id}`}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="h-6 w-6 text-primary" />
            #{session.session_number} — {session.title}
          </h1>
        </div>
        <StatusBadge status={session.status} />
      </div>

      {hasSummary ? (
        <SummaryEditor session={session} onUpdate={refetch} />
      ) : (
        <div className="text-center py-20 text-muted-foreground">
          <p className="text-lg">Nenhum resumo disponível ainda</p>
          <p className="text-sm mt-1">
            {session.status === "pending"
              ? "Faça upload de áudio para gerar o resumo."
              : session.status === "error"
              ? "Ocorreu um erro no processamento. Tente novamente."
              : "O processamento ainda está em andamento."}
          </p>
        </div>
      )}
    </div>
  );
}
