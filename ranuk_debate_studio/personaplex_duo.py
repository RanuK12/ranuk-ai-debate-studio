# © 2026 Ranuk IT Solutions — ranuk.dev
"""
personaplex_duo.py — Dual-Agent & Full-Duplex Orchestrator for NVIDIA PersonaPlex (7B).

Supports all 18 official NVIDIA PersonaPlex voice embeddings (NATF0-3, NATM0-3,
VARF0-4, VARM0-4), <system> role conditioning, and stereo full-duplex stream orchestration.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

PERSONAPLEX_REPO = Path.home() / "Apps" / "personaplex"

NATURAL_FEMALE_VOICES = ("NATF0.pt", "NATF1.pt", "NATF2.pt", "NATF3.pt")
NATURAL_MALE_VOICES = ("NATM0.pt", "NATM1.pt", "NATM2.pt", "NATM3.pt")
VARIETY_FEMALE_VOICES = ("VARF0.pt", "VARF1.pt", "VARF2.pt", "VARF3.pt", "VARF4.pt")
VARIETY_MALE_VOICES = ("VARM0.pt", "VARM1.pt", "VARM2.pt", "VARM3.pt", "VARM4.pt")

ALL_PERSONAPLEX_VOICES = (
    NATURAL_FEMALE_VOICES
    + NATURAL_MALE_VOICES
    + VARIETY_FEMALE_VOICES
    + VARIETY_MALE_VOICES
)


def wrap_system_prompt(text: str) -> str:
    """Wrap role instructions in PersonaPlex's expected <system> ... <system> tags."""
    cleaned = text.strip()
    if cleaned.startswith("<system>") and cleaned.endswith("<system>"):
        return cleaned
    return f"<system> {cleaned} <system>"


def validate_voice_prompt(voice: str) -> str:
    """Ensure the voice embedding filename ends with .pt and belongs to the 18 PersonaPlex voices."""
    v = voice.strip()
    if not v.endswith(".pt"):
        v = f"{v}.pt"
    if v not in ALL_PERSONAPLEX_VOICES:
        raise ValueError(f"Unsupported PersonaPlex voice '{voice}'. Must be one of {ALL_PERSONAPLEX_VOICES}")
    return v


@dataclass
class DebateScenario:
    slug: str
    title: str
    subtitle: str
    speaker_a_name: str
    speaker_a_role: str
    speaker_b_name: str
    speaker_b_role: str
    voice_prompt: str
    system_prompt: str
    sample_audio: str
    captions: List[Dict[str, object]] = field(default_factory=list)

    @property
    def wrapped_prompt(self) -> str:
        return wrap_system_prompt(self.system_prompt)


