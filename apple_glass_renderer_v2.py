# © 2026 Ranuk IT Solutions — ranuk.dev
"""
apple_glass_renderer_v2.py — Ultra-Refined Apple Vision Pro / Keynote Glassmorphic Engine.
"""
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path("/Users/emilioranucoli/Apps/ranuk-ai-debate-studio")
BRAND_DIR = REPO_ROOT / "assets" / "brand"


def load_apple_font(font_type: str = "display", size: int = 24) -> ImageFont.FreeTypeFont:
    paths = {
        "display": "/System/Library/Fonts/SFNS.ttf",
        "rounded": "/System/Library/Fonts/SFNSRounded.ttf",
        "mono": "/System/Library/Fonts/SFNSMono.ttf",
        "keynote": "/System/Library/Fonts/Avenir Next.ttc",
    }
    target = paths.get(font_type, "/System/Library/Fonts/SFNS.ttf")
    try:
        return ImageFont.truetype(target, size=size)
    except Exception:
        return ImageFont.load_default()


def load_ranuk_apple_logo(size: int = 40) -> Optional[Image.Image]:
    path = BRAND_DIR / "minilogo.png"
    if not path.exists():
        path = Path.home() / "Downloads" / "minilogo.png"
    if path.exists():
        try:
            raw = Image.open(path).convert("RGB")
            arr = np.array(raw, dtype=np.float32)
            lum = np.max(arr, axis=2)
            alpha = np.clip((lum - 14.0) * 2.4, 0.0, 255.0).astype(np.uint8)
            rgba = np.dstack([arr.astype(np.uint8), alpha])
            img = Image.fromarray(rgba, mode="RGBA")
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            ox = (size - img.width) // 2
            oy = (size - img.height) // 2
            canvas.paste(img, (ox, oy), img)
            return canvas
        except Exception:
            pass
    return None


def create_vibrant_apple_aurora(width: int, height: int, phase: float = 0.0) -> Image.Image:
    """Rich, luminous Apple Vision Pro chromatic mesh gradient."""
    y, x = np.mgrid[:height, :width]
    # Deep obsidian baseline
    base_grad = (4.0 + 7.0 * (y / float(height))).astype(np.uint8)
    base_img = Image.fromarray(np.dstack([base_grad, base_grad + 1, base_grad + 6, np.full((height, width), 255, dtype=np.uint8)]), mode="RGBA")

    # Spot 1: Electric Cyan Aurora behind Left Speaker
    cx1, cy1 = int(width * 0.25), int(height * 0.38)
    dist1 = np.sqrt((x - cx1) ** 2 + (y - cy1) ** 2)
    alpha1 = (np.clip(1.0 - dist1 / 440.0, 0.0, 1.0) ** 2.0) * 110.0

    # Spot 2: Apple Royal Indigo / Violet behind Center
    cx2, cy2 = int(width * 0.50), int(height * 0.22)
    dist2 = np.sqrt((x - cx2) ** 2 + (y - cy2) ** 2)
    alpha2 = (np.clip(1.0 - dist2 / 460.0, 0.0, 1.0) ** 2.2) * 95.0

    # Spot 3: Apple Neon Emerald behind Right Speaker
    cx3, cy3 = int(width * 0.75), int(height * 0.38)
    dist3 = np.sqrt((x - cx3) ** 2 + (y - cy3) ** 2)
    alpha3 = (np.clip(1.0 - dist3 / 440.0, 0.0, 1.0) ** 2.0) * 110.0

    r = np.clip(alpha1 * 0.02 + alpha2 * 0.55 + alpha3 * 0.08, 0, 255).astype(np.uint8)
    g = np.clip(alpha1 * 0.90 + alpha2 * 0.22 + alpha3 * 0.92, 0, 255).astype(np.uint8)
    b = np.clip(alpha1 * 1.00 + alpha2 * 0.98 + alpha3 * 0.55, 0, 255).astype(np.uint8)
    a = np.clip(alpha1 + alpha2 + alpha3, 0, 205).astype(np.uint8)

    aurora = Image.fromarray(np.dstack([r, g, b, a]), mode="RGBA").filter(ImageFilter.GaussianBlur(24))
    combined = Image.alpha_composite(base_img, aurora)

    # Add ultra-subtle architectural grid
    grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid)
    for gx in range(0, width, 48):
        gdraw.line([(gx, 0), (gx, height)], fill=(255, 255, 255, 6), width=1)
    for gy in range(0, height, 48):
        gdraw.line([(0, gy), (width, gy)], fill=(255, 255, 255, 6), width=1)
    return Image.alpha_composite(combined, grid)


