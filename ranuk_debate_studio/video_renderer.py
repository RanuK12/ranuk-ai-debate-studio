# © 2026 Ranuk IT Solutions — ranuk.dev
"""
video_renderer.py — Multi-Model Full-Duplex AI Debate Video Renderer (Ranuk IT Solutions).

Supports 4 Intercalating 9:16 Vertical UI Models for YouTube Shorts & TikTok:
  1. "model_1_cyber_nexus"      — Ranuk Cyber-Glass Arena (Electric Cyan vs. Neon Emerald, Twin Vertical Pods + VS Bridge)
  2. "model_2_quantum_matrix"   — Quantum Command Deck (Hyper Violet vs. Solar Gold, Stacked Horizontal HUD Decks)
  3. "model_3_silicon_warroom"  — Silicon Valley War Room (Laser Crimson vs. Ice Cobalt, Tactical Cards + Acoustic Clash Spine)
  4. "model_4_blackwell_tensor" — Blackwell Tensor Studio (Matrix Tensor Green vs. Plasma Cyan, 360° Radial Halos + LED VU Meters)

Also supports 16:9 Landscape ("glass_studio", "split_wave").
Guarantees 100% verbatim synchronized subtitles with real-time karaoke word highlighting in the bottom stage.
Zero tofu/missing emoji glyphs: all icons are vector-rendered natively.
"""
from __future__ import annotations

import json
import math
import subprocess
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .personaplex_duo import DebateScenario, PRESET_SCENARIOS
from .waveform_analyzer import FrameAudioTelemetry, analyze_stereo_stream, find_ffmpeg

REPO_ROOT = Path(__file__).resolve().parent.parent
BRAND_DIR = REPO_ROOT / "assets" / "brand"

VERTICAL_UI_MODELS: Tuple[str, ...] = (
    "model_1_cyber_nexus",
    "model_2_quantum_matrix",
    "model_3_silicon_warroom",
    "model_4_blackwell_tensor",
)

MODEL_THEMES: Dict[str, Dict[str, Any]] = {
    "model_1_cyber_nexus": {
        "name": "MODELO 1 • CYBER-GLASS ARENA",
        "badge": "CYBER-GLASS HUD",
        "bg_top": (4, 8, 18),
        "bg_bot": (8, 15, 30),
        "col_a": (0, 240, 255),        # Electric Cyan
        "col_a_sub": (37, 99, 235),    # Deep Cobalt
        "col_b": (16, 235, 155),       # Neon Emerald
        "col_b_sub": (5, 150, 105),    # Deep Emerald
        "col_overlap": (251, 191, 36), # Amber Gold
        "card_bg": (10, 16, 28),
        "grid_type": "blueprint",
    },
    "model_2_quantum_matrix": {
        "name": "MODELO 2 • QUANTUM COMMAND DECK",
        "badge": "QUANTUM MATRIX",
        "bg_top": (9, 4, 20),
        "bg_bot": (18, 8, 36),
        "col_a": (192, 132, 252),      # Hyper Violet
        "col_a_sub": (126, 34, 206),   # Deep Purple
        "col_b": (251, 191, 36),       # Solar Gold
        "col_b_sub": (217, 119, 6),    # Deep Amber
        "col_overlap": (0, 240, 255),  # Electric Cyan
        "card_bg": (16, 10, 30),
        "grid_type": "perspective",
    },
    "model_3_silicon_warroom": {
        "name": "MODELO 3 • SILICON VALLEY WAR ROOM",
        "badge": "WAR ROOM TACTICAL",
        "bg_top": (10, 10, 15),
        "bg_bot": (18, 14, 22),
        "col_a": (255, 42, 95),        # Laser Crimson
        "col_a_sub": (190, 18, 60),    # Deep Rose
        "col_b": (56, 189, 248),       # Ice Cobalt
        "col_b_sub": (2, 132, 199),    # Deep Sky
        "col_overlap": (253, 224, 71), # Tactical Yellow
        "card_bg": (16, 16, 24),
        "grid_type": "dots",
    },
    "model_4_blackwell_tensor": {
        "name": "MODELO 4 • BLACKWELL TENSOR STUDIO",
        "badge": "TENSOR ENGINE",
        "bg_top": (4, 11, 7),
        "bg_bot": (7, 20, 14),
        "col_a": (74, 222, 128),       # Blackwell Tensor Green
        "col_a_sub": (22, 163, 74),    # Forest Matrix
        "col_b": (34, 211, 238),       # Plasma Cyan
        "col_b_sub": (8, 145, 178),    # Deep Cyan
        "col_overlap": (190, 242, 100),# Lime Volt
        "card_bg": (8, 18, 14),
        "grid_type": "circuit",
    },
}


def _interpolate_bands(bands_16: List[float], target_count: int = 24) -> np.ndarray:
    x_old = np.linspace(0.0, 1.0, len(bands_16))
    x_new = np.linspace(0.0, 1.0, target_count)
    return np.interp(x_new, x_old, bands_16)


def select_ui_model_for_index(index: int) -> str:
    """Return one of the 4 vertical UI models in strict rotation."""
    return VERTICAL_UI_MODELS[index % len(VERTICAL_UI_MODELS)]


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


def _load_ranuk_apple_logo(size: int = 48) -> Optional[Image.Image]:
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
                alpha = np.clip((lum - 14.0) * 2.5, 0.0, 255.0).astype(np.uint8)
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


def _draw_lightning_icon(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color: Tuple[int, int, int, int]) -> None:
    """Draw a crisp vector lightning bolt icon without relying on emoji fonts."""
    pts = [
        (x + int(size * 0.55), y),
        (x + int(size * 0.15), y + int(size * 0.55)),
        (x + int(size * 0.48), y + int(size * 0.55)),
        (x + int(size * 0.35), y + size),
        (x + int(size * 0.85), y + int(size * 0.42)),
        (x + int(size * 0.52), y + int(size * 0.42)),
    ]
    draw.polygon(pts, fill=color)


def _draw_mic_wave_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: Tuple[int, int, int, int]) -> None:
    """Draw a crisp vector live-audio pulse icon inside speaker pills."""
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=color)
    draw.arc([cx - 10, cy - 10, cx + 10, cy + 10], start=310, end=50, fill=color, width=2)
    draw.arc([cx - 10, cy - 10, cx + 10, cy + 10], start=130, end=230, fill=color, width=2)


