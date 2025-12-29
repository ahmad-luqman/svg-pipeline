"""Color transformation."""

from typing import Any

from svg_pipeline.backends.base import Backend


class ColorTransform:
    """Transform that applies color changes to images."""

    def __init__(self, foreground: str | None = None, background: str | None = None):
        """Initialize color transform.

        Args:
            foreground: Foreground color in hex (e.g., '#ffffff')
            background: Background color in hex (e.g., '#000000')
        """
        self.foreground = foreground
        self.background = background

    def apply(self, image: Any, backend: Backend) -> Any:
        """Apply the color transformation.

        Args:
            image: Backend-specific image object
            backend: Processing backend to use

        Returns:
            Color-transformed image
        """
        return backend.recolor(image, self.foreground, self.background)

    def __repr__(self) -> str:
        parts = []
        if self.foreground:
            parts.append(f"fg={self.foreground}")
        if self.background:
            parts.append(f"bg={self.background}")
        return f"ColorTransform({', '.join(parts)})"
