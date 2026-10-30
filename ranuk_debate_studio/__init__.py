# © 2026 Ranuk IT Solutions — ranuk.dev
"""
Ranuk AI Debate Studio — Full-Duplex Multi-Agent Debate & Video Studio powered by NVIDIA PersonaPlex 7B.
"""
from .personaplex_duo import (
    ALL_PERSONAPLEX_VOICES,
    NATURAL_FEMALE_VOICES,
    NATURAL_MALE_VOICES,
    VARIETY_FEMALE_VOICES,
    VARIETY_MALE_VOICES,
    PRESET_SCENARIOS,
    DebateScenario,
    build_offline_command,
    validate_voice_prompt,
    wrap_system_prompt,
)
from .video_renderer import render_debate_video
from .waveform_analyzer import FrameAudioTelemetry, analyze_stereo_stream, compute_16_bands

__version__ = "0.1.0"
__all__ = [
    "ALL_PERSONAPLEX_VOICES",
    "NATURAL_FEMALE_VOICES",
    "NATURAL_MALE_VOICES",
    "VARIETY_FEMALE_VOICES",
    "VARIETY_MALE_VOICES",
    "PRESET_SCENARIOS",
    "DebateScenario",
    "build_offline_command",
    "validate_voice_prompt",
    "wrap_system_prompt",
    "render_debate_video",
    "FrameAudioTelemetry",
    "analyze_stereo_stream",
    "compute_16_bands",
]