def _ensure_scenario_captions(scenario: DebateScenario, audio_path: Path, actual_duration: float) -> List[Dict[str, Any]]:
    """Guarantee non-empty synchronized captions for any scenario."""
    meta_json = audio_path.with_suffix(".json")
    if meta_json.exists():
        try:
            loaded = json.loads(meta_json.read_text(encoding="utf-8"))
            if isinstance(loaded, list) and len(loaded) > 0:
                scenario.captions = loaded
                return loaded
        except Exception:
            pass

    if scenario.captions and len(scenario.captions) > 0:
        return list(scenario.captions)

    try:
        from .duplex_dialogue_synth import HOT_DEBATE_SCRIPTS
        if scenario.slug in HOT_DEBATE_SCRIPTS:
            base_sc, turns, _ = HOT_DEBATE_SCRIPTS[scenario.slug]
            total_chars = max(1, sum(len(t.text) for t in turns))
            usable_dur = max(5.0, actual_duration - 0.8)
            cursor = 0.35
            synthesized_caps: List[Dict[str, Any]] = []
            for t in turns:
                dur = max(1.8, (len(t.text) / total_chars) * usable_dur)
                start_t = max(0.0, cursor - (t.overlap_prev_ms / 1000.0 if synthesized_caps else 0.0))
                end_t = min(actual_duration, start_t + dur)
                spk_name = scenario.speaker_a_name if t.speaker == "A" else scenario.speaker_b_name
                synthesized_caps.append({
                    "start": round(start_t, 3),
                    "end": round(end_t, 3),
                    "speaker": t.speaker,
                    "speaker_name": spk_name,
                    "tag": t.tag,
                    "text": t.text,
                })
                cursor = end_t + 0.1
            scenario.captions = synthesized_caps
            return synthesized_caps
    except Exception:
        pass

    if scenario.slug in PRESET_SCENARIOS and PRESET_SCENARIOS[scenario.slug].captions:
        scenario.captions = list(PRESET_SCENARIOS[scenario.slug].captions)
        return list(scenario.captions)

    raise RuntimeError(f"CRITICAL: No captions found for debate scenario '{scenario.slug}' (audio={audio_path}).")


def _active_caption_with_context(
    scenario: DebateScenario, t_sec: float
) -> Tuple[str, str, str, str, float, int, int, Optional[Tuple[str, str]]]:
    caps = scenario.captions
    total = len(caps)
    if total == 0:
        return ("A", scenario.speaker_a_name, "LIVE DEBATE", scenario.subtitle, 0.5, 1, 1, None)

    active_idx = None
    for idx in range(total - 1, -1, -1):
        c = caps[idx]
        s = float(c.get("start", 0.0))
        e = float(c.get("end", 0.0))
        if s <= t_sec <= e:
            active_idx = idx
            break

    if active_idx is None:
        preceding = [i for i, c in enumerate(caps) if float(c.get("start", 0.0)) <= t_sec]
        active_idx = preceding[-1] if preceding else 0

    active = caps[active_idx]
    s = float(active.get("start", 0.0))
    e = max(s + 0.15, float(active.get("end", s + 1.0)))
    prog = min(1.0, max(0.0, (t_sec - s) / (e - s)))
    spk = str(active.get("speaker", "A"))
    spk_name = str(
        active.get("speaker_name")
        or (scenario.speaker_a_name if spk == "A" else scenario.speaker_b_name)
    )
    tag = str(active.get("tag", "LIVE ARGUMENT"))
    text = str(active.get("text", "")).strip()

    prev_info: Optional[Tuple[str, str]] = None
    if active_idx > 0:
        p_cap = caps[active_idx - 1]
        p_spk = str(p_cap.get("speaker", "A"))
        p_name = str(
            p_cap.get("speaker_name")
            or (scenario.speaker_a_name if p_spk == "A" else scenario.speaker_b_name)
        )
        p_text = str(p_cap.get("text", "")).strip()
        if p_text:
            prev_info = (p_name, p_text)

    return (spk, spk_name, tag, text, prog, active_idx + 1, total, prev_info)


def _boost_active_bands(bands: np.ndarray, is_speaking: bool, t_sec: float) -> Tuple[np.ndarray, float]:
    """Ensure active speaker always shows rich, dynamic frequency motion even between micro-syllables."""
    if not is_speaking:
        return bands, float(np.mean(bands))
    idx_arr = np.arange(len(bands), dtype=np.float32)
    synth_wave = (
        0.38 * np.sin(t_sec * 11.0 + idx_arr * 0.45) ** 2
        + 0.28 * np.cos(t_sec * 7.3 - idx_arr * 0.3) ** 2
        + 0.18
    )
    envelope = 1.0 - 0.35 * np.abs((idx_arr / max(1, len(bands) - 1)) - 0.45)
    boosted = np.maximum(bands * 1.35, synth_wave * envelope)
    boosted = np.clip(boosted, 0.15, 0.98)
    rms_out = max(0.32, float(np.mean(boosted) * 0.75))
    return boosted, rms_out


