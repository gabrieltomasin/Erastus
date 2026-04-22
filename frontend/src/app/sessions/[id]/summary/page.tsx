import { Header } from "@/components/layout/header";
import { SummaryEditorView } from "./summary-editor-view";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function SessionSummaryPage({ params }: Props) {
  const { id } = await params;
  return (
    <>
      <Header />
      <SummaryEditorView sessionId={parseInt(id)} />
    </>
  );
}
