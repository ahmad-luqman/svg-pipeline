# SVG Pipeline

Transform SVG sources into all required derivative formats with a single command.

## Features

- Generate complete favicon sets (ICO, PNG, SVG)
- Create PWA icons (apple-touch-icon, android-chrome)
- Export Open Graph images for social sharing
- Support for color theming
- Built-in presets for common use cases
- Extensible backend architecture
- Use as CLI or Python library

## Installation

```bash
pip install svg-pipeline
```

Or install from source:

```bash
git clone https://github.com/svg-pipeline/svg-pipeline
cd svg-pipeline
pip install -e ".[dev]"
```

## Quick Start

### CLI Usage

```bash
# Generate web assets with defaults
svg-pipeline generate ./logo.svg -o ./assets

# Use a specific preset
svg-pipeline generate ./logo.svg --preset web -o ./assets

# Apply color theme
svg-pipeline generate ./logo.svg --bg "#282a36" --fg "#f8f8f2" -o ./assets

# Generate from built-in template
svg-pipeline template silhouette --bg "#282a36" -o ./assets

# List available presets
svg-pipeline list-presets

# List available templates
svg-pipeline list-templates
```

### Library Usage

```python
from svg_pipeline import Pipeline

# Basic usage with preset
Pipeline("logo.svg").with_preset("web").generate("./output")

# With color theme
Pipeline("logo.svg") \
    .with_preset("web") \
    .with_colors(background="#282a36") \
    .generate("./output")

# Custom outputs
Pipeline("logo.svg") \
    .with_output("icon-64.png", "png", 64) \
    .with_output("icon-128.png", "png", 128) \
    .generate("./output")
```

## Presets

| Preset | Description |
|--------|-------------|
| `web` | Standard favicon set + PWA icons + OG image |
| `mobile` | iOS + Android app icon sets |
| `full` | Everything: web + mobile combined |

### Web Preset Output

```
output/
├── favicon.svg
├── favicon.ico
├── favicon-16x16.png
├── favicon-32x32.png
├── apple-touch-icon.png
├── android-chrome-192x192.png
├── android-chrome-512x512.png
├── og-image.png
└── site.webmanifest
```

## Architecture

SVG Pipeline is designed with extensibility in mind:

- **Backends**: Swappable image processing engines (Pillow default, OpenCV optional)
- **Transforms**: Modular image transformations (resize, color, convert)
- **Exporters**: Format-specific export handlers (PNG, ICO, manifest)
- **Presets**: YAML-based output configurations

### Creating Custom Presets

Create a YAML file in `~/.config/svg-pipeline/presets/`:

```yaml
name: my-preset
description: My custom preset

outputs:
  - name: icon-small.png
    format: png
    width: 32
    height: 32

  - name: icon-large.png
    format: png
    width: 512
    height: 512
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/

# Type checking
mypy src/
```

## Roadmap

- [ ] OpenCV backend for advanced transformations
- [ ] GPU-accelerated processing
- [ ] ML-powered silhouette extraction
- [ ] Parallel export execution
- [ ] Watch mode for development
- [ ] Plugin system for custom transforms

## License

MIT License - see [LICENSE](LICENSE) for details.
