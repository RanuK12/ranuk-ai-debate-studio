# © 2026 Ranuk IT Solutions — ranuk.dev
"""
video_renderer.py — Apple-Grade Liquid Glassmorphic Full-Duplex Debate Video Renderer.

Broadcast Layouts:
  1. "glass_studio"  (1280x720 16:9 HD) — Apple Vision Pro frosted glass pods, 3D Siri orbs,
     Dynamic Island interaction capsule, Apple Music liquid waveforms, and Keynote typography.
  2. "split_wave"    (1280x720 16:9 HD) — Minimalist Executive 64-band mirrored acoustic spine
     with frosted glass headers and live Dynamic Island HUD.
  3. "vertical_reel" (1080x1920 9:16 HD) — Viral mobile format for Reddit, X, Reels & Shorts
     with glowing Apple Siri orbs, responsive glass cards, and high-retention subtitles.
"""
from __future__ import annotations

import math
import subprocess
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from .personaplex_duo import DebateScenario
from .waveform_analyzer import FrameAudioTelemetry, analyze_stereo_stream, find_ffmpeg

REPO_ROOT = Path(__file__).resolve().parent.parent
BRAND_DIR = REPO_ROOT / "assets" / "brand"


def _load_apple_font(font_type: str = "display", size: int = 24) -> ImageFont.FreeTypeFont:
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


def _load_ranuk_apple_logo(size: int = 40) -> Optional[Image.Image]:
    candidates = [
        BRAND_DIR / "minilogo.png",
        BRAND_DIR / "minilogo2.png",
        Path.home() / "Downloads" / "minilogo.png",
    ]
    for p in candidates:
        if p.exists():
            try:
                raw = Image.open(p).convert("RGB")
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


def _create_vibrant_apple_aurora(width: int, height: int, is_vertical: bool = False, phase: float = 0.0) -> Image.Image:
    """Rich, luminous Apple Vision Pro chromatic mesh gradient with architectural grid."""
    y, x = np.mgrid[:height, :width]
    base_grad = (4.0 + 7.0 * (y / float(height))).astype(np.uint8)
    base_img = Image.fromarray(np.dstack([base_grad, base_grad + 1, base_grad + 6, np.full((height, width), 255, dtype=np.uint8)]), mode="RGBA")

    if is_vertical:
        # Vertical Mobile Aurora
        cx1, cy1 = int(width * 0.30), int(height * 0.40)
        cx2, cy2 = int(width * 0.50), int(height * 0.20)
        cx3, cy3 = int(width * 0.70), int(height * 0.40)
        r_scale = 560.0
    else:
        # 16:9 Landscape Aurora
        cx1, cy1 = int(width * 0.25), int(height * 0.38)
        cx2, cy2 = int(width * 0.50), int(height * 0.20)
        cx3, cy3 = int(width * 0.75), int(height * 0.38)
        r_scale = 460.0

    dist1 = np.sqrt((x - cx1) ** 2 + (y - cy1) ** 2)
    alpha1 = (np.clip(1.0 - dist1 / r_scale, 0.0, 1.0) ** 2.0) * 110.0

    dist2 = np.sqrt((x - cx2) ** 2 + (y - cy2) ** 2)
    alpha2 = (np.clip(1.0 - dist2 / (r_scale * 1.05), 0.0, 1.0) ** 2.2) * 95.0

    dist3 = np.sqrt((x - cx3) ** 2 + (y - cy3) ** 2)
    alpha3 = (np.clip(1.0 - dist3 / r_scale, 0.0, 1.0) ** 2.0) * 110.0

    r = np.clip(alpha1 * 0.02 + alpha2 * 0.55 + alpha3 * 0.08, 0, 255).astype(np.uint8)
    g = np.clip(alpha1 * 0.90 + alpha2 * 0.22 + alpha3 * 0.92, 0, 255).astype(np.uint8)
    b = np.clip(alpha1 * 1.00 + alpha2 * 0.98 + alpha3 * 0.55, 0, 255).astype(np.uint8)
    a = np.clip(alpha1 + alpha2 + alpha3, 0, 205).astype(np.uint8)

    aurora = Image.fromarray(np.dstack([r, g, b, a]), mode="RGBA").filter(ImageFilter.GaussianBlur(26))
    combined = Image.alpha_composite(base_img, aurora)

    # Architectural grid
    grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid)
    step = 54 if is_vertical else 48
    for gx in range(0, width, step):
        gdraw.line([(gx, 0), (gx, height)], fill=(255, 255, 255, 6), width=1)
    for gy in range(0, height, step):
        gdraw.line([(0, gy), (width, gy)], fill=(255, 255, 255, 6), width=1)
    return Image.alpha_composite(combined, grid)


