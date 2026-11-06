"""Config loading. The API key comes from the environment, never from the file."""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ConfigError(RuntimeError):
    pass


def load(path: Path | str | None = None) -> dict:
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    if not cfg_path.exists():
        raise ConfigError(f"no config file at {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    for key in ("provider", "telugu"):
        if key not in cfg:
            raise ConfigError(f"config.yaml is missing the '{key}' block")
    return cfg


def api_key(cfg: dict) -> str:
    env = cfg["provider"].get("api_key_env", "OPENAI_API_KEY")
    key = os.environ.get(env, "").strip()
    local = ROOT / ".api_key"
    if not key and local.exists():
        key = local.read_text(encoding="utf-8").strip()
    if not key:
        raise ConfigError(
            f"No API key. Set the environment variable {env}, or put the key in {local} "
            f"(that file is git-ignored). Nothing in this repo stores a key."
        )
    return key


def calibration() -> dict:
    path = ROOT / "data" / "calibration.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def syllables_per_second(cfg: dict) -> float | None:
    value = calibration().get("telugu_syllables_per_second") or cfg["telugu"].get("syllables_per_second")
    return float(value) if value else None


def batch_caps(cfg: dict) -> tuple[int, int | None]:
    """(max lines per request, max estimated prompt tokens per request).

    The token cap is what actually binds on a free-tier key; the line cap only stops a
    fifteen-line scene from becoming one enormous request.
    """
    block = cfg.get("batching", {}) or {}
    max_lines = int(block.get("max_lines_per_request", 14))
    tokens = block.get("max_prompt_tokens")
    return max_lines, (int(tokens) if tokens else None)
