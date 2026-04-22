import { SessionStatus } from "@/lib/types";

const statusStyles: Record<SessionStatus, string> = {
  pending: "bg-gray-500/20 text-gray-400",
  transcribing: "bg-blue-500/20 text-blue-400",
  summarizing: "bg-purple-500/20 text-purple-400",
  ready: "bg-green-500/20 text-green-400",
  error: "bg-red-500/20 text-red-400",
};

const statusLabels: Record<SessionStatus, string> = {
  pending: "Pendente",
  transcribing: "Transcrevendo",
  summarizing: "Resumindo",
  ready: "Pronto",
  error: "Erro",
};

interface StatusBadgeProps {
  status: SessionStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${statusStyles[status]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {statusLabels[status]}
    </span>
  );
}
