# © 2026 Ranuk IT Solutions — ranuk.dev
"""
cover_generator.py — Universal High-Conversion Cover & Thumbnail Generator for AI Debates.

Designed specifically for 9:16 Vertical formats (YouTube Shorts & TikTok):
- Exact 1080x1920 canvas.
- Strict safe zones: central 3:4 crop (y=380 to y=1440) fully protected against UI buttons,
  avatar overlaps, and horizontal/square grid clippings.
- Ranuk IT Solutions Cyber-Glass branding (neon cyan, emerald, obsidian dark mode, glowing HUD).
- Dynamic text engine: auto-wraps debate title, speaker names, roles, and day counter.
- Outputs lossless PNG and optimized JPEG.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Brand palettes aligned with the 4 rotating video models
COVER_THEMES: Dict[str, Dict[str, Any]] = {
    "model_1_cyber_nexus": {
        "bg_dark": (4, 8, 18),
        "bg_card": (10, 18, 36),
        "border_a": (0, 240, 255),      # Electric Cyan
        "border_b": (16, 235, 155),     # Neon Emerald
        "accent": (251, 191, 36),       # Amber Gold
        "title_highlight": (0, 240, 255),
    },
    "model_2_quantum_matrix": {
        "bg_dark": (9, 4, 20),
        "bg_card": (16, 10, 32),
        "border_a": (192, 132, 252),    # Hyper Violet
        "border_b": (251, 191, 36),     # Solar Gold
        "accent": (0, 240, 255),        # Electric Cyan
        "title_highlight": (251, 191, 36),
    },
    "model_3_silicon_warroom": {
        "bg_dark": (10, 10, 15),
        "bg_card": (18, 16, 26),
        "border_a": (255, 42, 95),      # Laser Crimson
        "border_b": (56, 189, 248),     # Ice Cobalt
        "accent": (253, 224, 71),       # Tactical Yellow
        "title_highlight": (255, 42, 95),
    },
    "model_4_blackwell_tensor": {
        "bg_dark": (4, 11, 7),
        "bg_card": (8, 20, 16),
        "border_a": (74, 222, 128),     # Blackwell Green
        "border_b": (34, 211, 238),     # Plasma Cyan
        "accent": (190, 242, 100),      # Lime Volt
        "title_highlight": (74, 222, 128),
    },
}


def _get_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    font_paths = {
        "title": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "impact": "/System/Library/Fonts/Supplemental/Impact.ttf",
        "sf_bold": "/System/Library/Fonts/SFNS.ttf",
        "sf_mono": "/System/Library/Fonts/SFNSMono.ttf",
        "avenir": "/System/Library/Fonts/Avenir Next.ttc",
    }
    path = font_paths.get(name, "/System/Library/Fonts/SFNS.ttf")
    try:
        return ImageFont.truetype(path, size=size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text_to_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    words = text.split()
    lines = []
    cur_line = []
    for w in words:
        test = " ".join(cur_line + [w])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur_line.append(w)
        else:
            if cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                lines.append(w)
                cur_line = []
    if cur_line:
        lines.append(" ".join(cur_line))
    return lines


def generate_debate_cover(
    title: str,
    speaker_a_name: str,
    speaker_a_role: str,
    speaker_b_name: str,
    speaker_b_role: str,
    day_num: int = 1,
    output_path: Optional[Path] = None,
    theme_key: str = "model_1_cyber_nexus"
) -> Path:
    """Generate universal 1080x1920 cover image for TikTok and YouTube Shorts."""
    W, H = 1080, 1920
    theme = COVER_THEMES.get(theme_key, COVER_THEMES["model_1_cyber_nexus"])

    img = Image.new("RGB", (W, H), theme["bg_dark"])
    draw = ImageDraw.Draw(img)

    # 1. Background Grid & Tech Lines
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=(12, 22, 45), width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=(12, 22, 45), width=1)

    # Subtle diagonal circuit accents
    draw.line([(0, 400), (400, 0)], fill=(20, 35, 65), width=2)
    draw.line([(W - 400, H), (W, H - 400)], fill=(20, 35, 65), width=2)

    # Radial Neon Glows (under speaker cards & title)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([W // 2 - 400, 750 - 400, W // 2 + 400, 750 + 400], fill=(*theme["border_a"], 35))
    gdraw.ellipse([W // 2 - 300, 1150 - 300, W // 2 + 300, 1150 + 300], fill=(*theme["border_b"], 35))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img.paste(glow, (0, 0), glow)

    # Fonts
    font_brand = _get_font("sf_bold", 22)
    font_day = _get_font("title", 24)
    font_title = _get_font("title", 52)
    font_matchup = _get_font("sf_bold", 22)
    font_name = _get_font("title", 28)
    font_role = _get_font("sf_bold", 20)
    font_vs = _get_font("impact", 36)
    font_hook = _get_font("title", 24)
    font_footer = _get_font("sf_mono", 20)

    # 2. Top Header Bar (Brand Identity)
    # Ranuk IT Solutions Pill
    draw.rounded_rectangle([60, 100, 530, 162], radius=16, fill=theme["bg_card"], outline=theme["border_a"], width=2)
    draw.text((85, 120), "RANUK IT SOLUTIONS", fill=(255, 255, 255), font=font_brand)
    # Audio Specs Pill
    draw.rounded_rectangle([720, 100, 1020, 162], radius=16, fill=theme["bg_card"], outline=theme["border_b"], width=2)
    draw.text((748, 120), "● 24kHz FULL-DUPLEX", fill=theme["border_b"], font=font_brand)

    # 3. Episode Pill (Safe Zone Top, y=360)
    draw.rounded_rectangle([290, 360, 790, 422], radius=31, fill=(18, 28, 54), outline=theme["border_a"], width=2)
    day_str = f"🔥 DAY #{day_num:02d} • AI DEBATE ARENA"
    bbox = draw.textbbox((0, 0), day_str, font=font_day)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, 378), day_str, fill=theme["border_a"], font=font_day)

    # 4. Main Question Card (Strictly centered in Safe Zone, y=446 to y=850)
    card_top, card_bot = 446, 850
    draw.rounded_rectangle([60, card_top, 1020, card_bot], radius=28, fill=theme["bg_card"], outline=theme["border_a"], width=3)

    # Clean & Wrap Title
    raw_title = title.replace("#Shorts", "").replace("#shorts", "").strip()
    title_lines = _wrap_text_to_width(draw, raw_title.upper(), font_title, 880)
    if len(title_lines) > 4:
        title_lines = title_lines[:4]

    y_t = card_top + 40
    for idx, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        lw = bbox[2] - bbox[0]
        # Alternate highlight color on the second line or punchline
        col = theme["title_highlight"] if idx in [1, 2] and len(title_lines) > 2 else (255, 255, 255)
        draw.text(((W - lw) // 2, y_t), line, fill=col, font=font_title)
        y_t += 70

    # Role Matchup Capsule at bottom of card
    matchup_text = f"{speaker_a_role.upper()}  ⚡️  {speaker_b_role.upper()}"
    bbox_m = draw.textbbox((0, 0), matchup_text, font=font_matchup)
    mw = bbox_m[2] - bbox_m[0]
    capsule_x1 = max(80, (W - mw - 60) // 2)
    capsule_x2 = min(1000, (W + mw + 60) // 2)
    draw.rounded_rectangle([capsule_x1, card_bot - 65, capsule_x2, card_bot - 18], radius=16, fill=(18, 28, 52), outline=theme["accent"], width=1)
    draw.text(((W - mw) // 2, card_bot - 55), matchup_text, fill=(241, 245, 249), font=font_matchup)

    # 5. The Dual Speaker Arena (y=880 to y=1340)
    # Left Speaker Pod (Speaker A)
    draw.rounded_rectangle([60, 880, 480, 1340], radius=24, fill=theme["bg_card"], outline=theme["border_a"], width=2)
    # Concentric acoustic glow rings
    draw.ellipse([185, 905, 355, 1075], outline=(*theme["border_a"], 70), width=2)
    draw.ellipse([200, 920, 340, 1060], outline=(*theme["border_a"], 140), width=2)
    draw.ellipse([215, 935, 325, 1045], fill=theme["border_a"], outline=(255, 255, 255), width=3)

    bbox_na = draw.textbbox((0, 0), speaker_a_name, font=font_name)
    draw.text(((540 - (bbox_na[2] - bbox_na[0])) // 2, 1080), speaker_a_name, fill=(255, 255, 255), font=font_name)
    bbox_ra = draw.textbbox((0, 0), speaker_a_role[:26], font=font_role)
    draw.text(((540 - (bbox_ra[2] - bbox_ra[0])) // 2, 1125), speaker_a_role[:26], fill=(148, 163, 184), font=font_role)

    # Soundwave bars (Left)
    for i in range(14):
        bh = 12 + int(math.sin(i * 0.6) * 22) + 20
        draw.rectangle([110 + i * 18, 1260 - bh, 122 + i * 18, 1260], fill=theme["border_a"])

    # Right Speaker Pod (Speaker B)
    draw.rounded_rectangle([600, 880, 1020, 1340], radius=24, fill=theme["bg_card"], outline=theme["border_b"], width=2)
    # Concentric acoustic glow rings
    draw.ellipse([725, 905, 895, 1075], outline=(*theme["border_b"], 70), width=2)
    draw.ellipse([740, 920, 880, 1060], outline=(*theme["border_b"], 140), width=2)
    draw.ellipse([755, 935, 865, 1045], fill=theme["border_b"], outline=(255, 255, 255), width=3)

    bbox_nb = draw.textbbox((0, 0), speaker_b_name, font=font_name)
    draw.text(((W + 600 - (bbox_nb[2] - bbox_nb[0])) // 2, 1080), speaker_b_name, fill=(255, 255, 255), font=font_name)
    bbox_rb = draw.textbbox((0, 0), speaker_b_role[:26], font=font_role)
    draw.text(((W + 600 - (bbox_rb[2] - bbox_rb[0])) // 2, 1125), speaker_b_role[:26], fill=(148, 163, 184), font=font_role)

    # Soundwave bars (Right)
    for i in range(14):
        bh = 12 + int(math.cos(i * 0.6) * 22) + 20
        draw.rectangle([650 + i * 18, 1260 - bh, 662 + i * 18, 1260], fill=theme["border_b"])

    # Center Clash Badge ("VS")
    draw.ellipse([495, 1065, 585, 1155], fill=theme["accent"], outline=(255, 255, 255), width=4)
    draw.text((518, 1087), "VS", fill=(0, 0, 0), font=font_vs)

    # 6. Bottom Acoustic Action Hook (Safe Zone Bottom, y=1390)
    draw.rounded_rectangle([100, 1390, 980, 1475], radius=42, fill=(18, 28, 54), outline=theme["accent"], width=2)
    hook_str = "🎙️ REAL-TIME INTERRUPTION • WHO WON THE DEBATE?"
    bbox_h = draw.textbbox((0, 0), hook_str, font=font_hook)
    draw.text(((W - (bbox_h[2] - bbox_h[0])) // 2, 1420), hook_str, fill=(255, 255, 255), font=font_hook)

    # 7. Brand Footer
    footer_text = "ranuk.dev/debates • Ranuk IT Solutions"
    bbox_f = draw.textbbox((0, 0), footer_text, font=font_footer)
    draw.text(((W - (bbox_f[2] - bbox_f[0])) // 2, 1780), footer_text, fill=(100, 116, 139), font=font_footer)

    if output_path is None:
        output_path = Path(f"/tmp/debate_day_{day_num:02d}_cover.png")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), format="PNG", quality=95)

    # Also save JPEG twin (for YouTube Data API v3 custom thumbnail)
    jpg_path = output_path.with_suffix(".jpg")
    img.save(str(jpg_path), format="JPEG", quality=92)

    return output_path
