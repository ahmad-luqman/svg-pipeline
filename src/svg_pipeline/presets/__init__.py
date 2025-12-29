"""Preset configurations for common output sets."""

from pathlib import Path
from typing import Any

import yaml

PRESETS_DIR = Path(__file__).parent


def load_preset(name: str) -> dict[str, Any]:
    """Load a preset configuration by name."""
    preset_path = PRESETS_DIR / f"{name}.yaml"
    if not preset_path.exists():
        available = [p.stem for p in PRESETS_DIR.glob("*.yaml")]
        raise ValueError(f"Preset '{name}' not found. Available: {available}")

    with open(preset_path) as f:
        return yaml.safe_load(f)


def list_presets() -> list[str]:
    """List all available preset names."""
    return [p.stem for p in PRESETS_DIR.glob("*.yaml")]


__all__ = ["load_preset", "list_presets", "PRESETS_DIR"]
