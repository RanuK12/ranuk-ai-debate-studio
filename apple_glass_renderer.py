# © 2026 Ranuk IT Solutions — Apple Glassmorphic Studio Preview
"""
apple_glass_renderer.py — Apple-grade Liquid Glassmorphic Full-Duplex Broadcast Renderer.
Implements:
  - macOS Sonoma / Apple Vision Pro frosted glass with specular highlight refraction borders.
  - Multi-layered chromatic aurora mesh background.
  - Siri-inspired acoustic fluid orbs with specular glass arcs and breathing energy fields.
  - Apple Music smooth liquid capsule waveforms (Gaussian-smoothed envelope).
  - Apple Dynamic Island live interaction hub with glowing state transitions.
  - Native Apple San Francisco typography (SFNS / SFNSRounded / SFNSMono).
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


def create_apple_aurora_background(width: int, height: int, phase: float = 0.0) -> Image.Image:
    """Create a deep OLED obsidian background with diffused Apple Vision Pro aurora mesh gradients."""
    # Deep base gradient
    y, x = np.mgrid[:height, :width]
    base_grad = (5.0 + 8.0 * (y / float(height))).astype(np.uint8)
    base_r = np.clip(base_grad - 1, 0, 255).astype(np.uint8)
    base_g = base_grad
    base_b = np.clip(base_grad + 7, 0, 255).astype(np.uint8)
    base_a = np.full((height, width), 255, dtype=np.uint8)
    base_img = Image.fromarray(np.dstack([base_r, base_g, base_b, base_a]), mode="RGBA")

    # Spot 1: Electric Cyan Aurora top-left
    cx1 = int(width * 0.22 + math.sin(phase * 0.6) * 40)
    cy1 = int(height * 0.28 + math.cos(phase * 0.5) * 30)
    dist1 = np.sqrt((x - cx1) ** 2 + (y - cy1) ** 2)
    alpha1 = (np.clip(1.0 - dist1 / 480.0, 0.0, 1.0) ** 2.2) * 85.0

    # Spot 2: Apple Royal Indigo / Violet top-center
    cx2 = int(width * 0.50 + math.cos(phase * 0.4) * 30)
    cy2 = int(height * 0.15)
    dist2 = np.sqrt((x - cx2) ** 2 + (y - cy2) ** 2)
    alpha2 = (np.clip(1.0 - dist2 / 500.0, 0.0, 1.0) ** 2.4) * 75.0

    # Spot 3: Apple Emerald Mint bottom-right
    cx3 = int(width * 0.78 + math.sin(phase * 0.5) * 40)
    cy3 = int(height * 0.32 + math.cos(phase * 0.7) * 25)
    dist3 = np.sqrt((x - cx3) ** 2 + (y - cy3) ** 2)
    alpha3 = (np.clip(1.0 - dist3 / 480.0, 0.0, 1.0) ** 2.2) * 85.0

    r = np.clip(alpha1 * 0.0 + alpha2 * 0.45 + alpha3 * 0.10, 0, 255).astype(np.uint8)
    g = np.clip(alpha1 * 0.85 + alpha2 * 0.25 + alpha3 * 0.95, 0, 255).astype(np.uint8)
    b = np.clip(alpha1 * 1.0 + alpha2 * 0.95 + alpha3 * 0.55, 0, 255).astype(np.uint8)
    a = np.clip(alpha1 + alpha2 + alpha3, 0, 185).astype(np.uint8)

    aurora_layer = Image.fromarray(np.dstack([r, g, b, a]), mode="RGBA")
    aurora_layer = aurora_layer.filter(ImageFilter.GaussianBlur(16))
    return Image.alpha_composite(base_img, aurora_layer)


def draw_apple_glass_card(
    draw: ImageDraw.ImageDraw,
    rect: Tuple[int, int, int, int],
    radius: int = 28,
    fill_alpha: int = 145,
    is_active: bool = False,
    active_color: Tuple[int, int, int] = (0, 240, 255),
) -> None:
    """
    Draw genuine Apple frosted glass with 3D specular highlight rim:
      - Top edge catches diffused light (semi-transparent white highlight)
      - Left & Right have subtle refractive glow
      - Bottom edge is soft dark
    """
    x0, y0, x1, y1 = rect
    # Glass back fill (dark translucent obsidian)
    base_fill = (15, 21, 35, fill_alpha)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=base_fill)

    # Specular rim
    if is_active:
        # Active rim has radiant chromatic glow
        glow_col = (*active_color, 210)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=glow_col, width=2)
        # Top inner specular light
        draw.rounded_rectangle([x0 + 1, y0 + 1, x1 - 1, y0 + 3], radius=radius, fill=(255, 255, 255, 85))
    else:
        # Dormant glass rim: delicate refractive light
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(255, 255, 255, 28), width=1)
        # Specular top light
        draw.rounded_rectangle([x0 + 2, y0 + 1, x1 - 2, y0 + 2], radius=radius, fill=(255, 255, 255, 50))


def draw_siri_fluid_orb(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    rms: float,
    speaking: bool,
    primary_color: Tuple[int, int, int],
    secondary_color: Tuple[int, int, int],
    initials: str,
    font_initials: ImageFont.ImageFont,
    phase: float = 0.0,
) -> None:
    """Apple Siri-inspired organic breathing orb with specular glass arc."""
    if speaking:
        # Breathing resonant outer field
        for ring in [3, 2, 1]:
            r_boost = int(ring * (7 + rms * 16) + math.sin(phase * 3.5 + ring) * 2.5)
            alpha = max(10, int((65 - ring * 16) * (0.6 + rms * 0.4)))
            draw.ellipse(
                [cx - (radius + r_boost), cy - (radius + r_boost), cx + (radius + r_boost), cy + (radius + r_boost)],
                fill=(*primary_color, alpha // 4),
                outline=(*primary_color, alpha),
                width=1,
            )

    # Glass core sphere
    core_r = radius + int(rms * 5 if speaking else 0)
    core_fill = (primary_color[0] // 5, primary_color[1] // 5, primary_color[2] // 5, 235) if speaking else (16, 22, 34, 215)
    border_col = (*primary_color, 240) if speaking else (255, 255, 255, 45)
    draw.ellipse([cx - core_r, cy - core_r, cx + core_r, cy + core_r], fill=core_fill, outline=border_col, width=2)

    # Specular glass reflection arc (top-left light sheen)
    arc_box = [cx - int(core_r * 0.72), cy - int(core_r * 0.72), cx + int(core_r * 0.72), cy + int(core_r * 0.72)]
    sheen_alpha = 110 if speaking else 45
    draw.arc(arc_box, start=200, end=320, fill=(255, 255, 255, sheen_alpha), width=2)

    # Initials
    bbox = draw.textbbox((0, 0), initials, font=font_initials)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    txt_col = (*secondary_color, 255) if speaking else (156, 163, 175, 210)
    draw.text((cx - tw // 2, cy - th // 2 - 2), initials, fill=txt_col, font=font_initials)


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
    max_height: int = 76,
) -> None:
    """Apple Music fluid rounded-pill waveform with Gaussian curve smoothing."""
    # Apply 3-point Gaussian smoothing so the bars look organic like Apple Music
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

        # Draw rounded vertical pill
        draw.rounded_rectangle(
            [bx, y_center - h, bx + bar_width, y_center + h],
            radius=bar_width // 2,
            fill=(*color_top, alpha),
        )


def render_apple_glass_preview(output_path: Path) -> Path:
    width, height = 1280, 720
    bg = create_apple_aurora_background(width, height, phase=1.2)
    logo = load_ranuk_apple_logo(size=44)

    f_large_title = load_apple_font("keynote", size=32)
    f_sub = load_apple_font("display", size=16)
    f_capsule = load_apple_font("rounded", size=13)
    f_speaker = load_apple_font("display", size=22)
    f_role = load_apple_font("display", size=13)
    f_quote = load_apple_font("display", size=20)
    f_status = load_apple_font("mono", size=11)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Apple Dynamic Island Capsule (Top Center)
    island_w, island_h = 580, 52
    ix0 = (width - island_w) // 2
    iy0 = 24
    draw.rounded_rectangle([ix0, iy0, ix0 + island_w, iy0 + island_h], radius=26, fill=(10, 14, 22, 220), outline=(255, 255, 255, 34), width=1)
    # Specular top highlight
    draw.rounded_rectangle([ix0 + 14, iy0 + 1, ix0 + island_w - 14, iy0 + 2], radius=20, fill=(255, 255, 255, 60))

    if logo:
        overlay.paste(logo, (ix0 + 12, iy0 + 5), logo)

    draw.text((ix0 + 64, iy0 + 17), "RANUK STUDIO  •  AI DEBATE ARENA", fill=(255, 255, 255, 245), font=f_capsule)

    # Dynamic Island Live Badge
    draw.rounded_rectangle([ix0 + island_w - 204, iy0 + 10, ix0 + island_w - 12, iy0 + island_h - 10], radius=16, fill=(251, 191, 36, 32), outline=(251, 191, 36, 175), width=1)
    draw.text((ix0 + island_w - 192, iy0 + 18), "⚡ FULL-DUPLEX OVERLAP", fill=(254, 243, 199, 255), font=f_status)

    # 2. Keynote Title & Subtitle
    draw.text((54, 94), "¿LA IA REEMPLAZARÁ A LOS INGENIEROS EN 2026?", fill=(255, 255, 255, 255), font=f_large_title)
    draw.text((54, 134), "Agentes Autónomos de Código vs. Arquitectura Humana en Producción  •  Passo 01", fill=(156, 163, 175, 235), font=f_sub)

    # 3. Two Apple Frosted Glass Speaker Cards
    card_y0, card_y1 = 175, 510
    card_w = 566

    # Pod A (Left - Mateo Vega)
    card_a = (54, card_y0, 54 + card_w, card_y1)
    draw_apple_glass_card(draw, card_a, radius=28, is_active=True, active_color=(0, 240, 255))
    draw_siri_fluid_orb(draw, 126, 254, 34, rms=0.75, speaking=True, primary_color=(0, 240, 255), secondary_color=(165, 243, 252), initials="MV", font_initials=f_speaker, phase=1.0)
    draw.text((186, 224), "Mateo Vega", fill=(255, 255, 255, 255), font=f_speaker)
    draw.text((186, 254), "CTO & Arquitecto de Sistemas Críticos", fill=(156, 163, 175, 220), font=f_role)
    draw.rounded_rectangle([186, 278, 350, 302], radius=12, fill=(0, 240, 255, 24), outline=(0, 240, 255, 120), width=1)
    draw.text((198, 283), "● CANAL IZQUIERDO (FL)", fill=(165, 243, 252, 255), font=f_status)

    # Pod A Liquid Waveform (Apple Music style)
    sim_bands_a = np.array([0.15, 0.4, 0.75, 0.9, 0.85, 0.65, 0.45, 0.35, 0.25, 0.3, 0.5, 0.7, 0.82, 0.65, 0.45, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05, 0.05, 0.05, 0.05], dtype=np.float32)
    draw_apple_music_waveform(draw, 84, 420, 24, bar_width=12, bar_gap=8, bands=sim_bands_a, speaking=True, color_top=(0, 240, 255), color_bot=(59, 130, 246), max_height=65)

    # Pod B (Right - Sofía Kovács)
    card_b = (width - 54 - card_w, card_y0, width - 54, card_y1)
    draw_apple_glass_card(draw, card_b, radius=28, is_active=True, active_color=(16, 235, 155))
    draw_siri_fluid_orb(draw, width - 54 - card_w + 72, 254, 34, rms=0.68, speaking=True, primary_color=(16, 235, 155), secondary_color=(167, 243, 208), initials="SK", font_initials=f_speaker, phase=2.0)
    draw.text((width - 54 - card_w + 132, 224), "Sofía Kovács", fill=(255, 255, 255, 255), font=f_speaker)
    draw.text((width - 54 - card_w + 132, 254), "Lead AI Agent Engineer • Ranuk Lab", fill=(156, 163, 175, 220), font=f_role)
    draw.rounded_rectangle([width - 54 - card_w + 132, 278, width - 54 - card_w + 304, 302], radius=12, fill=(16, 235, 155, 24), outline=(16, 235, 155, 120), width=1)
    draw.text((width - 54 - card_w + 144, 283), "● CANAL DERECHO (FR)", fill=(167, 243, 208, 255), font=f_status)

    # Pod B Liquid Waveform
    sim_bands_b = np.array([0.05, 0.1, 0.25, 0.55, 0.75, 0.88, 0.72, 0.58, 0.42, 0.35, 0.48, 0.65, 0.78, 0.62, 0.45, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05, 0.05, 0.05, 0.05], dtype=np.float32)
    draw_apple_music_waveform(draw, width - 54 - card_w + 30, 420, 24, bar_width=12, bar_gap=8, bands=sim_bands_b, speaking=True, color_top=(16, 235, 155), color_bot=(5, 150, 105), max_height=65)

    # 4. Apple Keynote Subtitle Bar (Bottom Stage)
    sub_rect = (54, 536, width - 54, 686)
    draw_apple_glass_card(draw, sub_rect, radius=24, fill_alpha=175, is_active=True, active_color=(0, 240, 255))

    # Speaker Pill
    draw.rounded_rectangle([80, 554, 250, 584], radius=15, fill=(0, 240, 255, 28), outline=(0, 240, 255, 160), width=1)
    draw.text((96, 560), "SOFÍA KOVÁCS", fill=(255, 255, 255, 255), font=f_capsule)
    draw.text((264, 560), "•  INTERRUPCIÓN FULL-DUPLEX (180ms)", fill=(0, 240, 255, 240), font=f_capsule)
    draw.text((width - 320, 560), "t = 08.24s  •  ranuk.dev/debates", fill=(156, 163, 175, 200), font=f_status)

    # Quote text
    draw.text((80, 602), "“¡Espera, Mateo! Ese era el debate de hace dos años. Hoy un enjambre de agentes", fill=(255, 255, 255, 255), font=f_quote)
    draw.text((80, 632), "detecta el fallo, valida el árbol sintáctico y despliega el parche en segundos.”", fill=(243, 244, 246, 245), font=f_quote)

    # Progress Capsule Bar
    draw.rounded_rectangle([80, 672, width - 80, 676], radius=2, fill=(255, 255, 255, 30))
    draw.rounded_rectangle([80, 672, 80 + 480, 676], radius=2, fill=(0, 240, 255, 240))

    final_img = Image.alpha_composite(bg, overlay)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_img.save(str(output_path), "PNG")
    return output_path


if __name__ == "__main__":
    out = Path("/Users/emilioranucoli/Apps/ranuk-ai-debate-studio/assets/preview_apple_glass.png")
    render_apple_glass_preview(out)
    print("Rendered Apple Glass preview to:", out)
