import Link from "next/link";
import { Card, CardTitle, CardDescription } from "@/components/ui/card";
import { Campaign } from "@/lib/types";
import { Calendar, Users } from "lucide-react";

interface CampaignCardProps {
  campaign: Campaign;
}

export function CampaignCard({ campaign }: CampaignCardProps) {
  return (
    <Link href={`/campaigns/${campaign.id}`}>
      <Card onClick={undefined}>
        <CardTitle>{campaign.title}</CardTitle>
        {campaign.description && <CardDescription>{campaign.description}</CardDescription>}
        <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Users className="h-3.5 w-3.5" />
            {campaign.session_count} sessão{campaign.session_count !== 1 ? "ões" : ""}
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" />
            {new Date(campaign.updated_at).toLocaleDateString("pt-BR")}
          </span>
        </div>
      </Card>
    </Link>
  );
}
