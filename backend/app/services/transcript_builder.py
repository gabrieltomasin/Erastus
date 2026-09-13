"""Pure helpers to build transcript text from Whisper segments.

Extracted from the transcribe worker so the interleaving logic is
unit-testable without a Celery broker, database, or Whisper model.
"""

MULTI_SPEAKER_FALLBACK = "speaker_?"


def format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS or MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def build_speaker_map(audio_files: list[dict]) -> dict[str, str]:
    """Map each file's filename to a speaker_N label based on its position."""
    return {
        af.get("filename", f"Arquivo {i+1}"): f"speaker_{i+1}"
        for i, af in enumerate(audio_files)
    }


def build_transcription(segments: list[dict], audio_files: list[dict]) -> str:
    """Build the transcript text from interleaved segments.

    Args:
        segments: dicts with start/end/text/file; file is the source filename.
            Sorted in place by start timestamp so simultaneous recordings from
            different sources read as one chronological conversation.
        audio_files: the session's audio file descriptors, used for the
            filename -> speaker mapping.

    Returns the transcript, or "" when there are no segments (the caller
    falls back to Whisper's full text).
    """
    if not segments:
        return ""

    segments.sort(key=lambda s: s["start"])
    speaker_map = build_speaker_map(audio_files)

    if len(audio_files) > 1:
        lines = []
        current_speaker = None
        for seg in segments:
            speaker = speaker_map.get(seg["file"], MULTI_SPEAKER_FALLBACK)
            timestamp = f"[{format_time(seg['start'])}]"
            if speaker != current_speaker:
                lines.append(f"\n**{speaker}:** {timestamp} {seg['text']}")
                current_speaker = speaker
            else:
                lines.append(f"{timestamp} {seg['text']}")
        return "\n".join(lines).strip()

    # Single file — simple transcription
    return " ".join(seg["text"] for seg in segments)
