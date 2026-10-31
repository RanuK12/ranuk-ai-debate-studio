# © 2026 Ranuk IT Solutions — ranuk.dev
"""
video_renderer.py — Next-Gen Glassmorphic & Multi-Layout Full-Duplex Debate Video Renderer.

Supports 3 broadcast styles:
  1. "glass_studio"  (1280x720 16:9 HD) — Sleek floating glass pods, 3D Ranuk neon logo,
     dynamic radial voice blooms, 32-band mirrored harmonic spectrums, and cinema subtitles.
  2. "split_wave"    (1280x720 16:9 HD) — Minimalist executive arena with a full-width
     64-band mirrored acoustic spine (Cyan top / Emerald bottom) and live dialogue dock.
  3. "vertical_reel" (1080x1920 9:16 HD) — Viral mobile format for Reddit, X, Shorts & Reels
     with dual harmonic orbs, reactive neon rings, and bold cinema subtitles.
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


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        if bold
        else [
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    )
    for c in candidates:
        if Path(c).exists():
            try:
                # For .ttc collections, index 1 is often Bold in Helvetica, but Arial Bold works directly
                if bold and c.endswith("Arial Bold.ttf"):
                    return ImageFont.truetype(c, size=size)
                return ImageFont.truetype(c, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def _load_brand_logo(target_size: int = 44) -> Optional[Image.Image]:
    """
    Load the 3D Neon Glass Ranuk 'R}' logo from assets/brand/minilogo.png or Downloads,
    converting its black background into smooth luminance alpha so the neon glass floats cleanly.
    """
    candidates = [
        BRAND_DIR / "minilogo.png",
        BRAND_DIR / "minilogo2.png",
        Path.home() / "Downloads" / "minilogo.png",
        Path.home() / "Downloads" / "Logos-IMG-News" / "minilogo.png",
    ]
    for path in candidates:
        if path.exists():
            try:
                raw = Image.open(path).convert("RGB")
                # Crop tight around the glowing R} emblem
                arr = np.array(raw, dtype=np.float32)
                lum = np.max(arr, axis=2)
                # Smooth alpha curve so black (0..18) is transparent and neon cyan glows
                alpha = np.clip((lum - 14.0) * 2.2, 0.0, 255.0).astype(np.uint8)
                rgba = np.dstack([arr.astype(np.uint8), alpha])
                img = Image.fromarray(rgba, mode="RGBA")
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
                ox = (target_size - img.width) // 2
                oy = (target_size - img.height) // 2
                canvas.paste(img, (ox, oy), img)
                return canvas
            except Exception:
                continue
    return None


def _active_caption(scenario: DebateScenario, t_sec: float) -> Tuple[str, str, str, str, float]:
    """
    Return (speaker_code, speaker_name, tag, text, progress_0_to_1) for timestamp t_sec.
    """
    active = None
    for cap in scenario.captions:
        s = float(cap.get("start", 0.0))
        e = float(cap.get("end", 0.0))
        if s <= t_sec <= e:
            active = cap
    if active is None and scenario.captions:
        # Find closest preceding or first caption
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


def _interpolate_bands(bands_16: List[float], target_count: int = 32) -> np.ndarray:
    x_old = np.linspace(0.0, 1.0, len(bands_16))
    x_new = np.linspace(0.0, 1.0, target_count)
    return np.interp(x_new, x_old, bands_16)


def _make_radial_glow(width: int, height: int, cx: int, cy: int, radius: int, color: Tuple[int, int, int], max_alpha: int = 95) -> Image.Image:
    """Create a pre-blurred soft radial neon bloom layer."""
    y, x = np.ogrid[:height, :width]
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    norm = np.clip(1.0 - (dist / float(radius)), 0.0, 1.0) ** 2.2
    alpha = (norm * max_alpha).astype(np.uint8)
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[..., 0] = color[0]
    rgba[..., 1] = color[1]
    rgba[..., 2] = color[2]
    rgba[..., 3] = alpha
    return Image.fromarray(rgba, mode="RGBA")


def _build_base_background(width: int, height: int) -> Image.Image:
    """Create a sleek deep-obsidian gradient background with ultra-subtle architectural grid lines."""
    y = np.linspace(0.0, 1.0, height)[:, None]
    x = np.linspace(0.0, 1.0, width)[None, :]
    r = (6 + 6 * y + 3 * (1.0 - x)).astype(np.uint8)
    g = (9 + 10 * y + 4 * x).astype(np.uint8)
    b = (18 + 16 * y + 8 * (1.0 - y)).astype(np.uint8)
    rgb = np.dstack([np.broadcast_to(r, (height, width)), np.broadcast_to(g, (height, width)), np.broadcast_to(b, (height, width))])
    img = Image.fromarray(rgb, mode="RGB").convert("RGBA")

    grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid)
    step = 64
    for gx in range(0, width, step):
        gdraw.line([(gx, 0), (gx, height)], fill=(148, 163, 184, 7), width=1)
    for gy in range(0, height, step):
        gdraw.line([(0, gy), (width, gy)], fill=(148, 163, 184, 7), width=1)

    return Image.alpha_composite(img, grid)


def _draw_voice_orb(
    overlay_draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    base_r: int,
    rms: float,
    speaking: bool,
    primary_rgb: Tuple[int, int, int],
    secondary_rgb: Tuple[int, int, int],
    phase: float,
    initials: str,
    font_initials: ImageFont.ImageFont,
) -> None:
    """Draw multi-ring harmonic glowing voice avatar orb."""
    if speaking:
        for ring_idx in range(3, 0, -1):
            wave_offset = math.sin(phase * 3.2 + ring_idx) * 3.0
            r_outer = int(base_r + ring_idx * (8 + rms * 18) + wave_offset)
            alpha = max(12, int((75 - ring_idx * 18) * (0.5 + min(1.0, rms) * 0.5)))
            overlay_draw.ellipse(
                [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
                fill=(primary_rgb[0], primary_rgb[1], primary_rgb[2], alpha // 3),
                outline=(primary_rgb[0], primary_rgb[1], primary_rgb[2], alpha),
                width=2,
            )

    core_r = int(base_r + (rms * 6 if speaking else 0))
    fill_col = (primary_rgb[0] // 5, primary_rgb[1] // 5, primary_rgb[2] // 5, 230) if speaking else (15, 23, 42, 220)
    border_col = (*primary_rgb, 245) if speaking else (100, 116, 139, 110)
    overlay_draw.ellipse(
        [cx - core_r, cy - core_r, cx + core_r, cy + core_r],
        fill=fill_col,
        outline=border_col,
        width=2,
    )
    bbox = overlay_draw.textbbox((0, 0), initials, font=font_initials)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    txt_col = (*secondary_rgb, 255) if speaking else (148, 163, 184, 210)
    overlay_draw.text((cx - tw // 2, cy - th // 2 - 2), initials, fill=txt_col, font=font_initials)


def render_debate_video(
    scenario: DebateScenario,
    audio_path: Path,
    output_mp4: Path,
    fps: int = 24,
    max_duration_sec: float = 28.0,
    width: int = 1280,
    height: int = 720,
    style: str = "glass_studio",
) -> Path:
    """
    Render an ultra-modern Full-Duplex AI Debate video in one of 3 broadcast styles:
      - 'glass_studio'  (1280x720)
      - 'split_wave'    (1280x720)
      - 'vertical_reel' (1080x1920 when style=='vertical_reel' if default dimensions passed)
    """
    if style == "vertical_reel" and width == 1280 and height == 720:
        width, height = 1080, 1920

    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    telemetry = analyze_stereo_stream(audio_path, fps=fps, max_duration_sec=max_duration_sec)
    actual_duration = len(telemetry) / float(fps)

    # Colors: Electric Cyan (Speaker A) & Neon Emerald-Mint (Speaker B)
    col_a = (0, 240, 255)
    col_a_soft = (165, 243, 252)
    col_b = (16, 235, 155)
    col_b_soft = (167, 243, 208)
    col_overlap = (251, 191, 36)

    base_bg = _build_base_background(width, height)
    logo_small = _load_brand_logo(target_size=42 if style != "vertical_reel" else 56)
    logo_watermark = _load_brand_logo(target_size=180 if style != "vertical_reel" else 240)
    if logo_watermark is not None:
        wm_arr = np.array(logo_watermark)
        wm_arr[..., 3] = (wm_arr[..., 3].astype(np.float32) * 0.08).astype(np.uint8)
        logo_watermark = Image.fromarray(wm_arr, mode="RGBA")
        wx = (width - logo_watermark.width) // 2
        wy = (height - logo_watermark.height) // 2 - (20 if style != "vertical_reel" else 80)
        base_bg.paste(logo_watermark, (wx, wy), logo_watermark)

    # Pre-compute ambient glow maps
    if style == "vertical_reel":
        glow_a = _make_radial_glow(width, height, 280, 740, 420, col_a, max_alpha=78)
        glow_b = _make_radial_glow(width, height, 800, 740, 420, col_b, max_alpha=78)
        glow_ov = _make_radial_glow(width, height, 540, 740, 460, col_overlap, max_alpha=85)
    else:
        glow_a = _make_radial_glow(width, height, 320, 360, 390, col_a, max_alpha=75)
        glow_b = _make_radial_glow(width, height, 960, 360, 390, col_b, max_alpha=75)
        glow_ov = _make_radial_glow(width, height, 640, 350, 410, col_overlap, max_alpha=82)

    # Fonts
    is_vert = style == "vertical_reel"
    f_brand = _load_font(22 if is_vert else 15, bold=True)
    f_pill = _load_font(17 if is_vert else 13, bold=True)
    f_title = _load_font(42 if is_vert else 30, bold=True)
    f_sub = _load_font(22 if is_vert else 16, bold=False)
    f_name = _load_font(28 if is_vert else 21, bold=True)
    f_role = _load_font(16 if is_vert else 13, bold=False)
    f_dialogue = _load_font(27 if is_vert else 19, bold=True)
    f_footer = _load_font(18 if is_vert else 12, bold=False)

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
        "20",
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

    smooth_l_bands = np.zeros(32, dtype=np.float32)
    smooth_r_bands = np.zeros(32, dtype=np.float32)
    smooth_l_rms = 0.0
    smooth_r_rms = 0.0

    initials_a = "".join([p[0] for p in scenario.speaker_a_name.split()[:2]]).upper() or "A"
    initials_b = "".join([p[0] for p in scenario.speaker_b_name.split()[:2]]).upper() or "B"

    try:
        for frame in telemetry:
            t_sec = frame.timestamp_sec
            smooth_l_rms = 0.62 * frame.left_rms + 0.38 * smooth_l_rms
            smooth_r_rms = 0.62 * frame.right_rms + 0.38 * smooth_r_rms
            cur_l = _interpolate_bands(frame.left_bands, 32)
            cur_r = _interpolate_bands(frame.right_bands, 32)
            smooth_l_bands = 0.65 * cur_l + 0.35 * smooth_l_bands
            smooth_r_bands = 0.65 * cur_r + 0.35 * smooth_r_bands

            canvas = base_bg.copy()
            if frame.left_speaking or smooth_l_rms > 0.08:
                canvas = Image.alpha_composite(canvas, glow_a)
            if frame.right_speaking or smooth_r_rms > 0.08:
                canvas = Image.alpha_composite(canvas, glow_b)
            if frame.is_overlap:
                canvas = Image.alpha_composite(canvas, glow_ov)

            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            spk_code, spk_name, turn_tag, cap_text, prog = _active_caption(scenario, t_sec)
            active_col = col_a if spk_code == "A" else col_b

            if style == "vertical_reel":
                # --- STYLE 3: 9:16 VERTICAL VIRAL REEL (1080x1920) ---
                # Top Floating Brand Bar
                draw.rounded_rectangle([54, 64, width - 54, 152], radius=44, fill=(15, 23, 42, 185), outline=(255, 255, 255, 35), width=1)
                if logo_small:
                    overlay.paste(logo_small, (80, 80), logo_small)
                draw.text((150, 94), "RANUK IT SOLUTIONS  •  AI DEBATE", fill=(248, 250, 252, 255), font=f_brand)
                draw.rounded_rectangle([width - 310, 84, width - 82, 132], radius=24, fill=(0, 240, 255, 28), outline=(0, 240, 255, 130), width=1)
                draw.text((width - 284, 97), "● FULL-DUPLEX 24kHz", fill=(165, 243, 252, 255), font=f_pill)

                # Editorial Title Block
                title_lines = textwrap.wrap(scenario.title, width=26)[:2]
                ty = 195
                for line in title_lines:
                    draw.text((64, ty), line, fill=(255, 255, 255, 255), font=f_title)
                    ty += 52
                draw.text((64, ty + 8), scenario.subtitle[:64], fill=(148, 163, 184, 235), font=f_sub)
                draw.rounded_rectangle([64, ty + 48, 320, ty + 53], radius=3, fill=(0, 240, 255, 210))

                # Dual Speaker Glass Pods
                pod_top, pod_bot = 430, 1060
                # Left Pod
                draw.rounded_rectangle(
                    [54, pod_top, 518, pod_bot],
                    radius=28,
                    fill=(15, 23, 42, 165),
                    outline=(*col_a, 185) if frame.left_speaking else (255, 255, 255, 30),
                    width=2 if frame.left_speaking else 1,
                )
                _draw_voice_orb(draw, 286, 565, 48, smooth_l_rms, frame.left_speaking, col_a, col_a_soft, t_sec, initials_a, f_name)
                b_a = draw.textbbox((0, 0), scenario.speaker_a_name, font=f_name)
                draw.text((286 - (b_a[2] - b_a[0]) // 2, 655), scenario.speaker_a_name, fill=(248, 250, 252, 255), font=f_name)
                r_a = draw.textbbox((0, 0), scenario.speaker_a_role, font=f_role)
                draw.text((286 - (r_a[2] - r_a[0]) // 2, 694), scenario.speaker_a_role, fill=(148, 163, 184, 220), font=f_role)

                # Left Mirrored Equalizer inside Left Pod
                mid_y = 885
                for idx in range(24):
                    val = float(smooth_l_bands[idx])
                    bx = 88 + idx * 16
                    bh = int(6 + val * 115) if frame.left_speaking else int(4 + val * 18)
                    alpha = 235 if frame.left_speaking else 75
                    draw.rounded_rectangle([bx, mid_y - bh, bx + 10, mid_y + int(bh * 0.55)], radius=5, fill=(*col_a, alpha))

                # Right Pod
                draw.rounded_rectangle(
                    [562, pod_top, width - 54, pod_bot],
                    radius=28,
                    fill=(15, 23, 42, 165),
                    outline=(*col_b, 185) if frame.right_speaking else (255, 255, 255, 30),
                    width=2 if frame.right_speaking else 1,
                )
                _draw_voice_orb(draw, 794, 565, 48, smooth_r_rms, frame.right_speaking, col_b, col_b_soft, t_sec, initials_b, f_name)
                b_b = draw.textbbox((0, 0), scenario.speaker_b_name, font=f_name)
                draw.text((794 - (b_b[2] - b_b[0]) // 2, 655), scenario.speaker_b_name, fill=(248, 250, 252, 255), font=f_name)
                r_b = draw.textbbox((0, 0), scenario.speaker_b_role, font=f_role)
                draw.text((794 - (r_b[2] - r_b[0]) // 2, 694), scenario.speaker_b_role, fill=(148, 163, 184, 220), font=f_role)

                for idx in range(24):
                    val = float(smooth_r_bands[idx])
                    bx = 596 + idx * 16
                    bh = int(6 + val * 115) if frame.right_speaking else int(4 + val * 18)
                    alpha = 235 if frame.right_speaking else 75
                    draw.rounded_rectangle([bx, mid_y - bh, bx + 10, mid_y + int(bh * 0.55)], radius=5, fill=(*col_b, alpha))

                # Full-Duplex Overlap Status Pill
                if frame.is_overlap:
                    draw.rounded_rectangle([140, 1095, width - 140, 1165], radius=35, fill=(120, 53, 15, 225), outline=(251, 191, 36, 255), width=2)
                    draw.text((225, 1118), "[LIVE] SOLAPAMIENTO FULL-DUPLEX ACTIVO  •  180ms", fill=(254, 243, 199, 255), font=f_pill)
                else:
                    draw.rounded_rectangle([190, 1095, width - 190, 1165], radius=35, fill=(15, 23, 42, 180), outline=(255, 255, 255, 35), width=1)
                    draw.text((275, 1118), f"CANAL DUAL SIMULTÁNEO  •  INTERRUPCIONES: {frame.cumulative_overlaps}", fill=(148, 163, 184, 235), font=f_pill)

                # Cinema Subtitle Stage (Large Mobile Card)
                dock_top, dock_bot = 1205, 1720
                draw.rounded_rectangle([54, dock_top, width - 54, dock_bot], radius=32, fill=(10, 16, 30, 215), outline=(*active_col, 140), width=2)
                draw.rounded_rectangle([94, dock_top + 38, 410, dock_top + 88], radius=25, fill=(*active_col, 35), outline=(*active_col, 190), width=1)
                draw.text((120, dock_top + 52), spk_name.upper(), fill=(255, 255, 255, 255), font=f_pill)
                draw.text((435, dock_top + 52), f"•  {turn_tag}", fill=(*active_col, 240), font=f_pill)

                wrapped_cap = textwrap.wrap(f"“{cap_text}”", width=42)[:6]
                cy_text = dock_top + 115
                for line in wrapped_cap:
                    draw.text((94, cy_text), line, fill=(248, 250, 252, 255), font=f_dialogue)
                    cy_text += 44

                # Utterance Progress Bar
                bar_w = int((width - 188) * prog)
                draw.rounded_rectangle([94, dock_bot - 36, width - 94, dock_bot - 26], radius=5, fill=(51, 65, 85, 130))
                if bar_w > 10:
                    draw.rounded_rectangle([94, dock_bot - 36, 94 + bar_w, dock_bot - 26], radius=5, fill=(*active_col, 245))

                draw.text((220, 1785), "ranuk.dev  •  Ranuk IT Solutions  •  NVIDIA PersonaPlex 7B", fill=(148, 163, 184, 200), font=f_footer)

            elif style == "split_wave":
                # --- STYLE 2: MINIMALIST EXECUTIVE SPLIT-WAVE ARENA (1280x720) ---
                # Top Floating Glass Pill
                draw.rounded_rectangle([40, 22, width - 40, 74], radius=26, fill=(15, 23, 42, 180), outline=(255, 255, 255, 32), width=1)
                if logo_small:
                    overlay.paste(logo_small, (58, 27), logo_small)
                draw.text((112, 38), "RANUK IT SOLUTIONS  •  EXECUTIVE DEBATE ARENA", fill=(248, 250, 252, 255), font=f_brand)
                if frame.is_overlap:
                    draw.rounded_rectangle([width - 420, 31, width - 58, 65], radius=17, fill=(120, 53, 15, 220), outline=(251, 191, 36, 255), width=1)
                    draw.text((width - 398, 40), "● LIVE FULL-DUPLEX OVERLAP (180ms)", fill=(254, 243, 199, 255), font=f_pill)
                else:
                    draw.rounded_rectangle([width - 395, 31, width - 58, 65], radius=17, fill=(0, 240, 255, 22), outline=(0, 240, 255, 95), width=1)
                    draw.text((width - 375, 40), f"● DUAL-STREAM 24kHz  •  OVERLAPS: {frame.cumulative_overlaps}", fill=(165, 243, 252, 245), font=f_pill)

                # Title & Subtitle
                draw.text((48, 92), scenario.title, fill=(255, 255, 255, 255), font=f_title)
                draw.text((48, 132), scenario.subtitle, fill=(148, 163, 184, 235), font=f_sub)

                # Compact Floating Speaker Headers
                # Left Speaker Pill
                draw.rounded_rectangle([48, 172, 520, 256], radius=20, fill=(15, 23, 42, 175), outline=(*col_a, 180) if frame.left_speaking else (255, 255, 255, 28), width=2 if frame.left_speaking else 1)
                _draw_voice_orb(draw, 98, 214, 22, smooth_l_rms, frame.left_speaking, col_a, col_a_soft, t_sec, initials_a, f_brand)
                draw.text((144, 190), scenario.speaker_a_name, fill=(248, 250, 252, 255), font=f_name)
                draw.text((144, 219), scenario.speaker_a_role, fill=(148, 163, 184, 220), font=f_role)

                # Right Speaker Pill
                draw.rounded_rectangle([width - 520, 172, width - 48, 256], radius=20, fill=(15, 23, 42, 175), outline=(*col_b, 180) if frame.right_speaking else (255, 255, 255, 28), width=2 if frame.right_speaking else 1)
                _draw_voice_orb(draw, width - 470, 214, 22, smooth_r_rms, frame.right_speaking, col_b, col_b_soft, t_sec, initials_b, f_brand)
                draw.text((width - 424, 190), scenario.speaker_b_name, fill=(248, 250, 252, 255), font=f_name)
                draw.text((width - 424, 219), scenario.speaker_b_role, fill=(148, 163, 184, 220), font=f_role)

                # Full-Width 64-Band Mirrored Acoustic Spine
                spine_y = 395
                draw.rounded_rectangle([48, 274, width - 48, 516], radius=24, fill=(10, 16, 30, 155), outline=(255, 255, 255, 25), width=1)
                bands_64_l = _interpolate_bands(list(smooth_l_bands), 64)
                bands_64_r = _interpolate_bands(list(smooth_r_bands), 64)
                for b_idx in range(64):
                    bx = 76 + b_idx * 17.6
                    lh = int(5 + float(bands_64_l[b_idx]) * 98) if frame.left_speaking else int(3 + float(bands_64_l[b_idx]) * 14)
                    rh = int(5 + float(bands_64_r[b_idx]) * 98) if frame.right_speaking else int(3 + float(bands_64_r[b_idx]) * 14)
                    la = 240 if frame.left_speaking else 75
                    ra = 240 if frame.right_speaking else 75
                    draw.rounded_rectangle([bx, spine_y - lh, bx + 10, spine_y - 2], radius=4, fill=(*col_a, la))
                    draw.rounded_rectangle([bx, spine_y + 2, bx + 10, spine_y + rh], radius=4, fill=(*col_b, ra))

                # Center Horizon Line
                line_col = (251, 191, 36, 220) if frame.is_overlap else (255, 255, 255, 45)
                draw.line([(68, spine_y), (width - 68, spine_y)], fill=line_col, width=2 if frame.is_overlap else 1)

                # Cinema Subtitle Dock
                draw.rounded_rectangle([48, 532, width - 48, 690], radius=22, fill=(10, 16, 30, 220), outline=(*active_col, 130), width=1)
                draw.rounded_rectangle([74, 548, 290, 578], radius=15, fill=(*active_col, 35), outline=(*active_col, 185), width=1)
                draw.text((92, 555), spk_name.upper(), fill=(255, 255, 255, 255), font=f_pill)
                draw.text((308, 555), f"•  {turn_tag}", fill=(*active_col, 240), font=f_pill)
                draw.text((width - 340, 555), f"t = {t_sec:05.2f}s  •  ranuk.dev", fill=(148, 163, 184, 195), font=f_footer)

                wrapped = textwrap.wrap(f"“{cap_text}”", width=92)[:3]
                cy_t = 588
                for ln in wrapped:
                    draw.text((74, cy_t), ln, fill=(248, 250, 252, 255), font=f_dialogue)
                    cy_t += 26

                bar_w = int((width - 148) * prog)
                draw.rounded_rectangle([74, 672, width - 74, 678], radius=3, fill=(51, 65, 85, 130))
                if bar_w > 6:
                    draw.rounded_rectangle([74, 672, 74 + bar_w, 678], radius=3, fill=(*active_col, 245))

            else:
                # --- STYLE 1 (DEFAULT): NEON GLASS STUDIO (1280x720) ---
                # Floating Glass Top Header Bar
                draw.rounded_rectangle([38, 18, width - 38, 70], radius=26, fill=(15, 23, 42, 185), outline=(255, 255, 255, 34), width=1)
                if logo_small:
                    overlay.paste(logo_small, (56, 23), logo_small)
                draw.text((110, 34), "RANUK IT SOLUTIONS  ×  AI DEBATE STUDIO", fill=(248, 250, 252, 255), font=f_brand)

                if frame.is_overlap:
                    draw.rounded_rectangle([width - 445, 27, width - 54, 61], radius=17, fill=(120, 53, 15, 225), outline=(251, 191, 36, 255), width=2)
                    draw.text((width - 424, 36), "[LIVE] SOLAPAMIENTO FULL-DUPLEX ACTIVO", fill=(254, 243, 199, 255), font=f_pill)
                else:
                    draw.rounded_rectangle([width - 415, 27, width - 54, 61], radius=17, fill=(0, 240, 255, 24), outline=(0, 240, 255, 105), width=1)
                    draw.text((width - 395, 36), f"● FULL-DUPLEX 24kHz  •  OVERLAPS: {frame.cumulative_overlaps}", fill=(165, 243, 252, 245), font=f_pill)

                # Crisp Editorial Title & Subtitle
                draw.text((44, 86), scenario.title, fill=(255, 255, 255, 255), font=f_title)
                draw.text((44, 126), scenario.subtitle, fill=(148, 163, 184, 235), font=f_sub)
                draw.rounded_rectangle([44, 154, 240, 158], radius=2, fill=(0, 240, 255, 220))
                draw.rounded_rectangle([246, 154, 340, 158], radius=2, fill=(16, 235, 155, 220))

                # Left Glass Speaker Card (Speaker A)
                draw.rounded_rectangle(
                    [40, 174, 616, 514],
                    radius=24,
                    fill=(15, 23, 42, 162),
                    outline=(*col_a, 190) if frame.left_speaking else (255, 255, 255, 30),
                    width=2 if frame.left_speaking else 1,
                )
                _draw_voice_orb(draw, 118, 252, 28, smooth_l_rms, frame.left_speaking, col_a, col_a_soft, t_sec, initials_a, f_name)
                draw.text((178, 212), scenario.speaker_a_name, fill=(248, 250, 252, 255), font=f_name)
                draw.text((178, 242), scenario.speaker_a_role, fill=(148, 163, 184, 225), font=f_role)
                l_pill_txt = "● TRANSMITIENDO (CANAL IZQ)" if frame.left_speaking else "○ ESCUCHA ACTIVA FULL-DUPLEX"
                l_pill_col = (*col_a, 240) if frame.left_speaking else (100, 116, 139, 195)
                draw.text((178, 270), l_pill_txt, fill=l_pill_col, font=f_pill)

                # Left 32-Band Harmonic Mirrored Equalizer
                eq_y = 418
                for idx in range(32):
                    val = float(smooth_l_bands[idx])
                    bx = 72 + idx * 16
                    bh = int(6 + val * 84) if frame.left_speaking else int(3 + val * 14)
                    alpha = 235 if frame.left_speaking else 70
                    draw.rounded_rectangle([bx, eq_y - bh, bx + 10, eq_y], radius=4, fill=(*col_a, alpha))
                    # Soft floor reflection
                    draw.rounded_rectangle([bx, eq_y + 4, bx + 10, eq_y + 4 + int(bh * 0.38)], radius=3, fill=(*col_a, alpha // 3))

                # Right Glass Speaker Card (Speaker B)
                draw.rounded_rectangle(
                    [664, 174, 1240, 514],
                    radius=24,
                    fill=(15, 23, 42, 162),
                    outline=(*col_b, 190) if frame.right_speaking else (255, 255, 255, 30),
                    width=2 if frame.right_speaking else 1,
                )
                _draw_voice_orb(draw, 742, 252, 28, smooth_r_rms, frame.right_speaking, col_b, col_b_soft, t_sec, initials_b, f_name)
                draw.text((802, 212), scenario.speaker_b_name, fill=(248, 250, 252, 255), font=f_name)
                draw.text((802, 242), scenario.speaker_b_role, fill=(148, 163, 184, 225), font=f_role)
                r_pill_txt = "● TRANSMITIENDO (CANAL DER)" if frame.right_speaking else "○ ESCUCHA ACTIVA FULL-DUPLEX"
                r_pill_col = (*col_b, 240) if frame.right_speaking else (100, 116, 139, 195)
                draw.text((802, 270), r_pill_txt, fill=r_pill_col, font=f_pill)

                for idx in range(32):
                    val = float(smooth_r_bands[idx])
                    bx = 696 + idx * 16
                    bh = int(6 + val * 84) if frame.right_speaking else int(3 + val * 14)
                    alpha = 235 if frame.right_speaking else 70
                    draw.rounded_rectangle([bx, eq_y - bh, bx + 10, eq_y], radius=4, fill=(*col_b, alpha))
                    draw.rounded_rectangle([bx, eq_y + 4, bx + 10, eq_y + 4 + int(bh * 0.38)], radius=3, fill=(*col_b, alpha // 3))

                # Center Dynamic Full-Duplex Bridge Node (Geometric Vector Icon)
                bridge_col = (251, 191, 36, 245) if frame.is_overlap else (0, 240, 255, 130)
                draw.ellipse([620, 324, 660, 364], fill=(15, 23, 42, 235), outline=bridge_col, width=2)
                for b_i, b_h in enumerate([6, 12, 16, 12, 6]):
                    bx_c = 630 + b_i * 5
                    draw.line([(bx_c, 344 - b_h // 2), (bx_c, 344 + b_h // 2)], fill=bridge_col, width=2)

                # Cinema Live Dialogue Subtitle Dock
                draw.rounded_rectangle([40, 530, 1240, 692], radius=22, fill=(10, 16, 30, 222), outline=(*active_col, 135), width=1)
                draw.rounded_rectangle([68, 546, 286, 576], radius=15, fill=(*active_col, 35), outline=(*active_col, 190), width=1)
                draw.text((86, 553), spk_name.upper(), fill=(255, 255, 255, 255), font=f_pill)
                draw.text((304, 553), f"•  {turn_tag}", fill=(*active_col, 240), font=f_pill)
                draw.text((width - 375, 553), f"t = {t_sec:05.2f}s  •  ranuk.dev  •  PersonaPlex 7B", fill=(148, 163, 184, 195), font=f_footer)

                wrapped = textwrap.wrap(f"“{cap_text}”", width=92)[:3]
                cy_t = 586
                for ln in wrapped:
                    draw.text((68, cy_t), ln, fill=(248, 250, 252, 255), font=f_dialogue)
                    cy_t += 26

                # Utterance Progress Bar
                bar_w = int((1240 - 136) * prog)
                draw.rounded_rectangle([68, 672, 1240 - 68, 678], radius=3, fill=(51, 65, 85, 130))
                if bar_w > 6:
                    draw.rounded_rectangle([68, 672, 68 + bar_w, 678], radius=3, fill=(*active_col, 245))

            final_rgb = Image.alpha_composite(canvas, overlay).convert("RGB")
            proc.stdin.write(final_rgb.tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=90)

    if proc.returncode != 0 or not output_mp4.exists():
        raise RuntimeError(f"FFmpeg video rendering failed with code {proc.returncode}")
    return output_mp4