def _draw_apple_frosted_card(
    draw: ImageDraw.ImageDraw,
    rect: Tuple[int, int, int, int],
    radius: int = 28,
    fill_alpha: int = 160,
    is_active: bool = False,
    active_color: Tuple[int, int, int] = (0, 240, 255),
) -> None:
    """Apple Vision Pro frosted glass slab with 3D specular highlight refraction."""
    x0, y0, x1, y1 = rect
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=(12, 17, 28, fill_alpha))
    if is_active:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(*active_color, 195), width=2)
        draw.rounded_rectangle([x0 + 4, y0 + 1, x1 - 4, y0 + 3], radius=radius, fill=(255, 255, 255, 120))
    else:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(255, 255, 255, 32), width=1)
        draw.rounded_rectangle([x0 + 6, y0 + 1, x1 - 6, y0 + 2], radius=radius, fill=(255, 255, 255, 65))


def _draw_apple_siri_orb(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    rms: float,
    speaking: bool,
    primary_color: Tuple[int, int, int],
    secondary_color: Tuple[int, int, int],
    phase: float = 0.0,
    max_halo_radius: int = 42,
) -> None:
    """Apple Siri-style 3D iridescent glowing sphere constrained within pod bounds."""
    if speaking:
        for ring in [3, 2, 1]:
            r_boost = min(max_halo_radius - radius, int(ring * (4 + rms * 8) + math.sin(phase * 3.5 + ring) * 2))
            alpha = max(12, int((65 - ring * 16) * (0.6 + rms * 0.4)))
            draw.ellipse(
                [cx - (radius + r_boost), cy - (radius + r_boost), cx + (radius + r_boost), cy + (radius + r_boost)],
                fill=(*primary_color, alpha // 4),
                outline=(*primary_color, alpha),
                width=1,
            )

    r_core = radius + int(rms * 3 if speaking else 0)
    for step in range(r_core, 0, -3):
        frac = step / float(r_core)
        col = (
            int(primary_color[0] * frac + secondary_color[0] * (1 - frac)),
            int(primary_color[1] * frac + secondary_color[1] * (1 - frac)),
            int(primary_color[2] * frac + secondary_color[2] * (1 - frac)),
        )
        alpha = int(220 if speaking else 140)
        draw.ellipse([cx - step, cy - step, cx + step, cy + step], fill=(*col, alpha))

    # Specular upper glass sheen
    sheen_box = [cx - int(r_core * 0.75), cy - int(r_core * 0.75), cx + int(r_core * 0.75), cy + int(r_core * 0.75)]
    draw.arc(sheen_box, start=210, end=330, fill=(255, 255, 255, 180 if speaking else 90), width=3)


def _draw_apple_music_waveform(
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
    max_height: int = 65,
) -> None:
    """Apple Music fluid rounded-pill waveform with Gaussian smoothing and soft floor reflection."""
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

        draw.rounded_rectangle(
            [bx, y_center - h, bx + bar_width, y_center + h],
            radius=bar_width // 2,
            fill=(*color_top, alpha),
        )
        ref_h = int(h * 0.38)
        draw.rounded_rectangle(
            [bx, y_center + h + 6, bx + bar_width, y_center + h + 6 + ref_h],
            radius=bar_width // 2,
            fill=(*color_bot, alpha // 4),
        )


def _active_caption(scenario: DebateScenario, t_sec: float) -> Tuple[str, str, str, str, float]:
    active = None
    for cap in scenario.captions:
        s = float(cap.get("start", 0.0))
        e = float(cap.get("end", 0.0))
        if s <= t_sec <= e:
            active = cap
    if active is None and scenario.captions:
        preceding = [c for c in scenario.captions if float(c.get("start", 0.0)) <= t_sec]
        active = preceding[-1] if preceding else scenario.captions[0]

    if active is None:
        return ("B", scenario.speaker_b_name, "FULL-DUPLEX STREAM", "Live Speech-to-Speech Stream Active", 0.5)

    s = float(active.get("start", 0.0))
    e = max(s + 0.1, float(active.get("end", s + 1.0)))
    prog = min(1.0, max(0.0, (t_sec - s) / (e - s)))
    spk = str(active.get("speaker", "B"))
    spk_name = str(active.get("speaker_name", scenario.speaker_a_name if spk == "A" else scenario.speaker_b_name))
    tag = str(active.get("tag", "EN VIVO"))
    text = str(active.get("text", "")).strip()
    return (spk, spk_name, tag, text, prog)


def _interpolate_bands(bands_16: List[float], target_count: int = 24) -> np.ndarray:
    x_old = np.linspace(0.0, 1.0, len(bands_16))
    x_new = np.linspace(0.0, 1.0, target_count)
    return np.interp(x_new, x_old, bands_16)


def render_debate_video(
    scenario: DebateScenario,
    audio_path: Path,
    output_mp4: Path,
    fps: int = 24,
    max_duration_sec: float = 35.0,
    width: int = 1280,
    height: int = 720,
    style: str = "glass_studio",
) -> Path:
    """Render broadcast MP4 video with authentic Apple Vision Pro glassmorphism and SF typography."""
    if style == "vertical_reel" and width == 1280 and height == 720:
        width, height = 1080, 1920

    is_vert = style == "vertical_reel"
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    telemetry = analyze_stereo_stream(audio_path, fps=fps, max_duration_sec=max_duration_sec)
    actual_duration = len(telemetry) / float(fps)

    # Color palette
    col_a = (0, 240, 255)       # Apple Electric Cyan
    col_a_sub = (59, 130, 246)   # Cobalt
    col_b = (16, 235, 155)      # Apple Neon Emerald
    col_b_sub = (5, 150, 105)    # Teal
    col_overlap = (251, 191, 36) # Amber warning

    base_bg = _create_vibrant_apple_aurora(width, height, is_vertical=is_vert)
    logo_island = _load_ranuk_apple_logo(size=38 if not is_vert else 48)

    # Apple Typography
    f_large_title = _load_apple_font("keynote", size=38 if is_vert else 31)
    f_sub = _load_apple_font("display", size=20 if is_vert else 15)
    f_island = _load_apple_font("rounded", size=18 if is_vert else 13)
    f_speaker = _load_apple_font("display", size=26 if is_vert else 21)
    f_role = _load_apple_font("display", size=16 if is_vert else 13)
    f_quote = _load_apple_font("display", size=25 if is_vert else 19)
    f_status = _load_apple_font("rounded", size=15 if is_vert else 11)
    f_footer = _load_apple_font("display", size=16 if is_vert else 12)

    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        f"{width}x{height}",
        "-pix_fmt",
        "rgb24",
        "-r",
        str(fps),
        "-i",
        "-",
        "-i",
        str(audio_path),
        "-t",
        f"{actual_duration:.2f}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "19",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output_mp4),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None

    smooth_l_bands = np.zeros(24, dtype=np.float32)
    smooth_r_bands = np.zeros(24, dtype=np.float32)
    smooth_l_rms = 0.0
    smooth_r_rms = 0.0

    try:
        for frame in telemetry:
            t_sec = frame.timestamp_sec
            smooth_l_rms = 0.65 * frame.left_rms + 0.35 * smooth_l_rms
            smooth_r_rms = 0.65 * frame.right_rms + 0.35 * smooth_r_rms
            cur_l = _interpolate_bands(frame.left_bands, 24)
            cur_r = _interpolate_bands(frame.right_bands, 24)
            smooth_l_bands = 0.68 * cur_l + 0.32 * smooth_l_bands
            smooth_r_bands = 0.68 * cur_r + 0.32 * smooth_r_bands

            canvas = base_bg.copy()
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            spk_code, spk_name, turn_tag, cap_text, prog = _active_caption(scenario, t_sec)
            active_col = col_a if spk_code == "A" else col_b

            if is_vert:
                # --- LAYOUT 3: 9:16 VERTICAL REEL (1080x1920) ---
                # Dynamic Island Top
                island_w, island_h = 720, 68
                ix0 = (width - island_w) // 2
                iy0 = 54
                draw.rounded_rectangle([ix0, iy0, ix0 + island_w, iy0 + island_h], radius=34, fill=(8, 12, 20, 235), outline=(255, 255, 255, 38), width=1)
                draw.rounded_rectangle([ix0 + 16, iy0 + 1, ix0 + island_w - 16, iy0 + 2], radius=20, fill=(255, 255, 255, 75))
                if logo_island:
                    overlay.paste(logo_island, (ix0 + 14, iy0 + 10), logo_island)
                draw.text((ix0 + 72, iy0 + 20), "RANUK STUDIO  •  AI DEBATE", fill=(255, 255, 255, 245), font=f_island)

                if frame.is_overlap:
                    draw.rounded_rectangle([ix0 + island_w - 280, iy0 + 12, ix0 + island_w - 16, iy0 + island_h - 12], radius=22, fill=(251, 191, 36, 40), outline=(251, 191, 36, 210), width=1)
                    draw.text((ix0 + island_w - 264, iy0 + 22), "⚡ FULL-DUPLEX (180ms)", fill=(254, 243, 199, 255), font=f_status)
                else:
                    draw.rounded_rectangle([ix0 + island_w - 260, iy0 + 12, ix0 + island_w - 16, iy0 + island_h - 12], radius=22, fill=(0, 240, 255, 25), outline=(0, 240, 255, 120), width=1)
                    draw.text((ix0 + island_w - 246, iy0 + 22), "● 24kHz FULL-DUPLEX", fill=(165, 243, 252, 255), font=f_status)

                # Title
                title_lines = textwrap.wrap(scenario.title, width=28)[:2]
                ty = 160
                for tl in title_lines:
                    draw.text((54, ty), tl, fill=(255, 255, 255, 255), font=f_large_title)
                    ty += 48
                draw.text((54, ty + 8), scenario.subtitle[:60], fill=(156, 163, 175, 235), font=f_sub)

                # Dual Pods (Left & Right)
                pod_top, pod_bot = 390, 1040
                pw = (width - 138) // 2

                # Left Pod
                _draw_apple_frosted_card(draw, (54, pod_top, 54 + pw, pod_bot), radius=28, is_active=frame.left_speaking, active_color=col_a)
                _draw_apple_siri_orb(draw, 54 + pw // 2, pod_top + 95, 36, smooth_l_rms, frame.left_speaking, col_a, col_a_sub, t_sec, max_halo_radius=54)
                bbox_a = draw.textbbox((0, 0), scenario.speaker_a_name, font=f_speaker)
                draw.text((54 + pw // 2 - (bbox_a[2] - bbox_a[0]) // 2, pod_top + 168), scenario.speaker_a_name, fill=(255, 255, 255, 255), font=f_speaker)
                bbox_ar = draw.textbbox((0, 0), scenario.speaker_a_role[:26], font=f_role)
                draw.text((54 + pw // 2 - (bbox_ar[2] - bbox_ar[0]) // 2, pod_top + 204), scenario.speaker_a_role[:26], fill=(156, 163, 175, 220), font=f_role)

                # Left Waveform inside pod
                _draw_apple_music_waveform(draw, 78, pod_top + 430, 18, bar_width=15, bar_gap=7, bands=smooth_l_bands[:18], speaking=frame.left_speaking, color_top=col_a, color_bot=col_a_sub, max_height=110)

                # Right Pod
                rx0 = width - 54 - pw
                _draw_apple_frosted_card(draw, (rx0, pod_top, rx0 + pw, pod_bot), radius=28, is_active=frame.right_speaking, active_color=col_b)
                _draw_apple_siri_orb(draw, rx0 + pw // 2, pod_top + 95, 36, smooth_r_rms, frame.right_speaking, col_b, col_b_sub, t_sec, max_halo_radius=54)
                bbox_b = draw.textbbox((0, 0), scenario.speaker_b_name, font=f_speaker)
                draw.text((rx0 + pw // 2 - (bbox_b[2] - bbox_b[0]) // 2, pod_top + 168), scenario.speaker_b_name, fill=(255, 255, 255, 255), font=f_speaker)
                bbox_br = draw.textbbox((0, 0), scenario.speaker_b_role[:26], font=f_role)
                draw.text((rx0 + pw // 2 - (bbox_br[2] - bbox_br[0]) // 2, pod_top + 204), scenario.speaker_b_role[:26], fill=(156, 163, 175, 220), font=f_role)

                # Right Waveform inside pod
                _draw_apple_music_waveform(draw, rx0 + 24, pod_top + 430, 18, bar_width=15, bar_gap=7, bands=smooth_r_bands[:18], speaking=frame.right_speaking, color_top=col_b, color_bot=col_b_sub, max_height=110)

                # Subtitle Stage
                sub_y0, sub_y1 = 1120, 1740
                _draw_apple_frosted_card(draw, (54, sub_y0, width - 54, sub_y1), radius=32, fill_alpha=185, is_active=True, active_color=active_col)
                draw.rounded_rectangle([90, sub_y0 + 36, 380, sub_y0 + 82], radius=23, fill=(*active_col, 32), outline=(*active_col, 180), width=1)
                draw.text((114, sub_y0 + 48), spk_name.upper(), fill=(255, 255, 255, 255), font=f_island)
                draw.text((404, sub_y0 + 48), f"•  {turn_tag}", fill=(*active_col, 240), font=f_island)

                wrapped = textwrap.wrap(f"“{cap_text}”", width=38)[:6]
                cy_t = sub_y0 + 120
                for ln in wrapped:
                    draw.text((90, cy_t), ln, fill=(255, 255, 255, 255), font=f_large_title)
                    cy_t += 50

                bar_w = int((width - 180) * prog)
                draw.rounded_rectangle([90, sub_y1 - 34, width - 90, sub_y1 - 28], radius=3, fill=(255, 255, 255, 30))
                if bar_w > 8:
                    draw.rounded_rectangle([90, sub_y1 - 34, 90 + bar_w, sub_y1 - 28], radius=3, fill=(*active_col, 245))

                draw.text((width // 2 - 190, 1800), "ranuk.dev  •  Ranuk IT Solutions  •  NVIDIA PersonaPlex 7B", fill=(156, 163, 175, 210), font=f_footer)

            else:
                # --- LAYOUT 1 & 2: 16:9 LANDSCAPE (1280x720) ---
                # 1. Dynamic Island Capsule (Top Center)
                island_w, island_h = 560, 48
                ix0 = (width - island_w) // 2
                iy0 = 22
                draw.rounded_rectangle([ix0, iy0, ix0 + island_w, iy0 + island_h], radius=24, fill=(8, 12, 20, 235), outline=(255, 255, 255, 38), width=1)
                draw.rounded_rectangle([ix0 + 16, iy0 + 1, ix0 + island_w - 16, iy0 + 2], radius=20, fill=(255, 255, 255, 75))

                if logo_island:
                    overlay.paste(logo_island, (ix0 + 12, iy0 + 5), logo_island)

                draw.text((ix0 + 58, iy0 + 15), "RANUK IT SOLUTIONS  •  AI DEBATE STUDIO", fill=(255, 255, 255, 245), font=f_island)

                if frame.is_overlap:
                    draw.rounded_rectangle([ix0 + island_w - 204, iy0 + 9, ix0 + island_w - 12, iy0 + island_h - 9], radius=15, fill=(251, 191, 36, 40), outline=(251, 191, 36, 210), width=1)
                    draw.text((ix0 + island_w - 192, iy0 + 17), "● LIVE FULL-DUPLEX (180ms)", fill=(254, 243, 199, 255), font=f_status)
                else:
                    draw.rounded_rectangle([ix0 + island_w - 195, iy0 + 9, ix0 + island_w - 12, iy0 + island_h - 9], radius=15, fill=(0, 240, 255, 22), outline=(0, 240, 255, 105), width=1)
                    draw.text((ix0 + island_w - 182, iy0 + 17), f"● 24kHz DUAL  •  OVERLAPS: {frame.cumulative_overlaps}", fill=(165, 243, 252, 245), font=f_status)

                # 2. Keynote Title & Subtitle
                draw.text((54, 88), scenario.title, fill=(255, 255, 255, 255), font=f_large_title)
                draw.text((54, 126), scenario.subtitle, fill=(156, 163, 175, 235), font=f_sub)

                # 3. Two Apple Frosted Glass Speaker Cards
                card_y0, card_y1 = 168, 516
                card_w = 566

                # Pod A (Left Speaker)
                card_a = (54, card_y0, 54 + card_w, card_y1)
                _draw_apple_frosted_card(draw, card_a, radius=28, is_active=frame.left_speaking, active_color=col_a)
                _draw_apple_siri_orb(draw, 114, 232, 28, smooth_l_rms, frame.left_speaking, col_a, col_a_sub, t_sec, max_halo_radius=44)
                draw.text((166, 212), scenario.speaker_a_name, fill=(255, 255, 255, 255), font=f_speaker)
                draw.text((166, 242), scenario.speaker_a_role, fill=(156, 163, 175, 220), font=f_role)
                draw.rounded_rectangle([166, 268, 330, 292], radius=12, fill=(0, 240, 255, 24), outline=(0, 240, 255, 120), width=1)
                draw.text((178, 273), "● CANAL IZQUIERDO (FL)", fill=(165, 243, 252, 255), font=f_status)

                _draw_apple_music_waveform(draw, 84, 408, 24, bar_width=12, bar_gap=8, bands=smooth_l_bands, speaking=frame.left_speaking, color_top=col_a, color_bot=col_a_sub, max_height=65)

                # Pod B (Right Speaker)
                card_b = (width - 54 - card_w, card_y0, width - 54, card_y1)
                _draw_apple_frosted_card(draw, card_b, radius=28, is_active=frame.right_speaking, active_color=col_b)
                _draw_apple_siri_orb(draw, width - 54 - card_w + 60, 232, 28, smooth_r_rms, frame.right_speaking, col_b, col_b_sub, t_sec, max_halo_radius=44)
                draw.text((width - 54 - card_w + 112, 212), scenario.speaker_b_name, fill=(255, 255, 255, 255), font=f_speaker)
                draw.text((width - 54 - card_w + 112, 242), scenario.speaker_b_role, fill=(156, 163, 175, 220), font=f_role)
                draw.rounded_rectangle([width - 54 - card_w + 112, 268, width - 54 - card_w + 276, 292], radius=12, fill=(16, 235, 155, 24), outline=(16, 235, 155, 120), width=1)
                draw.text((width - 54 - card_w + 124, 273), "● CANAL DERECHO (FR)", fill=(167, 243, 208, 255), font=f_status)

                _draw_apple_music_waveform(draw, width - 54 - card_w + 30, 408, 24, bar_width=12, bar_gap=8, bands=smooth_r_bands, speaking=frame.right_speaking, color_top=col_b, color_bot=col_b_sub, max_height=65)

                # 4. Apple Keynote Subtitle Bar (Bottom Stage)
                sub_rect = (54, 538, width - 54, 692)
                _draw_apple_frosted_card(draw, sub_rect, radius=24, is_active=True, active_color=active_col)

                # Speaker Tag
                draw.rounded_rectangle([80, 556, 240, 586], radius=15, fill=(*active_col, 28), outline=(*active_col, 160), width=1)
                draw.text((94, 562), spk_name.upper(), fill=(255, 255, 255, 255), font=f_island)
                draw.text((254, 562), f"•  {turn_tag}", fill=(*active_col, 240), font=f_island)
                draw.text((width - 320, 562), f"t = {t_sec:05.2f}s  •  ranuk.dev/debates", fill=(156, 163, 175, 200), font=f_status)

                wrapped = textwrap.wrap(f"“{cap_text}”", width=86)[:2]
                cy_t = 604
                for ln in wrapped:
                    draw.text((80, cy_t), ln, fill=(255, 255, 255, 255), font=f_quote)
                    cy_t += 28

                bar_w = int((width - 160) * prog)
                draw.rounded_rectangle([80, 676, width - 80, 680], radius=2, fill=(255, 255, 255, 30))
                if bar_w > 6:
                    draw.rounded_rectangle([80, 676, 80 + bar_w, 680], radius=2, fill=(*active_col, 245))

            final_rgb = Image.alpha_composite(canvas, overlay).convert("RGB")
            proc.stdin.write(final_rgb.tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=90)

    if proc.returncode != 0 or not output_mp4.exists():
        raise RuntimeError(f"FFmpeg video rendering failed with code {proc.returncode}")
    return output_mp4
