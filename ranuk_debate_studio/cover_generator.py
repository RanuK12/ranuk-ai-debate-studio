# © 2026 Ranuk IT Solutions — ranuk.dev
"""
cover_generator.py — Imposing, High-Conversion Cinematic 9:16 Cover & Thumbnail Engine.

Features:
- Imposing 3D AI Combatants (Cybernetic Neural Architect vs. Quantum AI Entity).
- Real Ranuk IT Solutions brand identity (high-res minilogo + < R /> HUD header).
- High-voltage volumetric clash, electric lightning, and metallic "VS" badge.
- Dynamic color themes matching the 4 rotating UI models.
- Word-level neon highlight with multi-directional drop shadows for maximum feed clickability.
- Strict 9:16 vertical safe-zone layout for YouTube Shorts shelf & TikTok grids.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
BRAND_DIR = REPO_ROOT / "assets" / "brand"
BASE_ARENA_PATH = BRAND_DIR / "base_arena_combatants.jpg"
MINILOGO_PATH = BRAND_DIR / "minilogo.png"

# Color themes strictly aligned with the 4 rotating video UI models
COVER_THEMES: Dict[str, Dict[str, Any]] = {
    "model_1_cyber_nexus": {
        "name": "CYBER-GLASS ARENA",
        "border_a": (0, 240, 255),       # Electric Cyan
        "border_b": (16, 235, 155),      # Neon Emerald
        "accent": (251, 191, 36),        # Amber Gold
        "title_highlight": (0, 240, 255),
        "tag_bg_a": (10, 20, 42, 230),
        "tag_bg_b": (10, 26, 32, 230),
    },
    "model_2_quantum_matrix": {
        "name": "QUANTUM MATRIX",
        "border_a": (192, 132, 252),     # Hyper Violet
        "border_b": (251, 191, 36),      # Solar Gold
        "accent": (0, 240, 255),         # Electric Cyan
        "title_highlight": (251, 191, 36),
        "tag_bg_a": (24, 14, 44, 230),
        "tag_bg_b": (34, 22, 12, 230),
    },
    "model_3_silicon_warroom": {
        "name": "SILICON WAR ROOM",
        "border_a": (255, 42, 95),       # Laser Crimson
        "border_b": (56, 189, 248),      # Ice Cobalt
        "accent": (253, 224, 71),        # Tactical Yellow
        "title_highlight": (255, 42, 95),
        "tag_bg_a": (36, 12, 22, 230),
        "tag_bg_b": (12, 24, 40, 230),
    },
    "model_4_blackwell_tensor": {
        "name": "BLACKWELL TENSOR",
        "border_a": (74, 222, 128),      # Blackwell Tensor Green
        "border_b": (34, 211, 238),      # Plasma Cyan
        "accent": (190, 242, 100),       # Lime Volt
        "title_highlight": (74, 222, 128),
        "tag_bg_a": (12, 30, 20, 230),
        "tag_bg_b": (10, 26, 36, 230),
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


def _wrap_text_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    clean = text.replace("#Shorts", "").replace("#shorts", "").strip()
    words = clean.split()
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
    theme_key: str = "model_1_cyber_nexus",
) -> Path:
    """Generate universal 1080x1920 cover image for TikTok and YouTube Shorts."""
    W, H = 1080, 1920
    theme = COVER_THEMES.get(theme_key, COVER_THEMES["model_1_cyber_nexus"])

    # 1. Base Arena Background
    if BASE_ARENA_PATH.exists():
        bg = Image.open(BASE_ARENA_PATH).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    else:
        bg = Image.new("RGB", (W, H), (4, 8, 18))

    # Contrast & punch boost for mobile feed visibility
    bg = ImageEnhance.Contrast(bg).enhance(1.15)
    bg = ImageEnhance.Color(bg).enhance(1.20)

    # 2. Gradient Overlays for High-Contrast Safe Zones
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(overlay)

    # Top darkening
    for y in range(0, 480):
        alpha = int(210 * (1.0 - (y / 480.0) ** 1.2))
        gdraw.line([(0, y), (W, y)], fill=(3, 7, 18, alpha))

    # Bottom darkening
    for y in range(H - 520, H):
        alpha = int(220 * (((y - (H - 520)) / 520.0) ** 1.2))
        gdraw.line([(0, y), (W, y)], fill=(3, 7, 18, alpha))

    # Center card shadow
    gdraw.rounded_rectangle([40, 430, W - 40, 860], radius=32, fill=(4, 8, 22, 190))

    # Fonts
    font_brand = _get_font("sf_bold", 24)
    font_badge = _get_font("sf_mono", 20)
    font_pill = _get_font("title", 26)
    font_title = _get_font("title", 54)
    font_name = _get_font("title", 28)
    font_role = _get_font("sf_bold", 22)
    font_vs = _get_font("impact", 44)
    font_hook = _get_font("title", 25)

    draw = ImageDraw.Draw(overlay)

    # 3. Top Header Bar with REAL Ranuk Logo
    draw.rounded_rectangle([60, 95, 560, 165], radius=20, fill=(10, 18, 36, 230), outline=(*theme["border_a"], 220), width=2)
    if MINILOGO_PATH.exists():
        logo = Image.open(MINILOGO_PATH).convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
        mask = Image.new("L", (64, 64), 0)
        m_draw = ImageDraw.Draw(mask)
        m_draw.ellipse([0, 0, 64, 64], fill=255)
        overlay.paste(logo, (75, 98), mask)
    draw.text((150, 115), "RANUK IT SOLUTIONS", fill=(255, 255, 255, 255), font=font_brand)

    # Audio Specs Badge
    draw.rounded_rectangle([720, 95, 1020, 165], radius=20, fill=(10, 18, 36, 230), outline=(*theme["border_b"], 220), width=2)
    draw.ellipse([742, 122, 758, 138], fill=(*theme["border_b"], 255))
    draw.text((770, 118), "24kHz FULL-DUPLEX", fill=(*theme["border_b"], 255), font=font_badge)

    # 4. Episode / Day Pill (Safe Zone Top)
    day_text = f"LIVE  //  DAY #{day_num:02d} • {theme['name']}"
    bbox_d = draw.textbbox((0, 0), day_text, font=font_pill)
    text_w = bbox_d[2] - bbox_d[0]
    day_pill_w = min(W - 80, max(480, text_w + 84))
    px1 = (W - day_pill_w) // 2
    draw.rounded_rectangle([px1, 348, px1 + day_pill_w, 412], radius=32, fill=(20, 32, 60, 240), outline=(*theme["border_a"], 240), width=2)
    draw.text(((W - text_w) // 2, 367), day_text, fill=(*theme["border_a"], 255), font=font_pill)

    # 5. Main Question Card (High Contrast 3D Neon Text)
    card_x1, card_y1, card_x2, card_y2 = 50, 436, W - 50, 856
    draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=28, fill=(8, 14, 30, 220), outline=(*theme["border_a"], 255), width=3)

    # High-Tech Corner Brackets
    b_len = 36
    draw.line([(card_x1 - 4, card_y1 + b_len), (card_x1 - 4, card_y1 - 4), (card_x1 + b_len, card_y1 - 4)], fill=theme["accent"], width=4)
    draw.line([(card_x2 + 4, card_y1 + b_len), (card_x2 + 4, card_y1 - 4), (card_x2 - b_len, card_y1 - 4)], fill=theme["accent"], width=4)
    draw.line([(card_x1 - 4, card_y2 - b_len), (card_x1 - 4, card_y2 + 4), (card_x1 + b_len, card_y2 + 4)], fill=theme["accent"], width=4)
    draw.line([(card_x2 + 4, card_y2 - b_len), (card_x2 + 4, card_y2 + 4), (card_x2 - b_len, card_y2 + 4)], fill=theme["accent"], width=4)

    # Dynamic Title Wrap & Color Accent
    raw_lines = _wrap_text_lines(draw, title.upper(), font_title, 900)
    if len(raw_lines) > 3:
        raw_lines = raw_lines[:3]

    cur_y = card_y1 + (40 if len(raw_lines) >= 3 else 60)
    for idx, line in enumerate(raw_lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        lw = bbox[2] - bbox[0]
        lx = (W - lw) // 2
        # Color: Alternate highlight color on the central punchline
        color = theme["title_highlight"] if idx == 1 or (len(raw_lines) == 1) else (255, 255, 255)
        # Deep 8-direction drop shadow for crystal-clear readability
        for ox, oy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4), (0, -4), (4, 0), (-4, 0)]:
            draw.text((lx + ox, cur_y + oy), line, fill=(0, 0, 0, 255), font=font_title)
        draw.text((lx, cur_y), line, fill=color, font=font_title)
        cur_y += 75

    # Matchup Capsule inside Card
    draw.rounded_rectangle([90, card_y2 - 68, W - 90, card_y2 - 18], radius=18, fill=(16, 26, 52, 235), outline=(*theme["accent"], 180), width=2)
    match_text = f"{speaker_a_role.upper()[:24]}   VS   {speaker_b_role.upper()[:24]}"
    bbox_m = draw.textbbox((0, 0), match_text, font=font_role)
    draw.text(((W - (bbox_m[2] - bbox_m[0])) // 2, card_y2 - 56), match_text, fill=(241, 245, 249), font=font_role)

    # 6. Speaker Holographic Plaques (Left: A, Right: B)
    # Speaker A Plaque
    draw.rounded_rectangle([60, 1160, 470, 1310], radius=20, fill=theme["tag_bg_a"], outline=(*theme["border_a"], 240), width=2)
    draw.text((85, 1180), speaker_a_name, fill=(255, 255, 255), font=font_name)
    draw.text((85, 1222), speaker_a_role[:24], fill=(148, 163, 184), font=font_role)
    draw.text((85, 1262), "CH-01 • LEFT 24kHz", fill=theme["border_a"], font=font_badge)

    # Speaker B Plaque
    draw.rounded_rectangle([W - 470, 1160, W - 60, 1310], radius=20, fill=theme["tag_bg_b"], outline=(*theme["border_b"], 240), width=2)
    draw.text((W - 445, 1180), speaker_b_name, fill=(255, 255, 255), font=font_name)
    draw.text((W - 445, 1222), speaker_b_role[:24], fill=(148, 163, 184), font=font_role)
    draw.text((W - 445, 1262), "CH-02 • RIGHT 24kHz", fill=theme["border_b"], font=font_badge)

    # 7. Center 'VS' Clash Badge (y=1235)
    vs_x, vs_y = W // 2, 1235
    draw.ellipse([vs_x - 55, vs_y - 55, vs_x + 55, vs_y + 55], fill=(*theme["accent"], 255), outline=(255, 255, 255, 255), width=4)
    draw.ellipse([vs_x - 45, vs_y - 45, vs_x + 45, vs_y + 45], outline=(0, 0, 0, 200), width=2)
    bbox_vs = draw.textbbox((0, 0), "VS", font=font_vs)
    draw.text((vs_x - (bbox_vs[2] - bbox_vs[0]) // 2, vs_y - (bbox_vs[3] - bbox_vs[1]) // 2 - 4), "VS", fill=(0, 0, 0, 255), font=font_vs)

    # 8. Bottom Safe-Zone Call to Action (y=1380 to y=1465)
    draw.rounded_rectangle([80, 1380, W - 80, 1465], radius=42, fill=(18, 28, 56, 240), outline=(*theme["accent"], 230), width=2)
    hook_text = "180ms INTERRUPT DEBATE  •  PICK YOUR SIDE BELOW"
    bbox_h = draw.textbbox((0, 0), hook_text, font=font_hook)
    draw.text(((W - (bbox_h[2] - bbox_h[0])) // 2, 1420), hook_text, fill=(255, 255, 255), font=font_hook)

    # 9. Brand Footer Bar (y=1780)
    draw.text(((W - 460) // 2, 1780), "ranuk.dev/debates • Ranuk IT Solutions", fill=(148, 163, 184, 220), font=font_role)

    # Final Composite
    final_img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")

    if output_path is None:
        output_path = Path(f"/tmp/debate_day_{day_num:02d}_cover.png")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_img.save(str(output_path), format="PNG", quality=95)
    final_img.save(str(output_path.with_suffix(".jpg")), format="JPEG", quality=92)

    return output_path
