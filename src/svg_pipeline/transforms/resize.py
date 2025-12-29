"""Resize transformation."""

from typing import Any

from svg_pipeline.backends.base import Backend


class ResizeTransform:
    """Transform that resizes images to specified dimensions."""

    def __init__(self, width: int, height: int | None = None):
        """Initialize resize transform.

        Args:
            width: Target width in pixels
            height: Target height (defaults to width for square output)
        """
        self.width = width
        self.height = height or width

    def apply(self, image: Any, backend: Backend) -> Any:
        """Apply the resize transformation.

        Args:
            image: Backend-specific image object
            backend: Processing backend to use

        Returns:
            Resized image
        """
        return backend.resize(image, self.width, self.height)

    def __repr__(self) -> str:
        return f"ResizeTransform({self.width}x{self.height})"
