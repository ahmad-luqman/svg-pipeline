"""Web manifest generator."""

import json
from pathlib import Path

from svg_pipeline.config import OutputSpec


class ManifestExporter:
    """Generator for site.webmanifest files."""

    def __init__(
        self,
        name: str = "",
        short_name: str = "",
        theme_color: str = "#ffffff",
        background_color: str = "#ffffff",
        display: str = "standalone",
    ):
        """Initialize manifest generator.

        Args:
            name: Application name
            short_name: Short application name
            theme_color: Theme color for browser UI
            background_color: Background color for splash screen
            display: Display mode (standalone, fullscreen, etc.)
        """
        self.name = name
        self.short_name = short_name
        self.theme_color = theme_color
        self.background_color = background_color
        self.display = display

    def generate(self, outputs: list[OutputSpec], output_dir: Path) -> Path:
        """Generate site.webmanifest file.

        Args:
            outputs: List of generated output specifications
            output_dir: Directory to write manifest

        Returns:
            Path to generated manifest file
        """
        # Filter for PNG outputs suitable as icons
        icon_outputs = [o for o in outputs if o.format == "png"]

        icons = []
        for output in icon_outputs:
            icon_entry = {
                "src": f"/{output.name}",
                "sizes": f"{output.width}x{output.height or output.width}",
                "type": "image/png",
            }
            # Mark large icons as maskable (PWA requirement)
            if output.width >= 192:
                icon_entry["purpose"] = "any maskable"
            icons.append(icon_entry)

        manifest = {
            "name": self.name,
            "short_name": self.short_name,
            "icons": icons,
            "theme_color": self.theme_color,
            "background_color": self.background_color,
            "display": self.display,
        }

        manifest_path = output_dir / "site.webmanifest"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        return manifest_path

    def __repr__(self) -> str:
        return f"ManifestExporter(name={self.name!r})"
