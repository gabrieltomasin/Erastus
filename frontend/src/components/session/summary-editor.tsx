"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import Highlight from "@tiptap/extension-highlight";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { SessionDetail } from "@/lib/types";
import { useState } from "react";
import {
  Bold,
  Italic,
  Heading2,
  List,
  ListOrdered,
  Highlighter,
  Save,
  RotateCcw,
} from "lucide-react";

interface SummaryEditorProps {
  session: SessionDetail;
  onUpdate: () => void;
}

export function SummaryEditor({ session, onUpdate }: SummaryEditorProps) {
  const [saving, setSaving] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({ placeholder: "Nenhum resumo ainda..." }),
      Highlight,
    ],
    content: session.final_summary || session.raw_summary || "",
    editable: true,
  });

  async function handleSave() {
    if (!editor) return;
    setSaving(true);
    try {
      const html = editor.getHTML();
      await apiFetch(`/sessions/${session.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ final_summary: html }),
      });
      onUpdate();
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    if (!editor || !session.raw_summary) return;
    editor.commands.setContent(session.raw_summary);
  }

  if (!editor) return null;

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1">
          <h2 className="text-sm font-semibold text-muted-foreground mr-3">Resumo</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => editor.chain().focus().toggleBold().run()}
            className={editor.isActive("bold") ? "bg-muted" : ""}
          >
            <Bold className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => editor.chain().focus().toggleItalic().run()}
            className={editor.isActive("italic") ? "bg-muted" : ""}
          >
            <Italic className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            className={editor.isActive("heading", { level: 2 }) ? "bg-muted" : ""}
          >
            <Heading2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            className={editor.isActive("bulletList") ? "bg-muted" : ""}
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            className={editor.isActive("orderedList") ? "bg-muted" : ""}
          >
            <ListOrdered className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => editor.chain().focus().toggleHighlight().run()}
            className={editor.isActive("highlight") ? "bg-muted" : ""}
          >
            <Highlighter className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex items-center gap-2">
          {session.raw_summary && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowOriginal(!showOriginal)}
            >
              {showOriginal ? "Editar" : "Ver Original"}
            </Button>
          )}
          {session.raw_summary && (
            <Button variant="ghost" size="sm" onClick={handleReset} title="Restaurar original">
              <RotateCcw className="h-4 w-4" />
            </Button>
          )}
          <Button size="sm" onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4" />
            {saving ? "Salvando..." : "Salvar"}
          </Button>
        </div>
      </div>

      {showOriginal ? (
        <div className="rounded-xl border border-border bg-card p-4 text-sm whitespace-pre-wrap max-h-[600px] overflow-y-auto">
          {session.raw_summary}
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card p-4 min-h-[200px] prose prose-sm dark:prose-invert max-w-none">
          <EditorContent editor={editor} />
        </div>
      )}
    </div>
  );
}
