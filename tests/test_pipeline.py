"""Tests for the core Pipeline functionality."""

import tempfile
from pathlib import Path

import pytest

from svg_pipeline import Pipeline
from svg_pipeline.backends.pillow import PillowBackend
from svg_pipeline.config import OutputSpec, PresetConfig
from svg_pipeline.presets import list_presets, load_preset


# Path to example SVG for testing
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
LOGO_SVG = EXAMPLES_DIR / "logo.svg"


class TestPillowBackend:
    """Tests for the Pillow backend."""

    def test_load_svg(self):
        """Test loading an SVG file."""
        backend = PillowBackend()
        image = backend.load_svg(LOGO_SVG, width=100)
        assert image is not None
        assert backend.get_size(image) == (100, 100)

    def test_resize(self):
        """Test resizing an image."""
        backend = PillowBackend()
        image = backend.load_svg(LOGO_SVG, width=100)
        resized = backend.resize(image, 50, 50)
        assert backend.get_size(resized) == (50, 50)

    def test_export_png(self):
        """Test exporting as PNG."""
        backend = PillowBackend()
        image = backend.load_svg(LOGO_SVG, width=100)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"
            backend.export_png(image, output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_export_ico(self):
        """Test exporting as ICO."""
        backend = PillowBackend()
        image = backend.load_svg(LOGO_SVG, width=100)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.ico"
            backend.export_ico(image, output_path, sizes=[16, 32])
            assert output_path.exists()
            assert output_path.stat().st_size > 0


class TestPresets:
    """Tests for preset loading."""

    def test_list_presets(self):
        """Test listing available presets."""
        presets = list_presets()
        assert "web" in presets
        assert "mobile" in presets
        assert "full" in presets

    def test_load_web_preset(self):
        """Test loading the web preset."""
        preset = load_preset("web")
        assert preset["name"] == "web"
        assert "outputs" in preset
        assert len(preset["outputs"]) > 0

    def test_load_invalid_preset(self):
        """Test that loading invalid preset raises error."""
        with pytest.raises(ValueError, match="not found"):
            load_preset("nonexistent")


class TestPipeline:
    """Tests for the Pipeline class."""

    def test_pipeline_init(self):
        """Test pipeline initialization."""
        pipeline = Pipeline(LOGO_SVG)
        assert pipeline.source == LOGO_SVG
        assert isinstance(pipeline.backend, PillowBackend)

    def test_pipeline_with_preset(self):
        """Test setting a preset."""
        pipeline = Pipeline(LOGO_SVG).with_preset("web")
        assert pipeline.preset_config is not None
        assert pipeline.preset_config.name == "web"

    def test_pipeline_with_colors(self):
        """Test setting colors."""
        pipeline = Pipeline(LOGO_SVG).with_colors(
            foreground="#ffffff", background="#000000"
        )
        assert pipeline.colors.foreground == "#ffffff"
        assert pipeline.colors.background == "#000000"

    def test_pipeline_generate(self):
        """Test generating assets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            pipeline = Pipeline(LOGO_SVG).with_preset("web")
            generated = pipeline.generate(output_dir)

            assert len(generated) > 0
            # Check some expected files
            assert (output_dir / "favicon.ico").exists()
            assert (output_dir / "favicon-32x32.png").exists()
            assert (output_dir / "apple-touch-icon.png").exists()

    def test_pipeline_custom_output(self):
        """Test adding custom output specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            pipeline = (
                Pipeline(LOGO_SVG)
                .with_output("custom-64.png", "png", 64)
                .with_output("custom-128.png", "png", 128)
            )
            generated = pipeline.generate(output_dir)

            assert (output_dir / "custom-64.png").exists()
            assert (output_dir / "custom-128.png").exists()

    def test_pipeline_nonexistent_source(self):
        """Test that nonexistent source raises error."""
        with pytest.raises(FileNotFoundError):
            Pipeline("/nonexistent/path.svg")


class TestConfig:
    """Tests for configuration models."""

    def test_output_spec_size(self):
        """Test OutputSpec size property."""
        spec = OutputSpec(name="test.png", format="png", width=100)
        assert spec.size == (100, 100)

        spec_rect = OutputSpec(name="test.png", format="png", width=100, height=50)
        assert spec_rect.size == (100, 50)

    def test_preset_config(self):
        """Test PresetConfig model."""
        config = PresetConfig(
            name="test",
            outputs=[
                OutputSpec(name="a.png", format="png", width=32),
                OutputSpec(name="b.png", format="png", width=64),
            ],
        )
        assert len(config.outputs) == 2
