import zipfile
from pathlib import Path

from app.services.zip_handler import extract_audio_from_zip


def _make_zip(tmp_path, entries: dict[str, bytes], name: str = "test.zip") -> str:
    zip_path = tmp_path / name
    with zipfile.ZipFile(zip_path, "w") as zf:
        for filename, content in entries.items():
            zf.writestr(filename, content)
    return str(zip_path)


def _extract(zip_path: str, out_dir) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    return extract_audio_from_zip(zip_path, str(out_dir))


def test_extracts_only_audio_extensions(tmp_path):
    zip_path = _make_zip(
        tmp_path,
        {
            "session.mp3": b"audio",
            "notes.txt": b"text",
            "photo.jpg": b"image",
        },
    )
    extracted = _extract(zip_path, tmp_path / "out")
    assert len(extracted) == 1
    assert extracted[0].endswith("session.mp3")


def test_flattens_nested_paths(tmp_path):
    out_dir = tmp_path / "out"
    zip_path = _make_zip(tmp_path, {"records/week1/session.mp3": b"audio"})
    extracted = _extract(zip_path, out_dir)
    assert len(extracted) == 1
    # The full nested path is not recreated — the file lands directly in out_dir
    assert extracted[0] == str(out_dir / "session.mp3")
    assert (out_dir / "session.mp3").read_bytes() == b"audio"


def test_duplicate_filenames_get_counter_suffix(tmp_path):
    out_dir = tmp_path / "out"
    zip_path = _make_zip(
        tmp_path,
        {
            "a/session.mp3": b"first",
            "b/session.mp3": b"second",
        },
    )
    extracted = _extract(zip_path, out_dir)
    assert len(extracted) == 2
    contents = sorted((out_dir / f).name for f in [extracted[0], extracted[1]])
    assert contents == ["session.mp3", "session_1.mp3"]
    # The two duplicates kept their distinct contents
    assert {Path(p).read_bytes() for p in extracted} == {b"first", b"second"}


def test_skips_directory_entries(tmp_path):
    out_dir = tmp_path / "out"
    zip_path = tmp_path / "dirs.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("nested/", "")
        zf.writestr("nested/session.mp3", b"audio")
    extracted = _extract(zip_path, out_dir)
    assert len(extracted) == 1
    assert extracted[0].endswith("session.mp3")


def test_zip_without_audio_returns_empty(tmp_path):
    zip_path = _make_zip(tmp_path, {"readme.md": b"nothing here"})
    assert _extract(zip_path, tmp_path / "out") == []
