"""Tests for the core Pipeline functionality."""

import tempfile
import time
from pathlib import Path

import pytest

from svg_pipeline import Pipeline
from svg_pipeline.backends.pillow import PillowBackend
from svg_pipeline.config import OutputSpec, PresetConfig
from svg_pipeline.executor import (
    ExecutorType,
    ProcessPoolTaskExecutor,
    SequentialExecutor,
    ThreadPoolTaskExecutor,
    create_executor,
)
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


class TestExecutor:
    """Tests for executor implementations."""

    def test_sequential_executor(self):
        """Test sequential executor runs tasks in order."""
        results = []

        def task(x):
            results.append(x)
            return x * 2

        executor = SequentialExecutor()
        assert executor.submit(task, 5) == 10
        assert results == [5]

    def test_sequential_executor_map(self):
        """Test sequential executor map function."""
        executor = SequentialExecutor()
        results = executor.map(lambda x: x * 2, [1, 2, 3])
        assert results == [2, 4, 6]

    def test_threadpool_executor(self):
        """Test threadpool executor runs tasks concurrently."""
        with ThreadPoolTaskExecutor(max_workers=2) as executor:
            future = executor.submit(lambda x: x * 2, 5)
            assert future.result() == 10

    def test_threadpool_executor_map(self):
        """Test threadpool executor map function."""
        with ThreadPoolTaskExecutor(max_workers=2) as executor:
            results = executor.map(lambda x: x * 2, [1, 2, 3])
            assert results == [2, 4, 6]

    def test_create_executor_sequential(self):
        """Test factory creates sequential executor."""
        executor = create_executor(ExecutorType.SEQUENTIAL)
        assert isinstance(executor, SequentialExecutor)

    def test_create_executor_threadpool(self):
        """Test factory creates threadpool executor."""
        executor = create_executor(ExecutorType.THREADPOOL)
        assert isinstance(executor, ThreadPoolTaskExecutor)
        executor.shutdown()

    def test_create_executor_from_string(self):
        """Test factory accepts string executor type."""
        executor = create_executor("threadpool")
        assert isinstance(executor, ThreadPoolTaskExecutor)
        executor.shutdown()

    def test_executor_context_manager(self):
        """Test executor works as context manager."""
        with create_executor(ExecutorType.THREADPOOL) as executor:
            result = executor.submit(lambda: 42)
            assert result.result() == 42


class TestParallelPipeline:
    """Tests for parallel pipeline execution."""

    def test_pipeline_with_parallel(self):
        """Test enabling parallel execution."""
        pipeline = Pipeline(LOGO_SVG).with_parallel()
        assert pipeline._executor_type == ExecutorType.THREADPOOL

    def test_pipeline_with_parallel_workers(self):
        """Test setting max workers."""
        pipeline = Pipeline(LOGO_SVG).with_parallel(max_workers=4)
        assert pipeline._max_workers == 4

    def test_pipeline_parallel_generate(self):
        """Test parallel generation produces same outputs as sequential."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Generate with parallel execution
            pipeline = Pipeline(LOGO_SVG).with_preset("web").with_parallel()
            generated = pipeline.generate(output_dir)

            assert len(generated) > 0
            # Check expected files exist
            assert (output_dir / "favicon.ico").exists()
            assert (output_dir / "favicon-32x32.png").exists()
            assert (output_dir / "apple-touch-icon.png").exists()
            assert (output_dir / "site.webmanifest").exists()

    def test_pipeline_parallel_custom_outputs(self):
        """Test parallel execution with custom outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            pipeline = (
                Pipeline(LOGO_SVG)
                .with_output("p1.png", "png", 32)
                .with_output("p2.png", "png", 64)
                .with_output("p3.png", "png", 128)
                .with_output("p4.png", "png", 256)
                .with_parallel(max_workers=2)
            )
            generated = pipeline.generate(output_dir)

            assert len(generated) == 4
            for i, size in enumerate([32, 64, 128, 256], 1):
                path = output_dir / f"p{i}.png"
                assert path.exists()

    def test_parallel_vs_sequential_output_parity(self):
        """Test that parallel and sequential produce identical file sets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            seq_dir = Path(tmpdir) / "sequential"
            par_dir = Path(tmpdir) / "parallel"

            # Sequential
            seq_files = (
                Pipeline(LOGO_SVG)
                .with_preset("web")
                .generate(seq_dir)
            )

            # Parallel
            par_files = (
                Pipeline(LOGO_SVG)
                .with_preset("web")
                .with_parallel()
                .generate(par_dir)
            )

            # Same number of files
            assert len(seq_files) == len(par_files)

            # Same file names
            seq_names = {f.name for f in seq_files}
            par_names = {f.name for f in par_files}
            assert seq_names == par_names
