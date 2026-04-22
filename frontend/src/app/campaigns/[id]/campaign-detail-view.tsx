"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Plus, Trash2, Settings } from "lucide-react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import { apiFetch } from "@/lib/api";
import { CampaignDetail, SessionBrief } from "@/lib/types";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { SortableSessionCard } from "@/components/session/sortable-session-card";

interface Props {
  campaignId: number;
}

export function CampaignDetailView({ campaignId }: Props) {
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSessionForm, setShowSessionForm] = useState(false);
  const [sessionTitle, setSessionTitle] = useState("");

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  async function load() {
    try {
      const data = await apiFetch<CampaignDetail>(`/campaigns/${campaignId}`);
      setCampaign(data);
    } catch (err) {
      console.error("Failed to load campaign:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [campaignId]);

  async function handleCreateSession(e: React.FormEvent) {
    e.preventDefault();
    if (!sessionTitle.trim()) return;
    await apiFetch("/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ campaign_id: campaignId, title: sessionTitle.trim() }),
    });
    setSessionTitle("");
    setShowSessionForm(false);
    await load();
  }

  async function handleDeleteSession(sessionId: number) {
    if (!confirm("Deletar esta sessão?")) return;
    await apiFetch(`/sessions/${sessionId}`, { method: "DELETE" });
    await load();
  }

  async function handleDeleteCampaign() {
    if (!confirm("Deletar esta campanha e todas as sessões?")) return;
    await apiFetch(`/campaigns/${campaignId}`, { method: "DELETE" });
    window.location.href = "/campaigns";
  }

  async function handleDragEnd(event: DragEndEvent) {
    if (!campaign) return;
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = campaign.sessions.findIndex((s) => s.id === active.id);
    const newIndex = campaign.sessions.findIndex((s) => s.id === over.id);
    const reordered = arrayMove(campaign.sessions, oldIndex, newIndex);

    // Optimistic update
    setCampaign({ ...campaign, sessions: reordered });

    try {
      await apiFetch(`/campaigns/${campaignId}/sessions/reorder`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_ids: reordered.map((s) => s.id) }),
      });
    } catch {
      // Revert on failure
      await load();
    }
  }

  function handleRename(sessionId: number, newTitle: string) {
    if (!campaign) return;
    setCampaign({
      ...campaign,
      sessions: campaign.sessions.map((s) => s.id === sessionId ? { ...s, title: newTitle } : s),
    });
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
        <Link href="/campaigns" className="text-muted-foreground hover:text-foreground transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{campaign.title}</h1>
          {campaign.description && (
            <p className="text-sm text-muted-foreground mt-1">{campaign.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Link href={`/campaigns/${campaignId}/edit`}>
            <Button variant="secondary">
              <Settings className="h-4 w-4" />
              Editar
            </Button>
          </Link>
          <Button variant="destructive" onClick={handleDeleteCampaign}>
            <Trash2 className="h-4 w-4" />
            Deletar
          </Button>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Sessões</h2>
        <Button onClick={() => setShowSessionForm(true)}>
          <Plus className="h-4 w-4" />
          Nova Sessão
        </Button>
      </div>

      {showSessionForm && (
        <form onSubmit={handleCreateSession} className="mb-4 flex gap-2">
          <input
            type="text"
            value={sessionTitle}
            onChange={(e) => setSessionTitle(e.target.value)}
            placeholder="Título da sessão"
            className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            autoFocus
          />
          <Button type="submit" disabled={!sessionTitle.trim()}>Criar</Button>
          <Button type="button" variant="secondary" onClick={() => { setShowSessionForm(false); setSessionTitle(""); }}>
            Cancelar
          </Button>
        </form>
      )}

      {campaign.sessions.length === 0 ? (
        <p className="text-center py-10 text-muted-foreground">
          Nenhuma sessão ainda. Clique em &quot;Nova Sessão&quot; para começar.
        </p>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={campaign.sessions.map((s) => s.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-2">
              {campaign.sessions.map((session) => (
                <SortableSessionCard
                  key={session.id}
                  session={session}
                  onDelete={handleDeleteSession}
                  onRename={handleRename}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
    </div>
  );
}
