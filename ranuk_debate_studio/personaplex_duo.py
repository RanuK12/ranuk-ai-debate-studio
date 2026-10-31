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
            {"start": 0.0, "end": 1.9, "speaker": "A", "text": "I've been thinking about starting a diet."},
            {"start": 1.9, "end": 6.5, "speaker": "B", "text": "Yeah, starting a diet can feel daunting, but you could keep it simple."},
            {"start": 6.5, "end": 9.4, "speaker": "B", "text": "Focus on eating more veggies and fruits..."},
            {"start": 9.4, "end": 12.0, "speaker": "A", "text": "Before I forget, I signed up for a marathon!"},
            {"start": 12.0, "end": 14.3, "speaker": "B", "text": "All right, congrats on signing up for the marathon!"},
            {"start": 14.3, "end": 16.5, "speaker": "B", "text": "That's a big challenge. You've got a lot of time."},
            {"start": 16.5, "end": 19.8, "speaker": "B", "text": "Focus on building a solid base with regular long runs."},
            {"start": 19.8, "end": 21.2, "speaker": "B", "text": "Stay hydrated."},
            {"start": 21.2, "end": 23.5, "speaker": "B", "text": "Make sure you fuel right before and after."},
            {"start": 23.5, "end": 26.5, "speaker": "B", "text": "And don't forget to stretch and take care of your feet!"},
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
            {"start": 0.0, "end": 4.5, "speaker": "A", "text": "So we were looking at deploying the neural network cluster..."},
            {"start": 4.5, "end": 6.5, "speaker": "B", "text": "Uh-huh, yeah, right."},
            {"start": 6.5, "end": 11.0, "speaker": "A", "text": "...and latency dropped from 800 milliseconds down to 180ms."},
            {"start": 11.0, "end": 14.5, "speaker": "B", "text": "That's incredible speed for 24kHz full-duplex."},
            {"start": 14.5, "end": 20.0, "speaker": "A", "text": "Exactly, the models can interrupt without cutting off the audio stream."},
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
            {"start": 0.0, "end": 2.0, "speaker": "A", "text": "I'm stuck here in line at Home Depot."},
            {"start": 2.0, "end": 5.1, "speaker": "A", "text": "I've got a bunch of tools that I'm trying to buy..."},
            {"start": 5.1, "end": 6.5, "speaker": "A", "text": "And my card got declined."},
            {"start": 6.5, "end": 7.8, "speaker": "B", "text": "Oh no, that's never fun. Let me check your account."},
            {"start": 7.8, "end": 10.6, "speaker": "B", "text": "Can I get your full name and date of birth, please?"},
            {"start": 10.6, "end": 13.5, "speaker": "A", "text": "Yeah, my name is James Hammer."},
            {"start": 13.5, "end": 18.5, "speaker": "A", "text": "And my date of birth is March 7, 1952."},
            {"start": 18.5, "end": 20.6, "speaker": "B", "text": "Thanks, James. Let me pull that up real quick."},
            {"start": 20.6, "end": 22.5, "speaker": "B", "text": "One moment, please..."},
            {"start": 22.5, "end": 26.8, "speaker": "B", "text": "Okay, I see the issue. There was a transaction for $1,200 at Home Depot."},
            {"start": 26.8, "end": 30.0, "speaker": "B", "text": "Your usual location is Seattle..."},
            {"start": 30.0, "end": 33.8, "speaker": "B", "text": "...but the transaction was attempted in Miami. That triggered the security flag."},
            {"start": 33.8, "end": 37.2, "speaker": "B", "text": "Would you like me to approve and resubmit the transaction?"},
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
            {"start": 0.0, "end": 3.2, "speaker": "B", "text": "Hello? Hi. Hi, I'm Alex. Astronaut on the Mars mission."},
            {"start": 3.2, "end": 7.0, "speaker": "A", "text": "Hi, nice to meet you. I'm just a ground engineer."},
            {"start": 7.0, "end": 11.5, "speaker": "B", "text": "Well, we've got a critical problem here in orbit."},
            {"start": 11.5, "end": 14.5, "speaker": "A", "text": "Okay, copy that. What is the problem?"},
            {"start": 14.5, "end": 19.5, "speaker": "B", "text": "The reactor core is melting! Coolant loops are collapsing!"},
            {"start": 19.5, "end": 24.0, "speaker": "A", "text": "Oh, that's not good. Telemetry shows core temp spiking!"},
            {"start": 24.0, "end": 29.5, "speaker": "B", "text": "Several other backup systems are failing across the habitat!"},
            {"start": 29.5, "end": 35.0, "speaker": "B", "text": "If we don't fix this now, we're talking about losing the entire ship!"},
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
