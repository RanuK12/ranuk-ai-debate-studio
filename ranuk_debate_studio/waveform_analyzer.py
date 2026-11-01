# © 2026 Ranuk IT Solutions — ranuk.dev
"""
waveform_analyzer.py — Stereo Full-Duplex Audio Telemetry & Spectrum Analyzer.

Extracts isolated Left Channel (Speaker A) and Right Channel (Speaker B / PersonaPlex 7B)
waveforms, computes 16-band FFT spectrums per video frame, and detects simultaneous
full-duplex speech overlaps (interruptions and backchanneling).
"""
from __future__ import annotations

import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class FrameAudioTelemetry:
    frame_idx: int
    timestamp_sec: float
    left_rms: float
    right_rms: float
    left_bands: List[float]
    right_bands: List[float]
    left_speaking: bool
    right_speaking: bool
    is_overlap: bool
    cumulative_overlaps: int


def find_ffmpeg() -> str:
    for candidate in ["/Users/emilioranucoli/.local/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if Path(candidate).exists():
            return candidate
    return shutil.which("ffmpeg") or "ffmpeg"


def decode_stereo_pcm(audio_path: Path, sample_rate: int = 24000, max_duration_sec: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray, int]:
    """Decode any audio file (.mp3, .wav, .ogg) into stereo float32 arrays (left, right)."""
    p = Path(audio_path)
    if not p.exists():
        raise FileNotFoundError(f"PCM decode target audio does not exist: {p.resolve()}")
    if p.stat().st_size == 0:
        raise ValueError(f"PCM decode target audio is empty (0 bytes): {p.resolve()}")
    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(audio_path),
    ]
    if max_duration_sec is not None:
        cmd.extend(["-t", f"{max_duration_sec:.2f}"])
    cmd.extend([
        "-f",
        "s16le",
        "-ac",
        "2",
        "-ar",
        str(sample_rate),
        "pipe:1",
    ])
    raw = subprocess.check_output(cmd, timeout=30)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if len(samples) % 2 != 0:
        samples = samples[:-1]
    stereo = samples.reshape(-1, 2)
    return stereo[:, 0], stereo[:, 1], sample_rate


def compute_16_bands(chunk: np.ndarray) -> List[float]:
    """Compute 16 normalized frequency band magnitudes (0.0 to 1.0) from an audio chunk."""
    if len(chunk) < 32:
        return [0.05] * 16
    windowed = chunk * np.hanning(len(chunk))
    fft_mag = np.abs(np.fft.rfft(windowed))
    # Split spectrum into 16 perceptual bands
    usable = fft_mag[1 : min(len(fft_mag), 256)]
    if len(usable) < 16:
        return [0.05] * 16
    splits = np.array_split(usable, 16)
    bands = []
    for s in splits:
        val = float(np.mean(s)) * 0.45
        bands.append(min(1.0, max(0.05, val)))
    return bands


def analyze_stereo_stream(
    audio_path: Path,
    fps: int = 24,
    sample_rate: int = 24000,
    max_duration_sec: Optional[float] = 28.0,
    speaking_threshold: float = 0.018,
) -> List[FrameAudioTelemetry]:
    """Analyze a stereo PersonaPlex conversation and return per-frame telemetry."""
    left, right, sr = decode_stereo_pcm(audio_path, sample_rate=sample_rate, max_duration_sec=max_duration_sec)
    samples_per_frame = max(1, int(sr / fps))
    total_frames = max(1, len(left) // samples_per_frame)

    frames: List[FrameAudioTelemetry] = []
    cumulative_overlaps = 0
    in_overlap_event = False
    overlap_hold_frames = 0

    for idx in range(total_frames):
        start = idx * samples_per_frame
        end = start + samples_per_frame
        l_chunk = left[start:end]
        r_chunk = right[start:end]

        l_rms = float(np.sqrt(np.mean(l_chunk ** 2))) if len(l_chunk) > 0 else 0.0
        r_rms = float(np.sqrt(np.mean(r_chunk ** 2))) if len(r_chunk) > 0 else 0.0

        l_speak = l_rms >= speaking_threshold
        r_speak = r_rms >= speaking_threshold
        raw_overlap = l_speak and r_speak

        if raw_overlap:
            if not in_overlap_event:
                cumulative_overlaps += 1
                in_overlap_event = True
            overlap_hold_frames = 6  # Keep badge lit for 250ms so human eye sees it clearly
        else:
            if overlap_hold_frames > 0:
                overlap_hold_frames -= 1
            else:
                in_overlap_event = False

        frames.append(
            FrameAudioTelemetry(
                frame_idx=idx,
                timestamp_sec=round(idx / fps, 3),
                left_rms=min(1.0, l_rms * 6.5),
                right_rms=min(1.0, r_rms * 6.5),
                left_bands=compute_16_bands(l_chunk),
                right_bands=compute_16_bands(r_chunk),
                left_speaking=l_speak,
                right_speaking=r_speak,
                is_overlap=(raw_overlap or overlap_hold_frames > 0),
                cumulative_overlaps=cumulative_overlaps,
            )
        )

    return frames
