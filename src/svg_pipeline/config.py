"""Configuration models for SVG Pipeline."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ColorConfig(BaseModel):
    """Color theme configuration."""

    foreground: str | None = Field(None, description="Foreground color (hex, e.g., '#ffffff')")
    background: str | None = Field(None, description="Background color (hex, e.g., '#000000')")


class OutputSpec(BaseModel):
    """Specification for a single output file."""

    name: str = Field(..., description="Output filename (without path)")
    format: Literal["png", "ico", "svg", "webp"] = Field(..., description="Output format")
    width: int = Field(..., ge=1, description="Output width in pixels")
    height: int | None = Field(None, ge=1, description="Output height (defaults to width)")

    @property
    def size(self) -> tuple[int, int]:
        """Get (width, height) tuple."""
        return (self.width, self.height or self.width)


class PresetConfig(BaseModel):
    """Configuration loaded from a preset file."""

    name: str = Field(..., description="Preset name")
    description: str = Field("", description="Preset description")
    outputs: list[OutputSpec] = Field(default_factory=list, description="Output specifications")
    generate_manifest: bool = Field(False, description="Whether to generate site.webmanifest")


class PipelineConfig(BaseModel):
    """Main pipeline configuration."""

    source: Path = Field(..., description="Source SVG/image file path")
    output_dir: Path = Field(default=Path("./output"), description="Output directory")
    colors: ColorConfig = Field(default_factory=lambda: ColorConfig(), description="Color theme")
    preset: str | None = Field(default=None, description="Preset name to use")
    outputs: list[OutputSpec] = Field(default_factory=list, description="Custom output specs")
    parallel: bool = Field(default=False, description="Enable parallel processing")
    backend: str = Field(default="pillow", description="Processing backend to use")

    model_config = {"frozen": False}


class ExecutorType(BaseModel):
    """Executor configuration for parallel processing."""

    type: Literal["sequential", "threadpool", "processpool"] = Field(
        "sequential", description="Executor type"
    )
    max_workers: int | None = Field(None, ge=1, description="Max worker threads/processes")
