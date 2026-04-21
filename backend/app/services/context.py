import logging
import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.session import Session, SessionStatus
from app.services.summarizer import LLMClient

logger = logging.getLogger(__name__)

CONTEXT_SYNTHESIS_PROMPT = """Sintetize os resumos das sessões de RPG abaixo em um documento de contexto da campanha conciso e organizado. Inclua:

## Personagens (Jogadores)
Lista dos personagens dos jogadores com suas classes, raças e desenvolvimento.

## NPCs Importantes
NPCs recorrentes, seus papéis e relação com o grupo.

## Enredo Principal
Linha narrativa principal e eventos marcantes.

## Subplots
Tramas secundárias em andamento.

## Locais Importantes
Lugares visitados e sua importância.

## Itens e Recursos
Itens mágicos, recursos ou informações importantes adquiridos.

## Fios Soltos
Questões não resolvidas e ganchos para futuras sessões.

Resumos das sessões:
{summaries}"""


async def update_campaign_context(db: AsyncSession, campaign_id: int) -> str:
    """Generate/update the campaign's general_context from all finalized session summaries."""
    # Fetch campaign
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    # Fetch all sessions with final summaries
    result = await db.execute(
        select(Session)
        .where(Session.campaign_id == campaign_id)
        .where(Session.final_summary.isnot(None))
        .order_by(Session.session_number)
    )
    sessions = result.scalars().all()

    if not sessions:
        return "Nenhuma sessão finalizada para gerar contexto."

    # Build summaries text
    parts = []
    for s in sessions:
        parts.append(f"### Sessão {s.session_number}: {s.title}\n{s.final_summary}")
    summaries_text = "\n\n".join(parts)

    # Generate context via LLM
    client = LLMClient()
    context = client.complete(
        "Você é um assistente especializado em organizar informações de campanhas de RPG de mesa.",
        CONTEXT_SYNTHESIS_PROMPT.format(summaries=summaries_text),
    )

    # Update campaign
    campaign.general_context = context
    campaign.context_updated_at = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()

    return context
