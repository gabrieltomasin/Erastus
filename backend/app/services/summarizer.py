import logging

import httpx
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """Você é um narrador especialista em RPG. Com base na transcrição abaixo e no contexto da campanha, gere um resumo estruturado com:

## Eventos Principais
Descreva os eventos mais importantes da sessão.

## Decisões dos Jogadores
Liste as decisões importantes tomadas pelos personagens.

## NPCs e Lore
Mencione novos NPCs encontrados ou revelações sobre o mundo.

## Ganchos para Próximas Sessões
Liste perguntas em aberto e possibilidades para o futuro.

Contexto da campanha:
{context}

Transcrição:
{transcription}"""


class LLMClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (base_url or settings.LLM_API_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE

    def _count_tokens(self, text: str) -> int:
        try:
            enc = tiktoken.encoding_for_model(self.model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))

    def _chunk_text(self, text: str, max_tokens: int, overlap: int = 200) -> list[str]:
        """Split text into chunks that fit within max_tokens."""
        try:
            enc = tiktoken.encoding_for_model(self.model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")

        tokens = enc.encode(text)
        chunks = []
        start = 0
        while start < len(tokens):
            end = start + max_tokens
            chunk_tokens = tokens[start:end]
            chunks.append(enc.decode(chunk_tokens))
            start = end - overlap
        return chunks

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    )
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request. Returns the assistant's message."""
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def summarize(
        self,
        transcription: str,
        context: str | None = None,
        custom_prompt: str | None = None,
    ) -> str:
        """Generate a summary of the transcription, using map-reduce for long texts."""
        context_text = context or "Nenhum contexto disponível ainda."
        prompt_template = custom_prompt or DEFAULT_SYSTEM_PROMPT

        # Estimate available tokens for input
        # Rough: most models have ~128k context. Reserve max_tokens for output + system overhead.
        model_context = 128000
        available_input = model_context - self.max_tokens - 500  # safety margin

        # Build the full prompt to check size
        full_prompt = prompt_template.format(context=context_text, transcription=transcription)
        prompt_tokens = self._count_tokens(full_prompt)

        if prompt_tokens <= available_input:
            # Fits in one request
            system = "Você é um assistente especializado em resumir sessões de RPG de mesa."
            user = full_prompt
            return self.complete(system, user)
        else:
            # Map-reduce: chunk transcription, summarize each, then combine
            logger.info(f"Transcription too large ({prompt_tokens} tokens), using map-reduce")
            chunk_size = available_input - self._count_tokens(
                prompt_template.format(context=context_text, transcription="")
            )
            chunks = self._chunk_text(transcription, max(1000, chunk_size))

            # Summarize each chunk
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Summarizing chunk {i + 1}/{len(chunks)}")
                chunk_prompt = prompt_template.format(context=context_text, transcription=chunk)
                summary = self.complete(
                    "Você é um assistente especializado em resumir sessões de RPG de mesa.",
                    chunk_prompt,
                )
                chunk_summaries.append(f"### Parte {i + 1}\n{summary}")

            # Combine chunk summaries
            combined = "\n\n".join(chunk_summaries)
            combine_prompt = (
                "Combine os seguintes resumos parciais de uma sessão de RPG em um único resumo "
                "coerente e bem estruturado, mantendo todos os eventos importantes:\n\n"
                f"{combined}"
            )
            return self.complete(
                "Você é um assistente especializado em resumir sessões de RPG de mesa.",
                combine_prompt,
            )
