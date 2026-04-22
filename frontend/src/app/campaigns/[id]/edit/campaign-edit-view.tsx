"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Save, Sparkles, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { CampaignDetail } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";

interface Props {
  campaignId: number;
}

export function CampaignEditView({ campaignId }: Props) {
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [context, setContext] = useState("");

  async function load() {
    try {
      const data = await apiFetch<CampaignDetail>(`/campaigns/${campaignId}`);
      setCampaign(data);
      setTitle(data.title);
      setDescription(data.description);
      setSystemPrompt(data.system_prompt || "");
      setContext(data.general_context || "");
    } catch (err) {
      console.error("Failed to load campaign:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [campaignId]);

  async function handleSave() {
    setSaving(true);
    try {
      await apiFetch(`/campaigns/${campaignId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title,
          description: description,
          system_prompt: systemPrompt || null,
          general_context: context || null,
        }),
      });
      await load();
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSaving(false);
    }
  }

  async function handleRegenerateContext() {
    setRegenerating(true);
    try {
      const data = await apiFetch<CampaignDetail>(
        `/campaigns/${campaignId}/regenerate-context`,
        { method: "POST" }
      );
      setContext(data.general_context || "");
      await load();
    } catch (err) {
      console.error("Failed to regenerate context:", err);
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

  if (!campaign) {
    return <p className="text-center py-20 text-muted-foreground">Campanha não encontrada</p>;
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link
          href={`/campaigns/${campaignId}`}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-bold flex-1">Editar Campanha</h1>
        <Button onClick={handleSave} disabled={saving}>
          <Save className="h-4 w-4" />
          {saving ? "Salvando..." : "Salvar"}
        </Button>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-1">Título</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Descrição</label>
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Prompt do Sistema (para geração de resumos)
          </label>
          <Textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={6}
            placeholder="Deixe vazio para usar o prompt padrão..."
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm font-medium">Contexto Geral da Campanha</label>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleRegenerateContext}
              disabled={regenerating}
            >
              {regenerating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {regenerating ? "Gerando..." : "Gerar com IA"}
            </Button>
          </div>
          <Textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            rows={10}
            placeholder="O contexto da campanha será gerado automaticamente a partir dos resumos das sessões..."
          />
          {campaign.context_updated_at && (
            <p className="text-xs text-muted-foreground mt-1">
              Última atualização: {new Date(campaign.context_updated_at).toLocaleString("pt-BR")}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
