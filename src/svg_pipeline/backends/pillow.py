"""Pillow-based image processing backend."""

from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

from svg_pipeline.backends.base import Backend


def hex_to_rgba(hex_color: str) -> tuple[int, int, int, int]:
    """Convert hex color string to RGBA tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (r, g, b, 255)
    elif len(hex_color) == 8:
        r, g, b, a = (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
            int(hex_color[6:8], 16),
        )
        return (r, g, b, a)
    raise ValueError(f"Invalid hex color: {hex_color}")


class PillowBackend(Backend):
    """Pillow/PIL-based image processing backend.

    This is the default backend, using Pillow for raster operations and
    CairoSVG for SVG rasterization.
    """

    def load_svg(
        self, path: Path, width: int | None = None, height: int | None = None
    ) -> Image.Image:
        """Load and rasterize an SVG file using CairoSVG."""
        png_data = cairosvg.svg2png(
            url=str(path),
            output_width=width,
            output_height=height,
        )
        return Image.open(BytesIO(png_data)).convert("RGBA")

    def load_image(self, path: Path) -> Image.Image:
        """Load a raster image file."""
        return Image.open(path).convert("RGBA")

    def resize(self, image: Image.Image, width: int, height: int) -> Image.Image:
        """Resize image using high-quality Lanczos resampling (stretches to fit)."""
        return image.resize((width, height), Image.Resampling.LANCZOS)

    def resize_cover(self, image: Image.Image, width: int, height: int) -> Image.Image:
        """Resize and center-crop to exactly fill target dimensions.

        Maintains aspect ratio by cropping the overflow. Best for icons where
        you want the image to fill the entire space without distortion.
        """
        src_w, src_h = image.size
        src_ratio = src_w / src_h
        target_ratio = width / height

        if src_ratio > target_ratio:
            # Source is wider - crop sides
            new_h = src_h
            new_w = int(src_h * target_ratio)
            left = (src_w - new_w) // 2
            crop_box = (left, 0, left + new_w, new_h)
        else:
            # Source is taller - crop top/bottom
            new_w = src_w
            new_h = int(src_w / target_ratio)
            top = (src_h - new_h) // 2
            crop_box = (0, top, new_w, top + new_h)

        cropped = image.crop(crop_box)
        return cropped.resize((width, height), Image.Resampling.LANCZOS)

    def resize_contain(
        self, image: Image.Image, width: int, height: int, bg_color: str = "#00000000"
    ) -> Image.Image:
        """Resize to fit within bounds, padding with background color.

        Maintains aspect ratio by adding padding. Best for cases where the
        full image must be visible (like OG images for social sharing).
        """
        src_w, src_h = image.size
        src_ratio = src_w / src_h
        target_ratio = width / height

        if src_ratio > target_ratio:
            # Source is wider - fit to width, pad top/bottom
            new_w = width
            new_h = int(width / src_ratio)
        else:
            # Source is taller - fit to height, pad sides
            new_h = height
            new_w = int(height * src_ratio)

        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Create background and paste centered
        rgba = hex_to_rgba(bg_color)
        result = Image.new("RGBA", (width, height), rgba)
        paste_x = (width - new_w) // 2
        paste_y = (height - new_h) // 2
        result.paste(resized, (paste_x, paste_y))
        return result

    def apply_background(self, image: Image.Image, color: str) -> Image.Image:
        """Composite image over a solid background color."""
        rgba = hex_to_rgba(color)
        background = Image.new("RGBA", image.size, rgba)
        return Image.alpha_composite(background, image)

    def recolor(
        self, image: Image.Image, foreground: str | None, background: str | None
    ) -> Image.Image:
        """Recolor image - simple implementation that applies background.

        For more sophisticated recoloring (replacing specific colors), a more
        complex implementation would be needed, potentially using numpy for
        pixel manipulation.
        """
        result = image.copy()

        if background:
            result = self.apply_background(result, background)

        # Note: True foreground recoloring would require analyzing the image
        # to identify foreground pixels. For now, this is a placeholder for
        # future enhancement with ML-based segmentation.

        return result

    def export_png(self, image: Image.Image, path: Path) -> None:
        """Export image as PNG."""
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, "PNG", optimize=True)

    def export_ico(
        self, image: Image.Image, path: Path, sizes: list[int] | None = None
    ) -> None:
        """Export image as ICO with multiple sizes embedded."""
        if sizes is None:
            sizes = [16, 32, 48]

        path.parent.mkdir(parents=True, exist_ok=True)

        # Create resized versions for each size
        ico_images = [self.resize(image, size, size) for size in sizes]

        # Save as ICO - Pillow handles multi-size ICO automatically
        ico_images[0].save(
            path,
            format="ICO",
            sizes=[(s, s) for s in sizes],
            append_images=ico_images[1:] if len(ico_images) > 1 else [],
        )

    def get_size(self, image: Image.Image) -> tuple[int, int]:
        """Get image dimensions."""
        return image.size

    def copy(self, image: Image.Image) -> Image.Image:
        """Create a copy of the image."""
        return image.copy()
