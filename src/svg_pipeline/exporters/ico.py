"""ICO (Windows icon) export handler."""

from pathlib import Path
from typing import Any

from svg_pipeline.backends.base import Backend


class IcoExporter:
    """Exporter for ICO format with multi-size support."""

    DEFAULT_SIZES = [16, 32, 48]

    def __init__(self, sizes: list[int] | None = None):
        """Initialize ICO exporter.

        Args:
            sizes: List of icon sizes to embed (default: [16, 32, 48])
        """
        self.sizes = sizes or self.DEFAULT_SIZES

    def export(self, image: Any, backend: Backend, path: Path) -> Path:
        """Export image as ICO with multiple embedded sizes.

        Args:
            image: Backend-specific image object
            backend: Processing backend
            path: Output file path

        Returns:
            Path to exported file
        """
        backend.export_ico(image, path, self.sizes)
        return path

    def __repr__(self) -> str:
        return f"IcoExporter(sizes={self.sizes})"
