"""PNG export handler."""

from pathlib import Path
from typing import Any

from svg_pipeline.backends.base import Backend


class PngExporter:
    """Exporter for PNG format with optimization options."""

    def __init__(self, optimize: bool = True, compression: int = 6):
        """Initialize PNG exporter.

        Args:
            optimize: Whether to optimize PNG output
            compression: Compression level (0-9)
        """
        self.optimize = optimize
        self.compression = compression

    def export(self, image: Any, backend: Backend, path: Path) -> Path:
        """Export image as PNG.

        Args:
            image: Backend-specific image object
            backend: Processing backend
            path: Output file path

        Returns:
            Path to exported file
        """
        backend.export_png(image, path)
        return path

    def __repr__(self) -> str:
        return f"PngExporter(optimize={self.optimize})"
