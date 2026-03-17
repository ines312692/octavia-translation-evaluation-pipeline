from pathlib import Path
from typing import List


def load_segments(filepath: str) -> List[str]:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    segments = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    segments = [s for s in segments if s]
    if not segments:
        raise ValueError(f"No segments found in: {filepath}")
    return segments