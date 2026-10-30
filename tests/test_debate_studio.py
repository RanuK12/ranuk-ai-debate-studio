# © 2026 Ranuk IT Solutions — ranuk.dev
"""Unit test suite for Ranuk AI Debate Studio (NVIDIA PersonaPlex 7B)."""
from pathlib import Path
import numpy as np
import pytest

from ranuk_debate_studio import (
    ALL_PERSONAPLEX_VOICES,
    PRESET_SCENARIOS,
    analyze_stereo_stream,
    build_offline_command,
    compute_16_bands,
    validate_voice_prompt,
    wrap_system_prompt,
)


def test_wrap_system_prompt():
    raw = "You are a wise and friendly teacher."
    wrapped = wrap_system_prompt(raw)
    assert wrapped == "<system> You are a wise and friendly teacher. <system>"
    assert wrap_system_prompt(wrapped) == wrapped


def test_validate_voice_prompt_all_18():
    assert len(ALL_PERSONAPLEX_VOICES) == 18
    assert validate_voice_prompt("NATF2") == "NATF2.pt"
    assert validate_voice_prompt("VARM0.pt") == "VARM0.pt"
    with pytest.raises(ValueError):
        validate_voice_prompt("INVALID_VOICE")


def test_preset_scenarios():
    assert "interruption_benchmark" in PRESET_SCENARIOS
    assert "backchannel_debate" in PRESET_SCENARIOS
    assert "banking_b2b_closer" in PRESET_SCENARIOS
    assert "mars_reactor_crisis" in PRESET_SCENARIOS
    for sc in PRESET_SCENARIOS.values():
        assert sc.wrapped_prompt.startswith("<system>")
        assert sc.voice_prompt in ALL_PERSONAPLEX_VOICES


def test_build_offline_command(tmp_path):
    in_wav = tmp_path / "in.wav"
    out_wav = tmp_path / "out.wav"
    cmd = build_offline_command(in_wav, out_wav, voice_prompt="NATM1", text_prompt="You enjoy having a good conversation.")
    assert "-m" in cmd and "moshi.offline" in cmd
    assert "NATM1.pt" in cmd
    assert "<system> You enjoy having a good conversation. <system>" in cmd


def test_compute_16_bands():
    t = np.linspace(0, 0.1, 2400, dtype=np.float32)
    sine = 0.5 * np.sin(2 * np.pi * 440 * t)
    bands = compute_16_bands(sine)
    assert len(bands) == 16
    assert all(0.05 <= b <= 1.0 for b in bands)


def test_analyze_stereo_stream_on_sample():
    sample = Path(__file__).resolve().parent.parent / "assets" / "samples" / "assistant.mp3"
    if sample.exists():
        frames = analyze_stereo_stream(sample, fps=10, max_duration_sec=5.0)
        assert len(frames) >= 40
        assert any(f.left_speaking or f.right_speaking for f in frames)
