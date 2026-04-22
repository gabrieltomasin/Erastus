"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { CampaignCreate } from "@/lib/types";

interface CampaignFormProps {
  onSubmit: (data: CampaignCreate) => Promise<void>;
  onCancel: () => void;
}

export function CampaignForm({ onSubmit, onCancel }: CampaignFormProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    try {
      await onSubmit({ title: title.trim(), description: description.trim() || undefined });
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-card p-5">
      <div>
        <label className="block text-sm font-medium mb-1">Nome da campanha</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Ex: Tormenta RPG - Reino de Tollon"
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          autoFocus
        />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">Descrição (opcional)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Breve descrição da campanha..."
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[60px] resize-y"
        />
      </div>
      <div className="flex gap-2 justify-end">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={!title.trim() || loading}>
          {loading ? "Criando..." : "Criar Campanha"}
        </Button>
      </div>
    </form>
  );
}
