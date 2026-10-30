# © 2026 Ranuk IT Solutions — ranuk.dev
"""
video_renderer.py — Studio-grade Full-Duplex Debate & Interaction Video Renderer.

Renders 1280x720 HD H.264 MP4 videos synchronized to NVIDIA PersonaPlex stereo streams,
displaying dual 16-band spectrum equalizers, real-time full-duplex overlap detection,
speaker status rings, and <system> persona prompt telemetry.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from .personaplex_duo import DebateScenario, PRESET_SCENARIOS
from .waveform_analyzer import FrameAudioTelemetry, analyze_stereo_stream, find_ffmpeg


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        if bold
        else [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    )
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def _caption_for_time(scenario: DebateScenario, t_sec: float) -> str:
    for cap in scenario.captions:
        if float(cap["start"]) <= t_sec <= float(cap["end"]):
            return str(cap["text"])
    if scenario.captions:
        return str(scenario.captions[-1]["text"])
    return "Full-Duplex Speech-to-Speech Stream Active (NVIDIA PersonaPlex 7B)"


def render_debate_video(
    scenario: DebateScenario,
    audio_path: Path,
    output_mp4: Path,
    fps: int = 24,
    max_duration_sec: float = 24.0,
    width: int = 1280,
    height: int = 720,
) -> Path:
    """Render an HD MP4 video synchronized with the stereo PersonaPlex audio file."""
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    telemetry = analyze_stereo_stream(audio_path, fps=fps, max_duration_sec=max_duration_sec)
    actual_duration = len(telemetry) / float(fps)

    font_brand = _load_font(18, bold=True)
    font_title = _load_font(30, bold=True)
    font_sub = _load_font(17, bold=False)
    font_speaker = _load_font(22, bold=True)
    font_role = _load_font(15, bold=False)
    font_badge = _load_font(15, bold=True)
    font_caption = _load_font(18, bold=True)
    font_prompt = _load_font(13, bold=False)

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
        "21",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-movflags",
        "+faststart",
        str(output_mp4),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None

    try:
        for frame in telemetry:
            img = Image.new("RGB", (width, height), (9, 13, 24))
            draw = ImageDraw.Draw(img)

            # Top Header Bar
            draw.rectangle([0, 0, width, 64], fill=(15, 23, 42))
            draw.line([0, 64, width, 64], fill=(45, 65, 95), width=2)
            draw.text((36, 20), "< R /> RANUK IT SOLUTIONS  ×  NVIDIA PERSONAPLEX 7B", fill=(100, 255, 218), font=font_brand)
            draw.text(
                (width - 410, 22),
                f"VOICE: {scenario.voice_prompt}  |  CODEC: MIMI 24kHz",
                fill=(148, 163, 184),
                font=font_badge,
            )

            # Title & Subtitle
            draw.text((40, 82), scenario.title, fill=(248, 250, 252), font=font_title)
            draw.text((40, 122), scenario.subtitle, fill=(148, 163, 184), font=font_sub)

            # Center Full-Duplex Overlap Indicator Badge
            if frame.is_overlap:
                draw.rounded_rectangle([410, 160, 870, 208], radius=10, fill=(124, 45, 18), outline=(249, 115, 22), width=3)
                draw.text(
                    (442, 175),
                    "[LIVE] FULL-DUPLEX OVERLAP / BACKCHANNEL ACTIVE",
                    fill=(254, 215, 170),
                    font=font_badge,
                )
            else:
                draw.rounded_rectangle([430, 160, 850, 208], radius=10, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
                draw.text(
                    (468, 175),
                    f"FULL-DUPLEX MONITOR  •  OVERLAPS: {frame.cumulative_overlaps}",
                    fill=(148, 163, 184),
                    font=font_badge,
                )

            # Left Speaker Card (Speaker A — Interlocutor)
            l_border = (100, 255, 218) if frame.left_speaking else (51, 65, 85)
            draw.rounded_rectangle([40, 225, 610, 540], radius=16, fill=(15, 23, 42), outline=l_border, width=3 if frame.left_speaking else 1)
            # Pulsing Avatar Circle Left
            l_radius = int(34 + frame.left_rms * 14)
            draw.ellipse([95 - l_radius, 285 - l_radius, 95 + l_radius, 285 + l_radius], fill=(13, 68, 72) if frame.left_speaking else (30, 41, 59), outline=(100, 255, 218), width=2)
            draw.text((86, 274), "A", fill=(100, 255, 218), font=font_speaker)
            draw.text((150, 255), scenario.speaker_a_name, fill=(248, 250, 252), font=font_speaker)
            draw.text((150, 285), scenario.speaker_a_role, fill=(148, 163, 184), font=font_role)

            l_status_txt = "● SPEAKING (LEFT CH)" if frame.left_speaking else "○ LISTENING"
            l_status_col = (100, 255, 218) if frame.left_speaking else (100, 116, 139)
            draw.text((150, 312), l_status_txt, fill=l_status_col, font=font_badge)

            # Left 16-Band Spectrum Bars
            bar_base_y = 510
            for b_idx, val in enumerate(frame.left_bands):
                bx = 75 + b_idx * 31
                bh = int(12 + val * 145)
                b_col = (100, 255, 218) if frame.left_speaking else (51, 65, 85)
                draw.rounded_rectangle([bx, bar_base_y - bh, bx + 20, bar_base_y], radius=4, fill=b_col)

            # Right Speaker Card (Speaker B — NVIDIA PersonaPlex 7B)
            r_border = (124, 208, 0) if frame.right_speaking else (51, 65, 85)
            draw.rounded_rectangle([670, 225, 1240, 540], radius=16, fill=(15, 23, 42), outline=r_border, width=3 if frame.right_speaking else 1)
            r_radius = int(34 + frame.right_rms * 14)
            draw.ellipse([725 - r_radius, 285 - r_radius, 725 + r_radius, 285 + r_radius], fill=(38, 70, 18) if frame.right_speaking else (30, 41, 59), outline=(124, 208, 0), width=2)
            draw.text((716, 274), "AI", fill=(163, 230, 53), font=font_speaker)
            draw.text((780, 255), scenario.speaker_b_name, fill=(248, 250, 252), font=font_speaker)
            draw.text((780, 285), scenario.speaker_b_role, fill=(148, 163, 184), font=font_role)

            r_status_txt = "● PERSONAPLEX ACTIVE (RIGHT CH)" if frame.right_speaking else "○ FULL-DUPLEX LISTENING"
            r_status_col = (163, 230, 53) if frame.right_speaking else (100, 116, 139)
            draw.text((780, 312), r_status_txt, fill=r_status_col, font=font_badge)

            # Right 16-Band Spectrum Bars
            for b_idx, val in enumerate(frame.right_bands):
                bx = 705 + b_idx * 31
                bh = int(12 + val * 145)
                b_col = (163, 230, 53) if frame.right_speaking else (51, 65, 85)
                draw.rounded_rectangle([bx, bar_base_y - bh, bx + 20, bar_base_y], radius=4, fill=b_col)

            # Bottom Telemetry & Live Caption Panel
            draw.rounded_rectangle([40, 560, 1240, 690], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
            cap_text = _caption_for_time(scenario, frame.timestamp_sec)
            draw.text((65, 578), f"LIVE STREAM  |  t = {frame.timestamp_sec:05.2f}s  |  {cap_text}", fill=(248, 250, 252), font=font_caption)

            prompt_preview = scenario.wrapped_prompt
            if len(prompt_preview) > 125:
                prompt_preview = prompt_preview[:122] + "..."
            draw.text((65, 618), f"PROMPT: {prompt_preview}", fill=(100, 255, 218), font=font_prompt)
            draw.text(
                (65, 648),
                "ranuk.dev  •  github.com/RanuK12/ranuk-ai-debate-studio  •  Powered by NVIDIA PersonaPlex 7B (Moshi)",
                fill=(148, 163, 184),
                font=font_prompt,
            )

            proc.stdin.write(img.tobytes())
    finally:
        proc.stdin.close()
        proc.wait(timeout=60)

    if proc.returncode != 0 or not output_mp4.exists():
        raise RuntimeError(f"FFmpeg video rendering failed with code {proc.returncode}")
    return output_mp4
