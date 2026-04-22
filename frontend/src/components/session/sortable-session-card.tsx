"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import Link from "next/link";
import { Trash2, GripVertical } from "lucide-react";
import { StatusBadge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { SessionBrief } from "@/lib/types";

interface Props {
  session: SessionBrief;
  onDelete: (id: number) => void;
}

export function SortableSessionCard({ session, onDelete }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: session.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style}>
      <Card className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <button
            {...attributes}
            {...listeners}
            className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground transition-colors touch-none"
          >
            <GripVertical className="h-4 w-4" />
          </button>
          <Link href={`/sessions/${session.id}`} className="flex items-center gap-3 flex-1 min-w-0">
            <span className="text-sm text-muted-foreground shrink-0">#{session.session_number}</span>
            <span className="font-medium truncate">{session.title}</span>
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={session.status} />
          <button
            onClick={(e) => { e.preventDefault(); onDelete(session.id); }}
            className="text-muted-foreground hover:text-destructive transition-colors"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </Card>
    </div>
  );
}
