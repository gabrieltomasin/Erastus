import { Header } from "@/components/layout/header";
import { CampaignDetailView } from "./campaign-detail-view";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function CampaignDetailPage({ params }: Props) {
  const { id } = await params;
  return (
    <>
      <Header />
      <CampaignDetailView campaignId={parseInt(id)} />
    </>
  );
}
