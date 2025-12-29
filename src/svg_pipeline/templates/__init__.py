"""Built-in SVG templates."""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent


def get_template(name: str) -> Path:
    """Get path to a built-in template by name."""
    template_path = TEMPLATES_DIR / f"{name}.svg"
    if not template_path.exists():
        available = [p.stem for p in TEMPLATES_DIR.glob("*.svg")]
        raise ValueError(f"Template '{name}' not found. Available: {available}")
    return template_path


__all__ = ["get_template", "TEMPLATES_DIR"]
