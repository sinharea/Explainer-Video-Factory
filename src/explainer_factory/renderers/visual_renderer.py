"""Visual rendering engine for educational scene graphics.

Generates scene images using Pillow with a rich visual theme system.
Produces 1920x1080 PNG images for each scene, including:
- Gradient backgrounds
- Styled text blocks
- Diagram elements (boxes, arrows, circles)
- Visual emphasis and decorative elements
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from explainer_factory.config import ThemeSettings, VideoSettings
from explainer_factory.exceptions import VisualRenderError
from explainer_factory.logging import get_logger
from explainer_factory.models.scene import Scene, SceneType, VisualElement

logger = get_logger(__name__)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _blend_color(
    c1: tuple[int, int, int],
    c2: tuple[int, int, int],
    factor: float,
) -> tuple[int, int, int]:
    """Blend two colors by a factor (0.0 = c1, 1.0 = c2)."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * factor) for i in range(3))


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font, falling back to default if system fonts unavailable."""
    font_names = [
        "arial.ttf",
        "Arial.ttf",
        "DejaVuSans.ttf",
        "segoeui.ttf",
        "calibri.ttf",
    ]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


class VisualRenderer:
    """Renders scene visuals as high-quality PNG images.

    Uses a theme-aware rendering system with gradient backgrounds,
    styled text, and diagram elements.
    """

    def __init__(
        self,
        video_settings: VideoSettings | None = None,
        theme_settings: ThemeSettings | None = None,
        theme_data: dict | None = None,
    ):
        """Initialize the visual renderer.

        Args:
            video_settings: Video resolution configuration.
            theme_settings: Theme color configuration.
            theme_data: Full theme data dict (overrides theme_settings).
        """
        self.video = video_settings or VideoSettings()
        self.theme_settings = theme_settings or ThemeSettings()

        # Load theme data
        if theme_data:
            self.theme = theme_data
        else:
            self.theme = {
                "colors": {
                    "primary": self.theme_settings.primary_color,
                    "secondary": self.theme_settings.secondary_color,
                    "background": self.theme_settings.bg_color,
                    "text": self.theme_settings.text_color,
                    "accent": self.theme_settings.accent_color,
                },
                "typography": {
                    "title_font_size": 72,
                    "heading_font_size": 48,
                    "body_font_size": 32,
                    "caption_font_size": 24,
                    "subtitle_font_size": 28,
                },
                "layout": {"margin": 80, "padding": 40, "corner_radius": 20},
            }

        self.colors = {k: _hex_to_rgb(v) for k, v in self.theme["colors"].items()}
        self.typography = self.theme["typography"]
        self.layout = self.theme["layout"]

        # Pre-load fonts
        self._fonts = {
            "title": _load_font(self.typography["title_font_size"]),
            "heading": _load_font(self.typography["heading_font_size"]),
            "body": _load_font(self.typography["body_font_size"]),
            "caption": _load_font(self.typography["caption_font_size"]),
        }

        logger.info(
            "visual_renderer.init",
            resolution=f"{self.video.width}x{self.video.height}",
        )

    def render_scene(self, scene: Scene, output_path: Path) -> Path:
        """Render a scene to a PNG image.

        Args:
            scene: Scene to render.
            output_path: Path to write the image.

        Returns:
            Path to the rendered image.

        Raises:
            VisualRenderError: If rendering fails.
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            img = Image.new("RGB", (self.video.width, self.video.height))
            draw = ImageDraw.Draw(img)

            # Draw gradient background
            self._draw_gradient_bg(draw, scene.scene_type)

            # Draw decorative elements
            self._draw_decorations(draw, scene.scene_type)

            # Draw visual elements
            for element in scene.visual_elements:
                self._draw_element(draw, img, element, scene.scene_type)

            # Draw scene number indicator
            self._draw_scene_indicator(draw, scene.scene_id)

            img.save(output_path, "PNG", quality=95)

            scene.visual_path = output_path
            logger.info(
                "visual_renderer.scene_done",
                scene_id=scene.scene_id,
                scene_type=scene.scene_type.value,
                output=str(output_path),
            )
            return output_path

        except Exception as e:
            raise VisualRenderError(
                f"Failed to render scene {scene.scene_id}",
                details={"scene_id": scene.scene_id, "error": str(e)},
            ) from e

    def render_all_scenes(self, scenes: list[Scene], output_dir: Path) -> dict[str, Path]:
        """Render visuals for all scenes.

        Args:
            scenes: List of scenes to render.
            output_dir: Directory for output images.

        Returns:
            Mapping of scene_id -> image path.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, Path] = {}

        logger.info("visual_renderer.batch_start", num_scenes=len(scenes))

        for scene in scenes:
            img_path = output_dir / f"{scene.scene_id}.png"
            self.render_scene(scene, img_path)
            results[scene.scene_id] = img_path

        logger.info("visual_renderer.batch_complete", num_rendered=len(results))
        return results

    # ─── Private rendering methods ──────────────────────────────────

    def _draw_gradient_bg(self, draw: ImageDraw.Draw, scene_type: SceneType) -> None:
        """Draw a gradient background appropriate for the scene type."""
        bg = self.colors.get("background", (15, 23, 42))
        primary = self.colors.get("primary", (79, 70, 229))
        secondary = self.colors.get("secondary", (124, 58, 237))

        # Choose gradient style by scene type
        if scene_type == SceneType.TITLE:
            c1, c2 = primary, secondary
        elif scene_type == SceneType.KEY_POINT:
            c1 = _blend_color(bg, primary, 0.3)
            c2 = _blend_color(bg, secondary, 0.2)
        elif scene_type == SceneType.SUMMARY:
            c1 = _blend_color(bg, self.colors.get("accent", (6, 182, 212)), 0.15)
            c2 = bg
        else:
            c1 = bg
            c2 = _blend_color(bg, primary, 0.08)

        # Draw vertical gradient
        for y in range(self.video.height):
            factor = y / self.video.height
            color = _blend_color(c1, c2, factor)
            draw.line([(0, y), (self.video.width, y)], fill=color)

    def _draw_decorations(self, draw: ImageDraw.Draw, scene_type: SceneType) -> None:
        """Draw decorative elements like subtle lines and shapes."""
        w, h = self.video.width, self.video.height
        accent = self.colors.get("accent", (6, 182, 212))
        faded_accent = (*accent, 40)  # Low opacity

        if scene_type == SceneType.TITLE:
            # Decorative line under title area
            y_line = int(h * 0.72)
            draw.line(
                [(int(w * 0.2), y_line), (int(w * 0.8), y_line)],
                fill=(*accent,),
                width=2,
            )
        elif scene_type == SceneType.DIAGRAM:
            # Grid dots for diagram background
            for x in range(0, w, 60):
                for y in range(0, h, 60):
                    r = 1
                    draw.ellipse(
                        [x - r, y - r, x + r, y + r],
                        fill=_blend_color(
                            self.colors.get("background", (15, 23, 42)),
                            accent,
                            0.15,
                        ),
                    )

        # Bottom accent bar
        bar_h = 4
        draw.rectangle(
            [(0, h - bar_h), (w, h)],
            fill=accent,
        )

    def _draw_element(
        self,
        draw: ImageDraw.Draw,
        img: Image.Image,
        element: VisualElement,
        scene_type: SceneType,
    ) -> None:
        """Draw a single visual element on the canvas."""
        w, h = self.video.width, self.video.height

        # Convert relative position/size to absolute pixels
        cx = int(element.position[0] * w)
        cy = int(element.position[1] * h)
        ew = int(element.size[0] * w)
        eh = int(element.size[1] * h)

        # Resolve color
        if element.color and element.color in self.colors:
            color = self.colors[element.color]
        elif element.color and element.color.startswith("#"):
            color = _hex_to_rgb(element.color)
        else:
            color = self.colors.get("text", (248, 250, 252))

        if element.element_type == "text_block":
            self._draw_text_block(draw, element.content, cx, cy, ew, eh, scene_type, color)
        elif element.element_type == "box":
            self._draw_box(draw, element.content, cx, cy, ew, eh, color)
        elif element.element_type == "arrow":
            self._draw_arrow(draw, cx, cy, ew, color)
        elif element.element_type == "circle":
            self._draw_circle(draw, element.content, cx, cy, min(ew, eh), color)
        elif element.element_type == "icon":
            self._draw_icon(draw, element.content, cx, cy, color)

    def _draw_text_block(
        self,
        draw: ImageDraw.Draw,
        text: str,
        cx: int,
        cy: int,
        max_w: int,
        max_h: int,
        scene_type: SceneType,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a text block with word-wrapping."""
        # Choose font based on scene type and position
        if scene_type == SceneType.TITLE and cy < self.video.height * 0.5:
            font = self._fonts["title"]
        elif cy < self.video.height * 0.25:
            font = self._fonts["heading"]
        else:
            font = self._fonts["body"]

        # Word wrap
        lines = self._wrap_text(text, font, max_w, draw)

        # Calculate total text height
        line_height = font.size + 8 if hasattr(font, "size") else 20
        total_h = len(lines) * line_height

        # Draw centered text
        start_y = cy - total_h // 2
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = cx - tw // 2
            y = start_y + i * line_height
            draw.text((x, y), line, fill=color, font=font)

    def _wrap_text(
        self, text: str, font, max_width: int, draw: ImageDraw.Draw
    ) -> list[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines or [text]

    def _draw_box(
        self,
        draw: ImageDraw.Draw,
        label: str,
        cx: int,
        cy: int,
        w: int,
        h: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a labeled box element."""
        x1, y1 = cx - w // 2, cy - h // 2
        x2, y2 = cx + w // 2, cy + h // 2
        r = min(self.layout["corner_radius"], w // 4, h // 4)

        # Draw rounded rectangle
        draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=(*color, 180), outline=color, width=2)

        # Draw label
        font = self._fonts["caption"]
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(
            (cx - tw // 2, cy - (bbox[3] - bbox[1]) // 2),
            label,
            fill=self.colors.get("text", (248, 250, 252)),
            font=font,
        )

    def _draw_arrow(
        self,
        draw: ImageDraw.Draw,
        cx: int,
        cy: int,
        length: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a horizontal arrow."""
        x1 = cx - length // 2
        x2 = cx + length // 2

        # Arrow line
        draw.line([(x1, cy), (x2, cy)], fill=color, width=3)

        # Arrowhead
        arrow_size = 12
        draw.polygon(
            [(x2, cy), (x2 - arrow_size, cy - arrow_size // 2), (x2 - arrow_size, cy + arrow_size // 2)],
            fill=color,
        )

    def _draw_circle(
        self,
        draw: ImageDraw.Draw,
        label: str,
        cx: int,
        cy: int,
        diameter: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a labeled circle."""
        r = diameter // 2
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline=color,
            width=2,
        )
        if label:
            font = self._fonts["caption"]
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(
                (cx - tw // 2, cy - (bbox[3] - bbox[1]) // 2),
                label,
                fill=color,
                font=font,
            )

    def _draw_icon(
        self,
        draw: ImageDraw.Draw,
        icon_text: str,
        cx: int,
        cy: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw an icon (emoji or symbol)."""
        font = self._fonts["heading"]
        bbox = draw.textbbox((0, 0), icon_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw // 2, cy - th // 2), icon_text, fill=color, font=font)

    def _draw_scene_indicator(self, draw: ImageDraw.Draw, scene_id: str) -> None:
        """Draw a subtle scene number in the bottom corner."""
        font = self._fonts["caption"]
        text_color = _blend_color(
            self.colors.get("background", (15, 23, 42)),
            self.colors.get("text", (248, 250, 252)),
            0.3,
        )
        draw.text(
            (self.video.width - 120, self.video.height - 40),
            scene_id,
            fill=text_color,
            font=font,
        )