PRESET_SCENARIOS: Dict[str, DebateScenario] = {
    "interruption_benchmark": DebateScenario(
        slug="interruption_benchmark",
        title="Full-Duplex Interruption & Turn-Taking",
        subtitle="NVIDIA PersonaPlex 7B • Live User Interruption Benchmark",
        speaker_a_name="Human Interlocutor",
        speaker_a_role="Live Caller (Interrupting Mid-Sentence)",
        speaker_b_name="PersonaPlex 7B (NATF2)",
        speaker_b_role="Full-Duplex AI Teacher & Advisor",
        voice_prompt="NATF2.pt",
        system_prompt="You are a wise and friendly teacher. Answer questions or provide advice in a clear and engaging way.",
        sample_audio="assistant.mp3",
        captions=[
            {"start": 0.0, "end": 4.5, "text": "[Caller asks question -> PersonaPlex responds with <200ms latency]"},
            {"start": 4.5, "end": 9.5, "text": "[Caller interrupts mid-sentence -> PersonaPlex yields floor immediately]"},
            {"start": 9.5, "end": 16.0, "text": "[Seamless context switch & natural conversational cadence]"},
        ],
    ),
    "backchannel_debate": DebateScenario(
        slug="backchannel_debate",
        title="Natural Backchanneling & Active Listening",
        subtitle="Simultaneous Listening + Speaking ('uh-huh', 'yeah', 'right')",
        speaker_a_name="Speaker A (Caller)",
        speaker_a_role="Storyteller / Debate Partner",
        speaker_b_name="PersonaPlex 7B (NATM1)",
        speaker_b_role="Active Listener with Contextual Backchannels",
        voice_prompt="NATM1.pt",
        system_prompt="You enjoy having a good conversation.",
        sample_audio="backchannel.mp3",
        captions=[
            {"start": 0.0, "end": 5.0, "text": "[Speaker A narrates -> PersonaPlex listens on Left Channel while vocalizing on Right]"},
            {"start": 5.0, "end": 11.0, "text": "[Contextual backchannels: 'oh okay', 'yeah', 'right' without breaking speaker flow]"},
            {"start": 11.0, "end": 20.0, "text": "[Full-Duplex organic turn transition when Speaker A pauses]"},
        ],
    ),
    "banking_b2b_closer": DebateScenario(
        slug="banking_b2b_closer",
        title="B2B Enterprise Voice Closer & Fraud Desk",
        subtitle="Strict Instruction Adherence, Empathy & Accent Control",
        speaker_a_name="Bank Customer",
        speaker_a_role="Cardholder ($1,200 Declined Transaction in Miami)",
        speaker_b_name="Sanni Virtanen (VARF1)",
        speaker_b_role="First Neuron Bank • AI Security Specialist",
        voice_prompt="VARF1.pt",
        system_prompt=(
            "You work for First Neuron Bank which is a bank and your name is Sanni Virtanen. "
            "Information: The customer's transaction for $1,200 at Home Depot was declined. "
            "Verify customer identity. The transaction was flagged due to an unusual location "
            "(transaction attempted in Miami, FL; customer normally transacts in Seattle, WA)."
        ),
        sample_audio="bank.mp3",
        captions=[
            {"start": 0.0, "end": 8.0, "text": "[Customer calls about declined $1,200 Home Depot charge -> Instant identity verification]"},
            {"start": 8.0, "end": 18.0, "text": "[PersonaPlex explains Miami vs. Seattle anomaly with natural empathy & zero pause]"},
            {"start": 18.0, "end": 35.0, "text": "[Real-time objection handling & security clearance in full-duplex audio]"},
        ],
    ),
    "mars_reactor_crisis": DebateScenario(
        slug="mars_reactor_crisis",
        title="High-Stress Sci-Fi Debate: Mars Reactor Meltdown",
        subtitle="Out-of-Distribution Roleplay & Emotional Urgency Control",
        speaker_a_name="Mission Control Engineer",
        speaker_a_role="Ground Support Specialist",
        speaker_b_name="Astronaut Alex (VARM0)",
        speaker_b_role="Mars Vessel Commander • Reactor Core Emergency",
        voice_prompt="VARM0.pt",
        system_prompt=(
            "You enjoy having a good conversation. Have a technical discussion about fixing a reactor core "
            "on a spaceship to Mars. You are an astronaut on a Mars mission. Your name is Alex. "
            "You are already dealing with a reactor core meltdown on a Mars mission."
        ),
        sample_audio="astronaut.mp3",
        captions=[
            {"start": 0.0, "end": 10.0, "text": "[Astronaut Alex reports critical reactor coolant failure with real vocal urgency]"},
            {"start": 10.0, "end": 22.0, "text": "[Rapid-fire technical troubleshooting & overlapping crisis backchanneling]"},
            {"start": 22.0, "end": 35.0, "text": "[Sustained persona coherence under continuous interruptions]"},
        ],
    ),
}


def build_offline_command(
    input_wav: Path,
    output_wav: Path,
    voice_prompt: str = "NATF2.pt",
    text_prompt: Optional[str] = None,
    seed: int = 42424242,
    cpu_offload: bool = True,
) -> List[str]:
    """Construct the CLI command to invoke NVIDIA PersonaPlex (`python -m moshi.offline`)."""
    vp = validate_voice_prompt(voice_prompt)
    cmd = [
        sys.executable,
        "-m",
        "moshi.offline",
        "--voice-prompt",
        vp,
        "--input-wav",
        str(input_wav),
        "--seed",
        str(seed),
        "--output-wav",
        str(output_wav),
    ]
    if text_prompt:
        cmd.extend(["--text-prompt", wrap_system_prompt(text_prompt)])
    if cpu_offload:
        cmd.append("--cpu-offload")
    return cmd
