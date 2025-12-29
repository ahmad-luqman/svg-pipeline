"""Core pipeline orchestration."""

from concurrent.futures import Future, as_completed
from enum import Enum
from pathlib import Path
from typing import Literal, Self

from svg_pipeline.backends.base import Backend
from svg_pipeline.backends.pillow import PillowBackend
from svg_pipeline.config import ColorConfig, OutputSpec, PipelineConfig, PresetConfig
from svg_pipeline.executor import Executor, ExecutorType, SequentialExecutor, create_executor
from svg_pipeline.presets import load_preset


class FitMode(Enum):
    """How to handle aspect ratio when resizing."""

    STRETCH = "stretch"  # Distort to fill (legacy behavior)
    COVER = "cover"  # Crop to fill, no distortion (best for icons)
    CONTAIN = "contain"  # Fit with padding (best for full visibility)


class Pipeline:
    """Main pipeline class for SVG to asset transformation.

    Provides a fluent API for configuring and executing the transformation pipeline.

    Example:
        Pipeline("logo.svg").with_preset("web").generate("./output")

        # With parallel execution
        Pipeline("logo.svg").with_preset("web").with_parallel().generate("./output")
    """

    def __init__(self, source: str | Path, backend: Backend | None = None):
        """Initialize pipeline with a source file.

        Args:
            source: Path to source SVG or image file
            backend: Processing backend (defaults to PillowBackend)
        """
        self.source = Path(source)
        if not self.source.exists():
            raise FileNotFoundError(f"Source file not found: {self.source}")

        self.backend = backend or PillowBackend()
        self.colors = ColorConfig()
        self.outputs: list[OutputSpec] = []
        self.preset_config: PresetConfig | None = None
        self._generate_manifest = False
        self._executor_type: ExecutorType = ExecutorType.SEQUENTIAL
        self._max_workers: int | None = None
        self._fit_mode: FitMode = FitMode.COVER  # Default to cover (no distortion)

    def with_preset(self, preset_name: str) -> Self:
        """Load a preset configuration.

        Args:
            preset_name: Name of preset (e.g., 'web', 'mobile', 'full')

        Returns:
            Self for method chaining
        """
        preset_data = load_preset(preset_name)
        self.preset_config = PresetConfig(
            name=preset_name,
            description=preset_data.get("description", ""),
            outputs=[OutputSpec(**o) for o in preset_data.get("outputs", [])],
            generate_manifest=preset_data.get("generate_manifest", False),
        )
        self._generate_manifest = self.preset_config.generate_manifest
        return self

    def with_colors(self, foreground: str | None = None, background: str | None = None) -> Self:
        """Set color theme for output.

        Args:
            foreground: Foreground color in hex (e.g., '#ffffff')
            background: Background color in hex (e.g., '#000000')

        Returns:
            Self for method chaining
        """
        self.colors = ColorConfig(foreground=foreground, background=background)
        return self

    def with_output(
        self,
        name: str,
        format: str,
        width: int,
        height: int | None = None,
    ) -> Self:
        """Add a custom output specification.

        Args:
            name: Output filename
            format: Output format ('png', 'ico', 'svg', 'webp')
            width: Output width in pixels
            height: Output height (defaults to width for square)

        Returns:
            Self for method chaining
        """
        self.outputs.append(
            OutputSpec(name=name, format=format, width=width, height=height)  # type: ignore
        )
        return self

    def with_manifest(self, generate: bool = True) -> Self:
        """Enable/disable manifest generation.

        Args:
            generate: Whether to generate site.webmanifest

        Returns:
            Self for method chaining
        """
        self._generate_manifest = generate
        return self

    def with_parallel(
        self,
        executor_type: ExecutorType | str = ExecutorType.THREADPOOL,
        max_workers: int | None = None,
    ) -> Self:
        """Enable parallel execution for output generation.

        Args:
            executor_type: Type of executor ('threadpool' or 'processpool')
            max_workers: Maximum number of workers (default: CPU count based)

        Returns:
            Self for method chaining

        Note:
            ThreadPool is recommended for most cases as it handles I/O-bound
            file operations well. ProcessPool may have overhead for small jobs.
        """
        if isinstance(executor_type, str):
            executor_type = ExecutorType(executor_type)
        self._executor_type = executor_type
        self._max_workers = max_workers
        return self

    def with_fit_mode(self, mode: FitMode | str) -> Self:
        """Set how aspect ratio is handled when resizing.

        Args:
            mode: Fit mode - 'cover' (crop to fill), 'contain' (pad to fit),
                  or 'stretch' (distort to fill)

        Returns:
            Self for method chaining

        Note:
            - 'cover' (default): Best for icons, crops overflow
            - 'contain': Shows full image with padding
            - 'stretch': Legacy behavior, may distort
        """
        if isinstance(mode, str):
            mode = FitMode(mode)
        self._fit_mode = mode
        return self

    def generate(self, output_dir: str | Path) -> list[Path]:
        """Execute the pipeline and generate all outputs.

        Args:
            output_dir: Directory to write output files

        Returns:
            List of paths to generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Collect all output specs
        all_outputs = list(self.outputs)
        if self.preset_config:
            all_outputs.extend(self.preset_config.outputs)

        if not all_outputs:
            raise ValueError("No outputs specified. Use with_preset() or with_output().")

        # Load source image
        source_image = self._load_source()

        # Apply color transformations if specified
        if self.colors.background:
            source_image = self.backend.apply_background(source_image, self.colors.background)

        # Separate SVG outputs (just copy) from raster outputs (need processing)
        svg_outputs = [o for o in all_outputs if o.format == "svg"]
        raster_outputs = [o for o in all_outputs if o.format != "svg"]

        generated_files: list[Path] = []

        # Generate raster outputs (potentially in parallel)
        with create_executor(self._executor_type, self._max_workers) as executor:
            if self._executor_type == ExecutorType.SEQUENTIAL:
                # Sequential execution
                for spec in raster_outputs:
                    output_file = output_path / spec.name
                    generated_files.append(
                        self._generate_output(source_image, spec, output_file)
                    )
            else:
                # Parallel execution
                futures: dict[Future[Path], OutputSpec] = {}
                for spec in raster_outputs:
                    output_file = output_path / spec.name
                    future = executor.submit(
                        self._generate_output, source_image, spec, output_file
                    )
                    futures[future] = spec

                # Collect results as they complete
                for future in as_completed(futures):
                    try:
                        result_path = future.result()
                        generated_files.append(result_path)
                    except Exception as e:
                        spec = futures[future]
                        raise RuntimeError(f"Failed to generate {spec.name}: {e}") from e

        # Copy SVG files (simple file copy, no parallelism needed)
        for svg_spec in svg_outputs:
            svg_dest = output_path / svg_spec.name
            svg_dest.write_bytes(self.source.read_bytes())
            generated_files.append(svg_dest)

        # Generate manifest if requested (after all outputs are done)
        if self._generate_manifest:
            manifest_path = self._generate_manifest_file(output_path, all_outputs)
            generated_files.append(manifest_path)

        return generated_files

    def _load_source(self):
        """Load the source file using the appropriate method."""
        suffix = self.source.suffix.lower()
        if suffix == ".svg":
            # Load at a large size for quality, we'll resize for each output
            return self.backend.load_svg(self.source, width=1024)
        else:
            return self.backend.load_image(self.source)

    def _generate_output(self, source_image, spec: OutputSpec, output_file: Path) -> Path:
        """Generate a single output file."""
        # Resize to target dimensions using the configured fit mode
        width, height = spec.size
        img_copy = self.backend.copy(source_image)

        match self._fit_mode:
            case FitMode.COVER:
                resized = self.backend.resize_cover(img_copy, width, height)
            case FitMode.CONTAIN:
                bg = self.colors.background or "#00000000"
                resized = self.backend.resize_contain(img_copy, width, height, bg)
            case FitMode.STRETCH:
                resized = self.backend.resize(img_copy, width, height)

        # Export based on format
        if spec.format == "png":
            self.backend.export_png(resized, output_file)
        elif spec.format == "ico":
            self.backend.export_ico(source_image, output_file)
        elif spec.format == "svg":
            # SVG copying handled separately in generate()
            pass
        else:
            raise ValueError(f"Unsupported format: {spec.format}")

        return output_file

    def _generate_manifest_file(self, output_dir: Path, outputs: list[OutputSpec]) -> Path:
        """Generate site.webmanifest file."""
        import json

        # Find icon-appropriate outputs for manifest
        icon_outputs = [
            o for o in outputs if o.format == "png" and o.width in [192, 512, 180, 32, 16]
        ]

        icons = []
        for output in icon_outputs:
            icon_entry = {
                "src": f"/{output.name}",
                "sizes": f"{output.width}x{output.height or output.width}",
                "type": "image/png",
            }
            # Mark large icons as maskable
            if output.width >= 192:
                icon_entry["purpose"] = "any maskable"
            icons.append(icon_entry)

        manifest = {
            "name": "",
            "short_name": "",
            "icons": icons,
            "theme_color": self.colors.foreground or "#ffffff",
            "background_color": self.colors.background or "#ffffff",
            "display": "standalone",
        }

        manifest_path = output_dir / "site.webmanifest"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        return manifest_path

    def to_config(self, output_dir: str | Path) -> PipelineConfig:
        """Export current pipeline configuration as a PipelineConfig object.

        Args:
            output_dir: Output directory to include in config

        Returns:
            PipelineConfig representing current pipeline state
        """
        all_outputs = list(self.outputs)
        if self.preset_config:
            all_outputs.extend(self.preset_config.outputs)

        return PipelineConfig(
            source=self.source,
            output_dir=Path(output_dir),
            colors=self.colors,
            preset=self.preset_config.name if self.preset_config else None,
            outputs=all_outputs,
        )
