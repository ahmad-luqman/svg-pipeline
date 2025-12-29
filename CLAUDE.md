# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (requires Cairo library)
DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/opt/cairo/lib:$DYLD_FALLBACK_LIBRARY_PATH" pytest

# Run single test
DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/opt/cairo/lib" pytest tests/test_pipeline.py::TestPipeline::test_pipeline_generate -v

# Linting
ruff check src/

# Type checking
mypy src/

# Run CLI
DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/opt/cairo/lib" svg-pipeline generate examples/logo.svg -o examples/output
```

**Note**: CairoSVG requires the native Cairo library. On macOS: `brew install cairo`. The `DYLD_FALLBACK_LIBRARY_PATH` is needed for Python to find it.

## Architecture

SVG Pipeline transforms SVG/image sources into derivative formats (favicons, PWA icons, OG images).

### Core Design Patterns

**Fluent API Pipeline**: The `Pipeline` class uses method chaining for configuration:
```python
Pipeline("logo.svg").with_preset("web").with_colors(bg="#000").with_parallel().generate("./out")
```

**Swappable Backends**: Abstract `Backend` class (`backends/base.py`) defines the image processing interface. `PillowBackend` is the default implementation. New backends (OpenCV, GPU) implement the same interface.

**Executor Abstraction**: `executor.py` provides `SequentialExecutor`, `ThreadPoolTaskExecutor`, and `ProcessPoolTaskExecutor` for parallel export. Pipeline uses this via `with_parallel()`.

### Key Components

- **`pipeline.py`**: Core orchestration. Loads source, applies transforms, dispatches to executor, generates outputs.
- **`backends/pillow.py`**: Image operations (load SVG via CairoSVG, resize with fit modes, export PNG/ICO).
- **`config.py`**: Pydantic models for `OutputSpec`, `PresetConfig`, `PipelineConfig`.
- **`presets/*.yaml`**: Declarative output specifications (web, mobile, full).
- **`cli.py`**: Typer CLI wrapping the Pipeline class.

### Fit Modes (Aspect Ratio Handling)

When resizing non-square images to square outputs:
- `cover` (default): Center-crop to fill, no distortion
- `contain`: Fit with padding
- `stretch`: Distort to fill (legacy)

### Adding New Features

- **New output format**: Add exporter in `exporters/`, update `_generate_output()` in pipeline.py
- **New preset**: Add YAML file in `presets/`
- **New backend**: Implement `Backend` ABC in `backends/`
- **New transform**: Add module in `transforms/`, wire into pipeline
