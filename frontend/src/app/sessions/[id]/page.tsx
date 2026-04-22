import { Header } from "@/components/layout/header";
import { SessionDetailView } from "./session-detail-view";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function SessionDetailPage({ params }: Props) {
  const { id } = await params;
  return (
    <>
      <Header />
      <SessionDetailView sessionId={parseInt(id)} />
    </>
  );
}