def _create_model_background(width: int, height: int, model_key: str) -> Image.Image:
    theme = MODEL_THEMES.get(model_key, MODEL_THEMES["model_1_cyber_nexus"])
    bg_top = theme["bg_top"]
    bg_bot = theme["bg_bot"]
    col_a = theme["col_a"]
    col_b = theme["col_b"]
    grid_type = theme["grid_type"]

    y, x = np.mgrid[:height, :width]
    fy = y / float(height)
    r_base = (bg_top[0] * (1.0 - fy) + bg_bot[0] * fy).astype(np.uint8)
    g_base = (bg_top[1] * (1.0 - fy) + bg_bot[1] * fy).astype(np.uint8)
    b_base = (bg_top[2] * (1.0 - fy) + bg_bot[2] * fy).astype(np.uint8)
    base_img = Image.fromarray(
        np.dstack([r_base, g_base, b_base, np.full((height, width), 255, dtype=np.uint8)]),
        mode="RGBA",
    )

    cx1, cy1 = int(width * 0.25), int(height * 0.36)
    cx2, cy2 = int(width * 0.75), int(height * 0.36)
    cx3, cy3 = int(width * 0.50), int(height * 0.68)
    r_scale = 550.0 if height > width else 440.0

    d1 = np.sqrt((x - cx1) ** 2 + (y - cy1) ** 2)
    a1 = (np.clip(1.0 - d1 / r_scale, 0.0, 1.0) ** 2.0) * 0.42

    d2 = np.sqrt((x - cx2) ** 2 + (y - cy2) ** 2)
    a2 = (np.clip(1.0 - d2 / r_scale, 0.0, 1.0) ** 2.0) * 0.42

    d3 = np.sqrt((x - cx3) ** 2 + (y - cy3) ** 2)
    a3 = (np.clip(1.0 - d3 / (r_scale * 1.15), 0.0, 1.0) ** 2.2) * 0.28

    r_glow = np.clip(a1 * col_a[0] + a2 * col_b[0] + a3 * ((col_a[0] + col_b[0]) // 2), 0, 255).astype(np.uint8)
    g_glow = np.clip(a1 * col_a[1] + a2 * col_b[1] + a3 * ((col_a[1] + col_b[1]) // 2), 0, 255).astype(np.uint8)
    b_glow = np.clip(a1 * col_a[2] + a2 * col_b[2] + a3 * ((col_a[2] + col_b[2]) // 2), 0, 255).astype(np.uint8)
    a_glow = np.clip((a1 + a2 + a3) * 255.0, 0, 205).astype(np.uint8)

    aurora = Image.fromarray(np.dstack([r_glow, g_glow, b_glow, a_glow]), mode="RGBA").filter(
        ImageFilter.GaussianBlur(24)
    )
    combined = Image.alpha_composite(base_img, aurora)

    grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid)

    if grid_type == "blueprint":
        step = 54
        for gx in range(0, width, step):
            gdraw.line([(gx, 0), (gx, height)], fill=(*col_a, 10), width=1)
        for gy in range(0, height, step):
            gdraw.line([(0, gy), (width, gy)], fill=(*col_b, 10), width=1)
        for gx in range(step, width, step * 3):
            for gy in range(step, height, step * 3):
                gdraw.line([(gx - 5, gy), (gx + 5, gy)], fill=(255, 255, 255, 28), width=1)
                gdraw.line([(gx, gy - 5), (gx, gy + 5)], fill=(255, 255, 255, 28), width=1)

    elif grid_type == "perspective":
        step = 64
        for gy in range(0, height, step):
            gdraw.line([(0, gy), (width, gy)], fill=(*col_a, 12), width=1)
        for gx in range(-width // 2, int(width * 1.5), 110):
            gdraw.line([(width // 2 + (gx - width // 2) // 3, 0), (gx, height)], fill=(*col_b, 11), width=1)

    elif grid_type == "dots":
        step = 36
        for gx in range(24, width, step):
            for gy in range(24, height, step):
                col = col_a if (gx + gy) % 72 == 0 else (255, 255, 255)
                gdraw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(*col, 24))

    elif grid_type == "circuit":
        step = 60
        for gx in range(0, width, step):
            gdraw.line([(gx, 0), (gx, height)], fill=(*col_a, 9), width=1)
        for gy in range(0, height, step):
            gdraw.line([(0, gy), (width, gy)], fill=(*col_b, 9), width=1)
        for i in range(1, 12):
            y_trace = (i * 155) % height
            x_turn = (i * 230) % (width - 200) + 100
            gdraw.line([(0, y_trace), (x_turn, y_trace), (x_turn + 35, y_trace + 35), (width, y_trace + 35)], fill=(*col_a, 20), width=2)
            gdraw.ellipse([x_turn - 4, y_trace - 4, x_turn + 4, y_trace + 4], fill=(*col_b, 48))

    return Image.alpha_composite(combined, grid)


def _draw_frosted_card(
    draw: ImageDraw.ImageDraw,
    rect: Tuple[int, int, int, int],
    radius: int = 28,
    fill_rgb: Tuple[int, int, int] = (12, 17, 28),
    fill_alpha: int = 195,
    is_active: bool = False,
    active_color: Tuple[int, int, int] = (0, 240, 255),
    chamfer: bool = False,
) -> None:
    x0, y0, x1, y1 = rect
    if chamfer:
        c = 22
        pts = [
            (x0 + c, y0),
            (x1 - c, y0),
            (x1, y0 + c),
            (x1, y1 - c),
            (x1 - c, y1),
            (x0 + c, y1),
            (x0, y1 - c),
            (x0, y0 + c),
        ]
        draw.polygon(pts, fill=(*fill_rgb, fill_alpha))
        outline_col = (*active_color, 240) if is_active else (255, 255, 255, 48)
        draw.line(pts + [pts[0]], fill=outline_col, width=3 if is_active else 1)
        if is_active:
            b_len = 36
            draw.line([(x0, y0 + c + b_len), (x0, y0 + c), (x0 + c, y0), (x0 + c + b_len, y0)], fill=(255, 255, 255, 225), width=3)
            draw.line([(x1, y1 - c - b_len), (x1, y1 - c), (x1 - c, y1), (x1 - c - b_len, y1)], fill=(255, 255, 255, 225), width=3)
    else:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=(*fill_rgb, fill_alpha))
        if is_active:
            draw.rounded_rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], radius=radius + 2, outline=(*active_color, 85), width=4)
            draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(*active_color, 245), width=2)
            draw.rounded_rectangle([x0 + 16, y0 + 1, x1 - 16, y0 + 3], radius=radius, fill=(255, 255, 255, 150))
        else:
            draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(255, 255, 255, 42), width=1)
            draw.rounded_rectangle([x0 + 18, y0 + 1, x1 - 18, y0 + 2], radius=radius, fill=(255, 255, 255, 65))


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
    max_halo_radius: int = 58,
) -> None:
    if speaking:
        for ring in [3, 2, 1]:
            r_boost = min(max_halo_radius - radius, int(ring * (6 + rms * 11) + math.sin(phase * 4.5 + ring) * 3))
            alpha = max(25, int((95 - ring * 22) * (0.7 + rms * 0.3)))
            draw.ellipse(
                [cx - (radius + r_boost), cy - (radius + r_boost), cx + (radius + r_boost), cy + (radius + r_boost)],
                fill=(*primary_color, alpha // 4),
                outline=(*primary_color, alpha),
                width=2,
            )

    r_core = radius + int(rms * 6 if speaking else 0)
    for step in range(r_core, 0, -3):
        frac = step / float(max(1, r_core))
        col = (
            int(primary_color[0] * frac + secondary_color[0] * (1 - frac)),
            int(primary_color[1] * frac + secondary_color[1] * (1 - frac)),
            int(primary_color[2] * frac + secondary_color[2] * (1 - frac)),
        )
        alpha = int(245 if speaking else 160)
        draw.ellipse([cx - step, cy - step, cx + step, cy + step], fill=(*col, alpha))

    sheen_box = [cx - int(r_core * 0.75), cy - int(r_core * 0.75), cx + int(r_core * 0.75), cy + int(r_core * 0.75)]
    draw.arc(sheen_box, start=205, end=335, fill=(255, 255, 255, 220 if speaking else 95), width=3)


def _draw_radial_halo_visualizer(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    base_radius: int,
    bands: np.ndarray,
    rms: float,
    speaking: bool,
    primary_color: Tuple[int, int, int],
    secondary_color: Tuple[int, int, int],
    phase: float,
) -> None:
    _draw_apple_siri_orb(draw, cx, cy, base_radius - 10, rms, speaking, primary_color, secondary_color, phase, max_halo_radius=base_radius + 10)
    num_rays = 24
    ray_vals = _interpolate_bands(list(bands), num_rays)
    for i in range(num_rays):
        angle = (2.0 * math.pi * i / num_rays) + phase * 0.4
        val = float(ray_vals[i])
        ray_len = int(10 + (val * 44 if speaking else val * 8))
        r0 = base_radius + 4
        r1 = r0 + ray_len
        x0 = cx + int(math.cos(angle) * r0)
        y0 = cy + int(math.sin(angle) * r0)
        x1 = cx + int(math.cos(angle) * r1)
        y1 = cy + int(math.sin(angle) * r1)
        alpha = 250 if speaking else 95
        draw.line([(x0, y0), (x1, y1)], fill=(*primary_color, alpha), width=4)


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
    max_height: int = 85,
    reflection: bool = True,
) -> None:
    smoothed = np.convolve(bands, [0.22, 0.56, 0.22], mode="same")
    for idx in range(min(bar_count, len(smoothed))):
        val = float(smoothed[idx])
        bx = x_start + idx * (bar_width + bar_gap)
        if speaking:
            h = int(10 + val * max_height)
            alpha = 250
        else:
            h = int(4 + val * 10)
            alpha = 80

        draw.rounded_rectangle(
            [bx, y_center - h, bx + bar_width, y_center + h],
            radius=max(2, bar_width // 2),
            fill=(*color_top, alpha),
        )
        if reflection:
            ref_h = int(h * 0.35)
            draw.rounded_rectangle(
                [bx, y_center + h + 5, bx + bar_width, y_center + h + 5 + ref_h],
                radius=max(2, bar_width // 2),
                fill=(*color_bot, alpha // 3),
            )


def _draw_wrapped_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    cx: int,
    y_start: int,
    max_chars_per_line: int,
    max_lines: int,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int, int],
    line_step: int = 24,
) -> int:
    lines = textwrap.wrap(text, width=max_chars_per_line)[:max_lines]
    cy = y_start
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, cy), ln, fill=fill, font=font)
        cy += line_step
    return cy


def _draw_ranuk_top_header_vertical(
    overlay: Image.Image,
    draw: ImageDraw.ImageDraw,
    width: int,
    logo_img: Optional[Image.Image],
    theme: Dict[str, Any],
    frame: FrameAudioTelemetry,
    f_brand: ImageFont.FreeTypeFont,
    f_badge: ImageFont.FreeTypeFont,
    chamfer: bool = False,
) -> None:
    hx0, hy0, hx1, hy1 = 46, 56, width - 46, 142
    col_a = theme["col_a"]
    col_b = theme["col_b"]
    col_ov = theme["col_overlap"]

    _draw_frosted_card(
        draw,
        (hx0, hy0, hx1, hy1),
        radius=43,
        fill_rgb=theme["card_bg"],
        fill_alpha=238,
        is_active=True,
        active_color=col_ov if frame.is_overlap else col_a,
        chamfer=chamfer,
    )

    if logo_img:
        overlay.paste(logo_img, (hx0 + 20, hy0 + (hy1 - hy0 - logo_img.height) // 2), logo_img)

    draw.text((hx0 + 86, hy0 + 17), "RANUK IT SOLUTIONS", fill=(255, 255, 255, 255), font=f_brand)
    draw.text((hx0 + 86, hy0 + 48), f"AI DEBATE ARENA  •  {theme['badge']}", fill=(*col_a, 240), font=f_badge)

    pill_w = 278
    px0 = hx1 - pill_w - 18
    py0, py1 = hy0 + 18, hy1 - 18
    if frame.is_overlap:
        draw.rounded_rectangle([px0, py0, hx1 - 18, py1], radius=24, fill=(*col_ov, 45), outline=(*col_ov, 240), width=2)
        _draw_lightning_icon(draw, px0 + 18, py0 + 13, 22, (*col_ov, 255))
        draw.text((px0 + 44, py0 + 14), "INTERRUPT 180ms", fill=(255, 250, 220, 255), font=f_badge)
    else:
        draw.rounded_rectangle([px0, py0, hx1 - 18, py1], radius=24, fill=(*col_b, 28), outline=(*col_b, 190), width=1)
        draw.ellipse([px0 + 20, py0 + 18, px0 + 32, py0 + 30], fill=(*col_b, 255))
        draw.text((px0 + 42, py0 + 14), "24kHz FULL-DUPLEX", fill=(225, 255, 245, 255), font=f_badge)


def _draw_topic_banner_vertical(
    draw: ImageDraw.ImageDraw,
    width: int,
    scenario: DebateScenario,
    theme: Dict[str, Any],
    f_title: ImageFont.FreeTypeFont,
    f_sub: ImageFont.FreeTypeFont,
) -> None:
    bx0, by0, bx1, by1 = 46, 160, width - 46, 344
    col_a = theme["col_a"]
    col_b = theme["col_b"]

    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=24, fill=(*theme["card_bg"], 215), outline=(255, 255, 255, 38), width=1)
    draw.rounded_rectangle([bx0 + 14, by0 + 18, bx0 + 22, by1 - 18], radius=4, fill=(*col_a, 255))

    title_lines = textwrap.wrap(scenario.title.upper(), width=32)[:2]
    ty = by0 + 18
    for ln in title_lines:
        draw.text((bx0 + 40, ty), ln, fill=(255, 255, 255, 255), font=f_title)
        ty += 44

    sub_lines = textwrap.wrap(scenario.subtitle, width=68)[:2]
    for sln in sub_lines:
        draw.text((bx0 + 40, ty + 4), sln, fill=(*col_b, 240), font=f_sub)
        ty += 24


def _draw_subtitle_stage_vertical(
    overlay: Image.Image,
    draw: ImageDraw.ImageDraw,
    width: int,
    theme: Dict[str, Any],
    spk_code: str,
    spk_name: str,
    turn_tag: str,
    cap_text: str,
    prog: float,
    turn_idx: int,
    total_turns: int,
    prev_info: Optional[Tuple[str, str]],
    t_sec: float,
    logo_small: Optional[Image.Image],
    f_pill: ImageFont.FreeTypeFont,
    f_sub_word: ImageFont.FreeTypeFont,
    f_prev: ImageFont.FreeTypeFont,
    f_footer: ImageFont.FreeTypeFont,
    chamfer: bool = False,
) -> None:
    sx0, sy0, sx1, sy1 = 46, 985, width - 46, 1505
    col_a = theme["col_a"]
    col_b = theme["col_b"]
    active_col = col_a if spk_code == "A" else col_b

    _draw_frosted_card(
        draw,
        (sx0, sy0, sx1, sy1),
        radius=30,
        fill_rgb=theme["card_bg"],
        fill_alpha=235,
        is_active=True,
        active_color=active_col,
        chamfer=chamfer,
    )

    # Top Speaker Pill with vector audio wave icon (zero missing emoji glyph!)
    name_label = spk_name.upper()
    bbox_n = draw.textbbox((0, 0), name_label, font=f_pill)
    nw = bbox_n[2] - bbox_n[0]
    px0, py0 = sx0 + 30, sy0 + 26
    px1, py1 = px0 + nw + 64, py0 + 44
    draw.rounded_rectangle([px0, py0, px1, py1], radius=22, fill=(*active_col, 45), outline=(*active_col, 240), width=2)
    _draw_mic_wave_icon(draw, px0 + 24, py0 + 22, (*active_col, 255))
    draw.text((px0 + 44, py0 + 11), name_label, fill=(255, 255, 255, 255), font=f_pill)

    draw.text((px1 + 16, py0 + 11), f"•  {turn_tag}", fill=(*active_col, 245), font=f_pill)

    cnt_txt = f"TURN {turn_idx:02d}/{total_turns:02d}"
    bbox_c = draw.textbbox((0, 0), cnt_txt, font=f_prev)
    cw = bbox_c[2] - bbox_c[0]
    draw.rounded_rectangle([sx1 - cw - 52, py0 + 4, sx1 - 28, py1 - 4], radius=14, fill=(255, 255, 255, 18), outline=(255, 255, 255, 55), width=1)
    draw.text((sx1 - cw - 40, py0 + 11), cnt_txt, fill=(210, 220, 235, 240), font=f_prev)

    text_area_top = sy0 + 88
    if prev_info is not None:
        p_name, p_text = prev_info
        short_prev = p_text if len(p_text) <= 66 else p_text[:63].rsplit(" ", 1)[0] + "..."
        prev_line = f">> PREV [{p_name.upper()}]: “{short_prev}”"
        draw.text((sx0 + 34, text_area_top), prev_line, fill=(148, 163, 184, 205), font=f_prev)
        draw.line([(sx0 + 34, text_area_top + 28), (sx1 - 34, text_area_top + 28)], fill=(255, 255, 255, 25), width=1)
        text_area_top += 42

    # --- Real-Time Word-by-Word Karaoke Subtitle Layout ---
    clean_words = cap_text.replace("—", " — ").split()
    if not clean_words:
        clean_words = ["..."]
    num_words = len(clean_words)
    active_word_idx = min(num_words - 1, max(0, int(prog * num_words)))

    max_line_w = (sx1 - sx0) - 72
    space_w = 13
    word_boxes: List[Tuple[str, int]] = []
    for w in clean_words:
        wb = draw.textbbox((0, 0), w, font=f_sub_word)
        word_boxes.append((w, wb[2] - wb[0]))

    lines: List[List[Tuple[int, str, int]]] = []
    cur_line: List[Tuple[int, str, int]] = []
    cur_w = 0
    for idx, (w_str, w_px) in enumerate(word_boxes):
        needed = w_px if not cur_line else (space_w + w_px)
        if cur_line and (cur_w + needed > max_line_w):
            lines.append(cur_line)
            cur_line = [(idx, w_str, w_px)]
            cur_w = w_px
        else:
            cur_line.append((idx, w_str, w_px))
            cur_w += needed
    if cur_line:
        lines.append(cur_line)

    visible_lines = lines[:6]
    line_h = 54
    total_text_h = len(visible_lines) * line_h
    avail_h = (sy1 - 54) - text_area_top
    cy = text_area_top + max(6, (avail_h - total_text_h) // 2)

    for ln in visible_lines:
        cx = sx0 + 36
        for w_idx, w_str, w_px in ln:
            is_current = w_idx == active_word_idx
            is_spoken = w_idx < active_word_idx

            if is_current:
                pad_x, pad_y = 10, 5
                draw.rounded_rectangle(
                    [cx - pad_x, cy - pad_y + 2, cx + w_px + pad_x, cy + 42 + pad_y],
                    radius=12,
                    fill=(*active_col, 245),
                    outline=(255, 255, 255, 240),
                    width=2,
                )
                draw.text((cx, cy), w_str, fill=(6, 10, 18, 255), font=f_sub_word)
            elif is_spoken:
                draw.text((cx, cy), w_str, fill=(255, 255, 255, 255), font=f_sub_word)
            else:
                draw.text((cx, cy), w_str, fill=(175, 190, 212, 220), font=f_sub_word)

            cx += w_px + space_w
        cy += line_h

    # Bottom Turn Progress Bar inside Subtitle Box
    bar_x0, bar_x1 = sx0 + 34, sx1 - 34
    bar_y = sy1 - 28
    draw.rounded_rectangle([bar_x0, bar_y, bar_x1, bar_y + 8], radius=4, fill=(255, 255, 255, 32))
    fill_w = int((bar_x1 - bar_x0) * prog)
    if fill_w > 8:
        draw.rounded_rectangle([bar_x0, bar_y, bar_x0 + fill_w, bar_y + 8], radius=4, fill=(*active_col, 255))

    # --- Ranuk IT Solutions Signature Footer Badge (y = 1522..1580) ---
    fy0, fy1 = 1522, 1580
    fw = 780
    fx0 = (width - fw) // 2
    draw.rounded_rectangle(
        [fx0, fy0, fx0 + fw, fy1],
        radius=29,
        fill=(*theme["card_bg"], 232),
        outline=(*col_a, 140),
        width=1,
    )
    if logo_small:
        overlay.paste(logo_small, (fx0 + 18, fy0 + (fy1 - fy0 - logo_small.height) // 2), logo_small)
    footer_txt = f"RANUK IT SOLUTIONS  •  ranuk.dev/debates  •  T+{t_sec:05.2f}s"
    draw.text((fx0 + 68, fy0 + 18), footer_txt, fill=(235, 242, 250, 245), font=f_footer)


def render_debate_video(
    scenario: DebateScenario,
    audio_path: Path,
    output_mp4: Path,
    fps: int = 24,
    max_duration_sec: float = 35.0,
    width: int = 1280,
    height: int = 720,
    style: str = "glass_studio",
    cover_intro_frames: int = 12,
) -> Path:
    """Render broadcast MP4 video with 4 rotating vertical models, Frame 0 master cover, and guaranteed karaoke subtitles."""
    is_vert = style in ("vertical_reel",) or style in VERTICAL_UI_MODELS or (height > width)
    if is_vert and width == 1280 and height == 720:
        width, height = 1080, 1920

    model_key = style if style in MODEL_THEMES else "model_1_cyber_nexus"
    theme = MODEL_THEMES[model_key]

    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    telemetry = analyze_stereo_stream(audio_path, fps=fps, max_duration_sec=max_duration_sec)
    actual_duration = len(telemetry) / float(fps)

    _ensure_scenario_captions(scenario, audio_path, actual_duration)

    col_a = theme["col_a"]
    col_a_sub = theme["col_a_sub"]
    col_b = theme["col_b"]
    col_b_sub = theme["col_b_sub"]
    col_overlap = theme["col_overlap"]

    base_bg = _create_model_background(width, height, model_key=model_key)
    logo_header = _load_ranuk_apple_logo(size=56 if is_vert else 38)
    logo_footer = _load_ranuk_apple_logo(size=38)

    # Master cover generation for Frame 0 & first 0.5s hook
    cover_raw_bytes: Optional[bytes] = None
    if is_vert and cover_intro_frames > 0:
        try:
            from .cover_generator import generate_debate_cover
            cover_tmp = output_mp4.parent / f"{output_mp4.stem}_master_cover.png"
            generate_debate_cover(
                title=scenario.title,
                speaker_a_name=scenario.speaker_a_name,
                speaker_a_role=scenario.speaker_a_role,
                speaker_b_name=scenario.speaker_b_name,
                speaker_b_role=scenario.speaker_b_role,
                day_num=1,
                output_path=cover_tmp,
                theme_key=model_key,
            )
            if cover_tmp.exists():
                with Image.open(cover_tmp) as c_im:
                    c_rgb = c_im.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
                    cover_raw_bytes = c_rgb.tobytes()
        except Exception as e:
            pass

    f_brand = _load_apple_font("keynote", size=24 if is_vert else 15)
    f_badge = _load_apple_font("rounded", size=17 if is_vert else 12)
    f_large_title = _load_apple_font("keynote", size=34 if is_vert else 31)
    f_sub = _load_apple_font("display", size=18 if is_vert else 15)
    f_speaker = _load_apple_font("keynote", size=27 if is_vert else 21)
    f_role = _load_apple_font("display", size=17 if is_vert else 13)
    f_sub_word = _load_apple_font("keynote", size=34 if is_vert else 20)
    f_prev = _load_apple_font("display", size=17 if is_vert else 12)
    f_status = _load_apple_font("mono", size=15 if is_vert else 11)
    f_footer = _load_apple_font("rounded", size=18 if is_vert else 12)

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
        cover_frames_count = cover_intro_frames if (is_vert and cover_raw_bytes is not None) else 0

        for frame_idx, frame in enumerate(telemetry):
            if frame_idx < cover_frames_count and cover_raw_bytes is not None:
                proc.stdin.write(cover_raw_bytes)
                continue

            t_sec = frame.timestamp_sec
            spk_code, spk_name, turn_tag, cap_text, prog, turn_idx, total_turns, prev_info = _active_caption_with_context(
                scenario, t_sec
            )

            # Combine raw audio gate with active turn state so the speaking AI is ALWAYS visually alive
            spk_a_on = frame.left_speaking or (spk_code == "A")
            spk_b_on = frame.right_speaking or (spk_code == "B")

            cur_l = _interpolate_bands(frame.left_bands, 24)
            cur_r = _interpolate_bands(frame.right_bands, 24)
            cur_l, boost_l_rms = _boost_active_bands(cur_l, spk_a_on, t_sec)
            cur_r, boost_r_rms = _boost_active_bands(cur_r, spk_b_on, t_sec)

            smooth_l_rms = 0.65 * max(frame.left_rms, boost_l_rms if spk_a_on else 0.0) + 0.35 * smooth_l_rms
            smooth_r_rms = 0.65 * max(frame.right_rms, boost_r_rms if spk_b_on else 0.0) + 0.35 * smooth_r_rms
            smooth_l_bands = 0.72 * cur_l + 0.28 * smooth_l_bands
            smooth_r_bands = 0.72 * cur_r + 0.28 * smooth_r_bands

            canvas = base_bg.copy()
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            active_col = col_a if spk_code == "A" else col_b
            use_chamfer = model_key in ("model_2_quantum_matrix", "model_3_silicon_warroom")

            if is_vert:
                _draw_ranuk_top_header_vertical(
                    overlay, draw, width, logo_header, theme, frame, f_brand, f_badge, chamfer=use_chamfer
                )
                _draw_topic_banner_vertical(draw, width, scenario, theme, f_large_title, f_sub)

                if model_key == "model_1_cyber_nexus":
                    # --- MODEL 1: Twin Vertical Cyber-Glass Pods + Central VS Conduit ---
                    pod_top, pod_bot = 362, 962
                    pw = 468
                    lx0 = 46
                    rx0 = width - 46 - pw

                    _draw_frosted_card(draw, (lx0, pod_top, lx0 + pw, pod_bot), radius=28, fill_rgb=theme["card_bg"], is_active=spk_a_on, active_color=col_a)
                    _draw_apple_siri_orb(draw, lx0 + pw // 2, pod_top + 92, 38, smooth_l_rms, spk_a_on, col_a, col_a_sub, t_sec, max_halo_radius=58)
                    _draw_wrapped_centered_text(draw, scenario.speaker_a_name, lx0 + pw // 2, pod_top + 165, 22, 1, f_speaker, (255, 255, 255, 255), 30)
                    _draw_wrapped_centered_text(draw, scenario.speaker_a_role, lx0 + pw // 2, pod_top + 202, 28, 2, f_role, (175, 190, 210, 230), 22)

                    draw.rounded_rectangle([lx0 + 115, pod_top + 258, lx0 + pw - 115, pod_top + 290], radius=16, fill=(*col_a, 35 if spk_a_on else 18), outline=(*col_a, 210 if spk_a_on else 90), width=1)
                    draw.text((lx0 + 142, pod_top + 266), "CH-01 • LEFT 24kHz", fill=(*col_a, 255), font=f_status)

                    _draw_apple_music_waveform(draw, lx0 + 36, pod_top + 435, 18, bar_width=15, bar_gap=7, bands=smooth_l_bands[:18], speaking=spk_a_on, color_top=col_a, color_bot=col_a_sub, max_height=105)

                    _draw_frosted_card(draw, (rx0, pod_top, rx0 + pw, pod_bot), radius=28, fill_rgb=theme["card_bg"], is_active=spk_b_on, active_color=col_b)
                    _draw_apple_siri_orb(draw, rx0 + pw // 2, pod_top + 92, 38, smooth_r_rms, spk_b_on, col_b, col_b_sub, t_sec, max_halo_radius=58)
                    _draw_wrapped_centered_text(draw, scenario.speaker_b_name, rx0 + pw // 2, pod_top + 165, 22, 1, f_speaker, (255, 255, 255, 255), 30)
                    _draw_wrapped_centered_text(draw, scenario.speaker_b_role, rx0 + pw // 2, pod_top + 202, 28, 2, f_role, (175, 190, 210, 230), 22)

                    draw.rounded_rectangle([rx0 + 115, pod_top + 258, rx0 + pw - 115, pod_top + 290], radius=16, fill=(*col_b, 35 if spk_b_on else 18), outline=(*col_b, 210 if spk_b_on else 90), width=1)
                    draw.text((rx0 + 138, pod_top + 266), "CH-02 • RIGHT 24kHz", fill=(*col_b, 255), font=f_status)

                    _draw_apple_music_waveform(draw, rx0 + 36, pod_top + 435, 18, bar_width=15, bar_gap=7, bands=smooth_r_bands[:18], speaking=spk_b_on, color_top=col_b, color_bot=col_b_sub, max_height=105)

                    cx_mid, cy_mid = width // 2, (pod_top + pod_bot) // 2
                    vs_col = col_overlap if frame.is_overlap else active_col
                    draw.ellipse([cx_mid - 32, cy_mid - 32, cx_mid + 32, cy_mid + 32], fill=(8, 14, 26, 245), outline=(*vs_col, 245), width=3)
                    draw.text((cx_mid - 16, cy_mid - 11), "VS", fill=(255, 255, 255, 255), font=f_brand)

                elif model_key == "model_2_quantum_matrix":
                    # --- MODEL 2: Stacked Wide Horizontal Command Decks (Violet vs Gold) ---
                    deck_a = (46, 362, width - 46, 646)
                    deck_b = (46, 678, width - 46, 962)

                    for d_rect, is_spk, rms_v, bands_v, s_name, s_role, c_main, c_sub, ch_lbl in [
                        (deck_a, spk_a_on, smooth_l_rms, smooth_l_bands, scenario.speaker_a_name, scenario.speaker_a_role, col_a, col_a_sub, "QUANTUM NODE A • 24kHz FL"),
                        (deck_b, spk_b_on, smooth_r_rms, smooth_r_bands, scenario.speaker_b_name, scenario.speaker_b_role, col_b, col_b_sub, "QUANTUM NODE B • 24kHz FR"),
                    ]:
                        dx0, dy0, dx1, dy1 = d_rect
                        _draw_frosted_card(draw, d_rect, fill_rgb=theme["card_bg"], is_active=is_spk, active_color=c_main, chamfer=True)
                        orb_cx, orb_cy = dx0 + 115, (dy0 + dy1) // 2
                        draw.ellipse([orb_cx - 68, orb_cy - 68, orb_cx + 68, orb_cy + 68], outline=(*c_main, 160 if is_spk else 50), width=2)
                        _draw_apple_siri_orb(draw, orb_cx, orb_cy, 40, rms_v, is_spk, c_main, c_sub, t_sec, max_halo_radius=62)

                        draw.text((dx0 + 210, dy0 + 24), s_name.upper(), fill=(255, 255, 255, 255), font=f_speaker)
                        draw.text((dx0 + 210, dy0 + 60), s_role[:56], fill=(195, 205, 225, 235), font=f_role)

                        draw.rounded_rectangle([dx1 - 285, dy0 + 22, dx1 - 28, dy0 + 56], radius=12, fill=(*c_main, 38 if is_spk else 18), outline=(*c_main, 215 if is_spk else 90), width=1)
                        draw.text((dx1 - 268, dy0 + 31), ch_lbl, fill=(*c_main, 255), font=f_status)

                        _draw_apple_music_waveform(
                            draw,
                            dx0 + 210,
                            dy0 + 188,
                            24,
                            bar_width=21,
                            bar_gap=10,
                            bands=bands_v,
                            speaking=is_spk,
                            color_top=c_main,
                            color_bot=c_sub,
                            max_height=68,
                            reflection=False,
                        )

                elif model_key == "model_3_silicon_warroom":
                    # --- MODEL 3: Silicon Valley War Room (Tactical Cards + Acoustic Clash Spine) ---
                    top_y0, top_y1 = 362, 710
                    pw = 468
                    lx0, rx0 = 46, width - 46 - pw

                    _draw_frosted_card(draw, (lx0, top_y0, lx0 + pw, top_y1), fill_rgb=theme["card_bg"], is_active=spk_a_on, active_color=col_a, chamfer=True)
                    draw.rectangle([lx0 + 24, top_y0 + 16, lx0 + pw - 24, top_y0 + 22], fill=(*col_a, 240 if spk_a_on else 75))
                    _draw_apple_siri_orb(draw, lx0 + pw // 2, top_y0 + 102, 38, smooth_l_rms, spk_a_on, col_a, col_a_sub, t_sec, max_halo_radius=56)
                    _draw_wrapped_centered_text(draw, scenario.speaker_a_name.upper(), lx0 + pw // 2, top_y0 + 178, 22, 1, f_speaker, (255, 255, 255, 255), 30)
                    _draw_wrapped_centered_text(draw, scenario.speaker_a_role, lx0 + pw // 2, top_y0 + 216, 28, 2, f_role, (200, 210, 225, 230), 22)
                    db_a = -48.0 if smooth_l_rms < 0.01 else max(-32.0, 20.0 * math.log10(smooth_l_rms))
                    draw.text((lx0 + pw // 2 - 90, top_y0 + 286), f"RMS: {db_a:05.1f} dB • CH-L", fill=(*col_a, 245), font=f_status)

                    _draw_frosted_card(draw, (rx0, top_y0, rx0 + pw, top_y1), fill_rgb=theme["card_bg"], is_active=spk_b_on, active_color=col_b, chamfer=True)
                    draw.rectangle([rx0 + 24, top_y0 + 16, rx0 + pw - 24, top_y0 + 22], fill=(*col_b, 240 if spk_b_on else 75))
                    _draw_apple_siri_orb(draw, rx0 + pw // 2, top_y0 + 102, 38, smooth_r_rms, spk_b_on, col_b, col_b_sub, t_sec, max_halo_radius=56)
                    _draw_wrapped_centered_text(draw, scenario.speaker_b_name.upper(), rx0 + pw // 2, top_y0 + 178, 22, 1, f_speaker, (255, 255, 255, 255), 30)
                    _draw_wrapped_centered_text(draw, scenario.speaker_b_role, rx0 + pw // 2, top_y0 + 216, 28, 2, f_role, (200, 210, 225, 230), 22)
                    db_b = -48.0 if smooth_r_rms < 0.01 else max(-32.0, 20.0 * math.log10(smooth_r_rms))
                    draw.text((rx0 + pw // 2 - 90, top_y0 + 286), f"RMS: {db_b:05.1f} dB • CH-R", fill=(*col_b, 245), font=f_status)

                    clash_rect = (46, 734, width - 46, 962)
                    _draw_frosted_card(draw, clash_rect, fill_rgb=theme["card_bg"], is_active=True, active_color=col_overlap if frame.is_overlap else active_col, chamfer=True)
                    draw.text((78, 752), "REAL-TIME ACOUSTIC CLASH SPECTRUM (24kHz FULL-DUPLEX)", fill=(225, 235, 250, 240), font=f_status)
                    draw.text((width - 310, 752), f"OVERLAPS: {frame.cumulative_overlaps:02d}  •  180ms", fill=(*col_overlap, 245), font=f_status)

                    _draw_apple_music_waveform(draw, 82, 868, 16, bar_width=18, bar_gap=8, bands=smooth_l_bands[:16], speaking=spk_a_on, color_top=col_a, color_bot=col_a_sub, max_height=68, reflection=False)
                    _draw_apple_music_waveform(draw, width // 2 + 28, 868, 16, bar_width=18, bar_gap=8, bands=smooth_r_bands[:16], speaking=spk_b_on, color_top=col_b, color_bot=col_b_sub, max_height=68, reflection=False)
                    draw.line([(width // 2, 785), (width // 2, 942)], fill=(255, 255, 255, 110), width=2)

                else:
                    # --- MODEL 4: Blackwell Tensor Studio (360° Radial Halos + LED VU Telemetry) ---
                    top_y0, top_y1 = 362, 775
                    pw = 468
                    lx0, rx0 = 46, width - 46 - pw

                    _draw_frosted_card(draw, (lx0, top_y0, lx0 + pw, top_y1), radius=30, fill_rgb=theme["card_bg"], is_active=spk_a_on, active_color=col_a)
                    _draw_radial_halo_visualizer(draw, lx0 + pw // 2, top_y0 + 138, 52, smooth_l_bands, smooth_l_rms, spk_a_on, col_a, col_a_sub, t_sec)
                    _draw_wrapped_centered_text(draw, scenario.speaker_a_name, lx0 + pw // 2, top_y0 + 262, 22, 1, f_speaker, (255, 255, 255, 255), 30)
                    _draw_wrapped_centered_text(draw, scenario.speaker_a_role, lx0 + pw // 2, top_y0 + 300, 28, 2, f_role, (185, 215, 195, 235), 22)
                    draw.text((lx0 + pw // 2 - 88, top_y0 + 364), "● TENSOR STREAM [FL]", fill=(*col_a, 245), font=f_status)

                    _draw_frosted_card(draw, (rx0, top_y0, rx0 + pw, top_y1), radius=30, fill_rgb=theme["card_bg"], is_active=spk_b_on, active_color=col_b)
                    _draw_radial_halo_visualizer(draw, rx0 + pw // 2, top_y0 + 138, 52, smooth_r_bands, smooth_r_rms, spk_b_on, col_b, col_b_sub, t_sec)
                    _draw_wrapped_centered_text(draw, scenario.speaker_b_name, rx0 + pw // 2, top_y0 + 262, 22, 1, f_speaker, (255, 255, 255, 255), 30)
                    _draw_wrapped_centered_text(draw, scenario.speaker_b_role, rx0 + pw // 2, top_y0 + 300, 28, 2, f_role, (185, 215, 225, 235), 22)
                    draw.text((rx0 + pw // 2 - 88, top_y0 + 364), "● TENSOR STREAM [FR]", fill=(*col_b, 245), font=f_status)

                    vu_rect = (46, 798, width - 46, 962)
                    _draw_frosted_card(draw, vu_rect, radius=24, fill_rgb=theme["card_bg"], is_active=True, active_color=active_col)
                    draw.text((78, 816), "NVIDIA PERSONAPLEX 7B  •  DUAL-CHANNEL TENSOR TELEMETRY", fill=(220, 245, 230, 240), font=f_status)

                    for row_idx, (lbl, rms_val, c_bar, spk_on) in enumerate([
                        ("CH-A [L]", smooth_l_rms, col_a, spk_a_on),
                        ("CH-B [R]", smooth_r_rms, col_b, spk_b_on),
                    ]):
                        ry = 856 + row_idx * 44
                        draw.text((78, ry + 4), lbl, fill=(*c_bar, 255), font=f_status)
                        num_segs = 28
                        active_segs = int(min(0.95, rms_val * 2.1 + (0.28 if spk_on else 0.04)) * num_segs)
                        for s_i in range(num_segs):
                            sx = 195 + s_i * 29
                            seg_col = col_overlap if s_i > 22 else c_bar
                            alpha = 245 if s_i < active_segs else 38
                            draw.rounded_rectangle([sx, ry, sx + 22, ry + 26], radius=5, fill=(*seg_col, alpha))

                _draw_subtitle_stage_vertical(
                    overlay=overlay,
                    draw=draw,
                    width=width,
                    theme=theme,
                    spk_code=spk_code,
                    spk_name=spk_name,
                    turn_tag=turn_tag,
                    cap_text=cap_text,
                    prog=prog,
                    turn_idx=turn_idx,
                    total_turns=total_turns,
                    prev_info=prev_info,
                    t_sec=t_sec,
                    logo_small=logo_footer,
                    f_pill=f_badge,
                    f_sub_word=f_sub_word,
                    f_prev=f_prev,
                    f_footer=f_footer,
                    chamfer=use_chamfer,
                )

            else:
                island_w, island_h = 580, 48
                ix0 = (width - island_w) // 2
                iy0 = 22
                draw.rounded_rectangle([ix0, iy0, ix0 + island_w, iy0 + island_h], radius=24, fill=(8, 12, 20, 235), outline=(255, 255, 255, 38), width=1)
                if logo_header:
                    overlay.paste(logo_header, (ix0 + 12, iy0 + 5), logo_header)
                draw.text((ix0 + 58, iy0 + 15), "RANUK IT SOLUTIONS  •  AI DEBATE STUDIO", fill=(255, 255, 255, 245), font=f_badge)

                draw.text((54, 88), scenario.title, fill=(255, 255, 255, 255), font=f_large_title)
                draw.text((54, 126), scenario.subtitle, fill=(156, 163, 175, 235), font=f_sub)

                card_y0, card_y1 = 168, 516
                card_w = 566
                card_a = (54, card_y0, 54 + card_w, card_y1)
                _draw_frosted_card(draw, card_a, radius=28, is_active=spk_a_on, active_color=col_a)
                _draw_apple_siri_orb(draw, 114, 232, 28, smooth_l_rms, spk_a_on, col_a, col_a_sub, t_sec, max_halo_radius=44)
                draw.text((166, 212), scenario.speaker_a_name, fill=(255, 255, 255, 255), font=f_speaker)
                draw.text((166, 242), scenario.speaker_a_role, fill=(156, 163, 175, 220), font=f_role)
                _draw_apple_music_waveform(draw, 84, 408, 24, bar_width=12, bar_gap=8, bands=smooth_l_bands, speaking=spk_a_on, color_top=col_a, color_bot=col_a_sub, max_height=65)

                card_b = (width - 54 - card_w, card_y0, width - 54, card_y1)
                _draw_frosted_card(draw, card_b, radius=28, is_active=spk_b_on, active_color=col_b)
                _draw_apple_siri_orb(draw, width - 54 - card_w + 60, 232, 28, smooth_r_rms, spk_b_on, col_b, col_b_sub, t_sec, max_halo_radius=44)
                draw.text((width - 54 - card_w + 112, 212), scenario.speaker_b_name, fill=(255, 255, 255, 255), font=f_speaker)
                draw.text((width - 54 - card_w + 112, 242), scenario.speaker_b_role, fill=(156, 163, 175, 220), font=f_role)
                _draw_apple_music_waveform(draw, width - 54 - card_w + 30, 408, 24, bar_width=12, bar_gap=8, bands=smooth_r_bands, speaking=spk_b_on, color_top=col_b, color_bot=col_b_sub, max_height=65)

                sub_rect = (54, 538, width - 54, 692)
                _draw_frosted_card(draw, sub_rect, radius=24, is_active=True, active_color=active_col)
                draw.text((84, 558), f"{spk_name.upper()}  •  {turn_tag}", fill=(*active_col, 245), font=f_badge)
                wrapped = textwrap.wrap(f"“{cap_text}”", width=78)[:2]
                cy_t = 598
                for ln in wrapped:
                    draw.text((84, cy_t), ln, fill=(255, 255, 255, 255), font=f_sub_word)
                    cy_t += 30

            final_rgb = Image.alpha_composite(canvas, overlay).convert("RGB")
            proc.stdin.write(final_rgb.tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=90)

    if proc.returncode != 0 or not output_mp4.exists():
        raise RuntimeError(f"FFmpeg video rendering failed with code {proc.returncode}")
    return output_mp4
