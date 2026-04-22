"use client";

import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { Campaign, CampaignCreate } from "@/lib/types";
import { CampaignCard } from "@/components/campaign/campaign-card";
import { CampaignForm } from "@/components/campaign/campaign-form";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export function CampaignList() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  async function loadCampaigns() {
    try {
      const data = await apiFetch<Campaign[]>("/campaigns");
      setCampaigns(data);
    } catch (err) {
      console.error("Failed to load campaigns:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCampaigns();
  }, []);

  async function handleCreate(data: CampaignCreate) {
    await apiFetch<Campaign>("/campaigns", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    setShowForm(false);
    await loadCampaigns();
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Campanhas</h1>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4" />
          Nova Campanha
        </Button>
      </div>

      {showForm && (
        <div className="mb-6">
          <CampaignForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} />
        </div>
      )}

      {campaigns.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground">
          <p className="text-lg">Nenhuma campanha ainda</p>
          <p className="text-sm mt-1">Clique em &quot;Nova Campanha&quot; para começar</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {campaigns.map((c) => (
            <CampaignCard key={c.id} campaign={c} />
          ))}
        </div>
      )}
    </div>
  );
}
