"""Abstract base class for image processing backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Backend(ABC):
    """Abstract backend interface for image processing.

    This interface defines the contract that all processing backends must fulfill.
    Implementing a new backend (e.g., OpenCV, GPU-accelerated) requires only
    implementing these methods.
    """

    # Type alias for backend-specific image representation
    ImageType = Any

    @abstractmethod
    def load_svg(self, path: Path, width: int | None = None, height: int | None = None) -> Any:
        """Load an SVG file and rasterize it.

        Args:
            path: Path to the SVG file
            width: Optional target width (preserves aspect ratio if only one dimension given)
            height: Optional target height

        Returns:
            Backend-specific image object
        """
        ...

    @abstractmethod
    def load_image(self, path: Path) -> Any:
        """Load a raster image file.

        Args:
            path: Path to the image file (PNG, JPEG, etc.)

        Returns:
            Backend-specific image object
        """
        ...

    @abstractmethod
    def resize(self, image: Any, width: int, height: int) -> Any:
        """Resize an image to the specified dimensions.

        Args:
            image: Backend-specific image object
            width: Target width in pixels
            height: Target height in pixels

        Returns:
            Resized image object
        """
        ...

    @abstractmethod
    def apply_background(self, image: Any, color: str) -> Any:
        """Apply a background color to an image with transparency.

        Args:
            image: Backend-specific image object (should have alpha channel)
            color: Background color in hex format (e.g., '#ffffff')

        Returns:
            Image with background applied
        """
        ...

    @abstractmethod
    def recolor(self, image: Any, foreground: str | None, background: str | None) -> Any:
        """Recolor an image by replacing colors.

        Args:
            image: Backend-specific image object
            foreground: New foreground color (hex), or None to keep original
            background: New background color (hex), or None to keep original

        Returns:
            Recolored image object
        """
        ...

    @abstractmethod
    def export_png(self, image: Any, path: Path) -> None:
        """Export image as PNG.

        Args:
            image: Backend-specific image object
            path: Output file path
        """
        ...

    @abstractmethod
    def export_ico(self, image: Any, path: Path, sizes: list[int] | None = None) -> None:
        """Export image as ICO (Windows icon format).

        Args:
            image: Backend-specific image object
            path: Output file path
            sizes: List of icon sizes to include (default: [16, 32, 48])
        """
        ...

    @abstractmethod
    def get_size(self, image: Any) -> tuple[int, int]:
        """Get the dimensions of an image.

        Args:
            image: Backend-specific image object

        Returns:
            Tuple of (width, height)
        """
        ...

    def copy(self, image: Any) -> Any:
        """Create a copy of an image.

        Default implementation returns the same object - override if backend
        requires explicit copying.
        """
        return image
