import logging
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration: float
    segments: list[dict]


class Transcriber:
    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ):
        self.model_name = model_name or settings.WHISPER_MODEL
        self.device = device or settings.WHISPER_DEVICE
        self.compute_type = compute_type or settings.WHISPER_COMPUTE_TYPE
        self._model = None

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            logger.info(f"Loading Whisper model: {self.model_name} (device={self.device}, compute_type={self.compute_type})")
            self._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.info("Whisper model loaded")
        return self._model

    def transcribe(self, audio_path: str, language: str | None = None) -> TranscriptionResult:
        model = self._load_model()
        lang = language or settings.WHISPER_LANGUAGE

        logger.info(f"Starting transcription: {audio_path} (language={lang})")
        segments_iter, info = model.transcribe(
            audio_path,
            language=lang,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )

        segments = []
        full_text_parts = []
        for seg in segments_iter:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
            })
            full_text_parts.append(seg.text.strip())

        full_text = " ".join(full_text_parts)
        logger.info(f"Transcription complete: {len(full_text)} chars, {info.duration:.1f}s audio")

        return TranscriptionResult(
            text=full_text,
            language=info.language,
            duration=info.duration,
            segments=segments,
        )
