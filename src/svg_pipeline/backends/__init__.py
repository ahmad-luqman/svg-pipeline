"""Backend implementations for image processing."""

from svg_pipeline.backends.base import Backend
from svg_pipeline.backends.pillow import PillowBackend

__all__ = ["Backend", "PillowBackend"]