def draw_apple_frosted_card(
    draw: ImageDraw.ImageDraw,
    rect: Tuple[int, int, int, int],
    radius: int = 30,
    is_active: bool = False,
    active_color: Tuple[int, int, int] = (0, 240, 255),
) -> None:
    """Apple Vision Pro frosted glass card with 3D specular highlight refraction."""
    x0, y0, x1, y1 = rect
    # 1. Dark translucent frosted glass slab
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=(12, 17, 28, 160))

    # 2. Specular border (light refraction)
    if is_active:
        # Luminous active border
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(*active_color, 195), width=2)
        # Specular top rim sheen
        draw.rounded_rectangle([x0 + 4, y0 + 1, x1 - 4, y0 + 3], radius=radius, fill=(255, 255, 255, 120))
    else:
        # Subtle dormant glass rim
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(255, 255, 255, 32), width=1)
        draw.rounded_rectangle([x0 + 6, y0 + 1, x1 - 6, y0 + 2], radius=radius, fill=(255, 255, 255, 65))


def draw_apple_siri_orb(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    rms: float,
    speaking: bool,
    primary_color: Tuple[int, int, int],
    secondary_color: Tuple[int, int, int],
    phase: float = 0.0,
) -> None:
    """Apple Siri-style 3D iridescent glowing sphere."""
    if speaking:
        # Multi-layer breathing acoustic fields
        for ring in [3, 2, 1]:
            r_boost = int(ring * (8 + rms * 14) + math.sin(phase * 3.5 + ring) * 3)
            alpha = max(12, int((65 - ring * 16) * (0.6 + rms * 0.4)))
            draw.ellipse(
                [cx - (radius + r_boost), cy - (radius + r_boost), cx + (radius + r_boost), cy + (radius + r_boost)],
                fill=(*primary_color, alpha // 4),
                outline=(*primary_color, alpha),
                width=1,
            )

    # Core 3D Sphere with layered gradient rings
    r_core = radius + int(rms * 4 if speaking else 0)
    for step in range(r_core, 0, -3):
        frac = step / float(r_core)
        col = (
            int(primary_color[0] * frac + secondary_color[0] * (1 - frac)),
            int(primary_color[1] * frac + secondary_color[1] * (1 - frac)),
            int(primary_color[2] * frac + secondary_color[2] * (1 - frac)),
        )
        alpha = int(220 if speaking else 140)
        draw.ellipse([cx - step, cy - step, cx + step, cy + step], fill=(*col, alpha))

    # Specular upper glass sheen (Apple glass reflection)
    sheen_box = [cx - int(r_core * 0.75), cy - int(r_core * 0.75), cx + int(r_core * 0.75), cy + int(r_core * 0.75)]
    draw.arc(sheen_box, start=210, end=330, fill=(255, 255, 255, 180 if speaking else 90), width=3)


def draw_apple_music_waveform(
    draw: ImageDraw.ImageDraw,
    x_start: int,
    y_center: int,
    bar_count: int,
    bar_width: int,
    bar_gap: int,
    bands: np.ndarray,
    speaking: bool,
    color_top: Tuple[int, int, int],
    color_bot: Tuple[int, int, int],
    max_height: int = 70,
) -> None:
    """Organic Gaussian-smoothed Apple Music audio pills with soft mirrored floor reflection."""
    smoothed = np.convolve(bands, [0.22, 0.56, 0.22], mode="same")
    for idx in range(bar_count):
        val = float(smoothed[idx])
        bx = x_start + idx * (bar_width + bar_gap)
        if speaking:
            h = int(6 + val * max_height)
            alpha = 245
        else:
            h = int(3 + val * 12)
            alpha = 65

        # Upper pill
        draw.rounded_rectangle(
            [bx, y_center - h, bx + bar_width, y_center + h],
            radius=bar_width // 2,
            fill=(*color_top, alpha),
        )
        # Mirrored floor reflection
        ref_h = int(h * 0.38)
        draw.rounded_rectangle(
            [bx, y_center + h + 6, bx + bar_width, y_center + h + 6 + ref_h],
            radius=bar_width // 2,
            fill=(*color_bot, alpha // 4),
        )


def render_preview_v2(output_path: Path) -> Path:
    width, height = 1280, 720
    bg = create_vibrant_apple_aurora(width, height, phase=1.2)
    logo = load_ranuk_apple_logo(size=38)

    f_large_title = load_apple_font("keynote", size=32)
    f_sub = load_apple_font("display", size=15)
    f_island = load_apple_font("rounded", size=13)
    f_speaker = load_apple_font("display", size=22)
    f_role = load_apple_font("display", size=13)
    f_quote = load_apple_font("display", size=20)
    f_status = load_apple_font("rounded", size=11)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Apple Dynamic Island (Top Center)
    island_w, island_h = 560, 48
    ix0 = (width - island_w) // 2
    iy0 = 22
    draw.rounded_rectangle([ix0, iy0, ix0 + island_w, iy0 + island_h], radius=24, fill=(8, 12, 20, 235), outline=(255, 255, 255, 38), width=1)
    draw.rounded_rectangle([ix0 + 16, iy0 + 1, ix0 + island_w - 16, iy0 + 2], radius=20, fill=(255, 255, 255, 75))

    if logo:
        overlay.paste(logo, (ix0 + 12, iy0 + 5), logo)

    draw.text((ix0 + 58, iy0 + 15), "RANUK IT SOLUTIONS  •  AI DEBATE STUDIO", fill=(255, 255, 255, 245), font=f_island)

    # Dynamic Island Warning Pill
    draw.rounded_rectangle([ix0 + island_w - 200, iy0 + 9, ix0 + island_w - 12, iy0 + island_h - 9], radius=15, fill=(251, 191, 36, 35), outline=(251, 191, 36, 185), width=1)
    draw.text((ix0 + island_w - 188, iy0 + 17), "● LIVE FULL-DUPLEX (180ms)", fill=(254, 243, 199, 255), font=f_status)

    # 2. Keynote Title & Subtitle
    draw.text((54, 88), "¿LA IA REEMPLAZARÁ A LOS INGENIEROS EN 2026?", fill=(255, 255, 255, 255), font=f_large_title)
    draw.text((54, 126), "Agentes Autónomos de Código vs. Arquitectura Humana en Producción  •  Episodio 01", fill=(156, 163, 175, 235), font=f_sub)

    # 3. Two Apple Frosted Glass Cards (Clean inside padding)
    card_y0, card_y1 = 168, 516
    card_w = 566

    # Pod A (Left - Mateo Vega)
    card_a = (54, card_y0, 54 + card_w, card_y1)
    draw_apple_frosted_card(draw, card_a, radius=28, is_active=True, active_color=(0, 240, 255))
    draw_apple_siri_orb(draw, 114, 232, 28, rms=0.75, speaking=True, primary_color=(0, 240, 255), secondary_color=(59, 130, 246), phase=1.0)
    draw.text((166, 212), "Mateo Vega", fill=(255, 255, 255, 255), font=f_speaker)
    draw.text((166, 242), "CTO & Arquitecto de Sistemas Críticos", fill=(156, 163, 175, 220), font=f_role)
    draw.rounded_rectangle([166, 268, 330, 292], radius=12, fill=(0, 240, 255, 24), outline=(0, 240, 255, 120), width=1)
    draw.text((178, 273), "● CANAL IZQUIERDO (FL)", fill=(165, 243, 252, 255), font=f_status)

    sim_bands_a = np.array([0.15, 0.4, 0.75, 0.9, 0.85, 0.65, 0.45, 0.35, 0.25, 0.3, 0.5, 0.7, 0.82, 0.65, 0.45, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05, 0.05, 0.05, 0.05], dtype=np.float32)
    draw_apple_music_waveform(draw, 84, 408, 24, bar_width=12, bar_gap=8, bands=sim_bands_a, speaking=True, color_top=(0, 240, 255), color_bot=(59, 130, 246), max_height=65)

    # Pod B (Right - Sofía Kovács)
    card_b = (width - 54 - card_w, card_y0, width - 54, card_y1)
    draw_apple_frosted_card(draw, card_b, radius=28, is_active=True, active_color=(16, 235, 155))
    draw_apple_siri_orb(draw, width - 54 - card_w + 60, 232, 28, rms=0.68, speaking=True, primary_color=(16, 235, 155), secondary_color=(5, 150, 105), phase=2.0)
    draw.text((width - 54 - card_w + 112, 212), "Sofía Kovács", fill=(255, 255, 255, 255), font=f_speaker)
    draw.text((width - 54 - card_w + 112, 242), "Lead AI Agent Engineer • Ranuk Lab", fill=(156, 163, 175, 220), font=f_role)
    draw.rounded_rectangle([width - 54 - card_w + 112, 268, width - 54 - card_w + 276, 292], radius=12, fill=(16, 235, 155, 24), outline=(16, 235, 155, 120), width=1)
    draw.text((width - 54 - card_w + 124, 273), "● CANAL DERECHO (FR)", fill=(167, 243, 208, 255), font=f_status)

    sim_bands_b = np.array([0.05, 0.1, 0.25, 0.55, 0.75, 0.88, 0.72, 0.58, 0.42, 0.35, 0.48, 0.65, 0.78, 0.62, 0.45, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05, 0.05, 0.05, 0.05], dtype=np.float32)
    draw_apple_music_waveform(draw, width - 54 - card_w + 30, 408, 24, bar_width=12, bar_gap=8, bands=sim_bands_b, speaking=True, color_top=(16, 235, 155), color_bot=(5, 150, 105), max_height=65)

    # 4. Apple Keynote Subtitle Bar (Bottom Stage)
    sub_rect = (54, 538, width - 54, 692)
    draw_apple_frosted_card(draw, sub_rect, radius=24, is_active=True, active_color=(0, 240, 255))

    # Speaker Pill
    draw.rounded_rectangle([80, 556, 240, 586], radius=15, fill=(0, 240, 255, 28), outline=(0, 240, 255, 160), width=1)
    draw.text((94, 562), "SOFÍA KOVÁCS", fill=(255, 255, 255, 255), font=f_island)
    draw.text((254, 562), "•  INTERRUPCIÓN FULL-DUPLEX (180ms)", fill=(0, 240, 255, 240), font=f_island)
    draw.text((width - 320, 562), "t = 08.24s  •  ranuk.dev/debates", fill=(156, 163, 175, 200), font=f_status)

    draw.text((80, 604), "“¡Espera, Mateo! Ese era el debate de hace dos años. Hoy un enjambre de agentes", fill=(255, 255, 255, 255), font=f_quote)
    draw.text((80, 634), "detecta el fallo, valida el árbol sintáctico y despliega el parche en segundos.”", fill=(243, 244, 246, 245), font=f_quote)

    # Progress Capsule Bar
    draw.rounded_rectangle([80, 676, width - 80, 680], radius=2, fill=(255, 255, 255, 30))
    draw.rounded_rectangle([80, 676, 80 + 480, 680], radius=2, fill=(0, 240, 255, 240))

    final_img = Image.alpha_composite(bg, overlay)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_img.save(str(output_path), "PNG")
    return output_path


if __name__ == "__main__":
    out = Path("/Users/emilioranucoli/Apps/ranuk-ai-debate-studio/assets/preview_apple_glass_v2.png")
    render_preview_v2(out)
    print("Rendered v2:", out)
