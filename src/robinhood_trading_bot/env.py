from __future__ import annotations

from pathlib import Path
from typing import Mapping
import os


def read_env_file(path: str | Path = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            values[key] = value.strip().strip('"').strip("'")
    return values


def merged_env(env_file: str | Path = ".env", environ: Mapping[str, str] | None = None) -> dict[str, str]:
    merged = read_env_file(env_file)
    merged.update(dict(os.environ if environ is None else environ))
    return merged
