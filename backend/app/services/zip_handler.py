import zipfile
from pathlib import Path

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".wma", ".aac"}


def extract_audio_from_zip(zip_path: str, output_dir: str) -> list[str]:
    """Extract audio files from a ZIP archive. Returns list of extracted file paths."""
    extracted = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            ext = Path(info.filename).suffix.lower()
            if ext not in AUDIO_EXTENSIONS:
                continue
            # Flatten: use only the filename, not the full path inside the ZIP
            filename = Path(info.filename).name
            target = Path(output_dir) / filename

            # Handle duplicate names
            counter = 1
            while target.exists():
                target = Path(output_dir) / f"{Path(filename).stem}_{counter}{ext}"
                counter += 1

            with zf.open(info) as src, open(target, "wb") as dst:
                dst.write(src.read())
            extracted.append(str(target))

    return extracted
