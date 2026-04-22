"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import Link from "next/link";
import { useState } from "react";
import { Trash2, GripVertical, Pencil, Check, X } from "lucide-react";
import { StatusBadge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { SessionBrief } from "@/lib/types";

interface Props {
  session: SessionBrief;
  onDelete: (id: number) => void;
  onRename: (id: number, newTitle: string) => void;
}

export function SortableSessionCard({ session, onDelete, onRename }: Props) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(session.title);

  async function handleSave() {
    if (!title.trim()) return;
    try {
      await apiFetch(`/sessions/${session.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim() }),
      });
      onRename(session.id, title.trim());
      setEditing(false);
    } catch {
      setTitle(session.title);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") handleSave();
    if (e.key === "Escape") { setTitle(session.title); setEditing(false); }
  }
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
          {editing ? (
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 min-w-0 rounded border border-border bg-background px-2 py-0.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/50"
                autoFocus
              />
              <button onClick={handleSave} className="text-green-500 hover:text-green-400">
                <Check className="h-4 w-4" />
              </button>
              <button onClick={() => { setTitle(session.title); setEditing(false); }} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Link href={`/sessions/${session.id}`} className="flex items-center gap-3 flex-1 min-w-0">
              <span className="font-medium truncate">{session.title}</span>
            </Link>
          )}
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={session.status} />
          {!editing && (
            <button
              onClick={(e) => { e.preventDefault(); setEditing(true); }}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <Pencil className="h-4 w-4" />
            </button>
          )}
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
