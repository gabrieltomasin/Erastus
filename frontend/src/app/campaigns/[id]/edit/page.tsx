import { Header } from "@/components/layout/header";
import { CampaignEditView } from "./campaign-edit-view";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function CampaignEditPage({ params }: Props) {
  const { id } = await params;
  return (
    <>
      <Header />
      <CampaignEditView campaignId={parseInt(id)} />
    </>
  );
}
