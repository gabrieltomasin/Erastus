from app.services.transcript_builder import (
    build_speaker_map,
    build_transcription,
    format_time,
)


def _seg(start: float, end: float, text: str, file: str) -> dict:
    return {"start": start, "end": end, "text": text, "file": file}


class TestFormatTime:
    def test_under_a_minute(self):
        assert format_time(0) == "00:00"
        assert format_time(5.7) == "00:05"

    def test_minutes(self):
        assert format_time(59) == "00:59"
        assert format_time(61) == "01:01"

    def test_hours(self):
        assert format_time(3600) == "01:00:00"
        assert format_time(3661) == "01:01:01"


class TestBuildSpeakerMap:
    def test_maps_filenames_to_speakers_in_order(self):
        files = [{"filename": "mesa.mp3"}, {"filename": "joao.m4a"}]
        assert build_speaker_map(files) == {
            "mesa.mp3": "speaker_1",
            "joao.m4a": "speaker_2",
        }

    def test_missing_filename_gets_positional_fallback(self):
        files = [{}, {"filename": "a.mp3"}]
        assert build_speaker_map(files) == {
            "Arquivo 1": "speaker_1",
            "a.mp3": "speaker_2",
        }


class TestBuildTranscription:
    def test_empty_segments_returns_empty_string(self):
        assert build_transcription([], [{"filename": "a.mp3"}]) == ""

    def test_single_file_joins_text_without_timestamps(self):
        segments = [_seg(0, 1, " Olá!", "a.mp3"), _seg(2, 3, " Tudo bem?", "a.mp3")]
        result = build_transcription(segments, [{"filename": "a.mp3"}])
        assert result == " Olá!  Tudo bem?"

    def test_multi_file_interleaves_by_start_time(self):
        segments = [
            _seg(10, 12, " fala do mesa", "mesa.mp3"),
            _seg(0, 2, " fala do joao", "joao.m4a"),
        ]
        files = [{"filename": "mesa.mp3"}, {"filename": "joao.m4a"}]
        result = build_transcription(segments, files)
        # Segments are reordered by start timestamp regardless of input order
        assert result.index("joao") < result.index("mesa")

    def test_multi_file_labels_speaker_on_change(self):
        segments = [
            _seg(0, 2, " oi", "a.mp3"),
            _seg(3, 5, " olá", "b.mp3"),
            _seg(6, 8, " continua", "b.mp3"),
            _seg(9, 10, " resposta", "a.mp3"),
        ]
        files = [{"filename": "a.mp3"}, {"filename": "b.mp3"}]
        lines = build_transcription(segments, files).splitlines()

        # First line starts with the leading newline separator stripped,
        # subsequent speaker changes are on their own lines.
        speaker_lines = [ln for ln in lines if ln.startswith("**")]
        assert [ln.split(":")[0] for ln in speaker_lines] == [
            "**speaker_1",
            "**speaker_2",
            "**speaker_1",
        ]
        # Consecutive segments from the same file keep flowing without a new label
        assert any("continua" in ln and not ln.startswith("**") for ln in lines)

    def test_multi_file_includes_timestamps(self):
        segments = [_seg(7265, 7267, " texto", "a.mp3")]
        files = [{"filename": "a.mp3"}, {"filename": "b.mp3"}]
        result = build_transcription(segments, files)
        assert "[02:01:05]" in result

    def test_unknown_file_gets_fallback_speaker(self):
        segments = [_seg(0, 2, " texto", "desconhecido.mp3")]
        files = [{"filename": "a.mp3"}, {"filename": "b.mp3"}]
        result = build_transcription(segments, files)
        assert "**speaker_?:**" in result
