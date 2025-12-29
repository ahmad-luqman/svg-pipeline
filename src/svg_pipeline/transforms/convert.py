"""Format conversion transformation."""

from pathlib import Path
from typing import Any, Literal

from svg_pipeline.backends.base import Backend


class ConvertTransform:
    """Transform that converts images to different formats."""

    def __init__(self, format: Literal["png", "ico", "webp", "jpeg"]):
        """Initialize conversion transform.

        Args:
            format: Target format
        """
        self.format = format

    def apply(self, image: Any, backend: Backend, output_path: Path) -> Path:
        """Apply the conversion and save to file.

        Args:
            image: Backend-specific image object
            backend: Processing backend to use
            output_path: Path to save converted file

        Returns:
            Path to the saved file
        """
        if self.format == "png":
            backend.export_png(image, output_path)
        elif self.format == "ico":
            backend.export_ico(image, output_path)
        else:
            raise NotImplementedError(f"Format {self.format} not yet implemented")

        return output_path

    def __repr__(self) -> str:
        return f"ConvertTransform(format={self.format})"
