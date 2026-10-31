# © 2026 Ranuk IT Solutions — ranuk.dev
"""
duplex_dialogue_synth.py — Full-Duplex Stereo Debate Synthesizer & Timeline Mixer.

Generates natural multi-turn debates in Spanish and English on current 2026 topics,
mixing Speaker A onto the Left Channel (FL) and Speaker B onto the Right Channel (FR)
with sub-second full-duplex interruptions and backchannels.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import edge_tts
import numpy as np

from .personaplex_duo import DebateScenario
from .waveform_analyzer import find_ffmpeg


@dataclass
class DialogueTurn:
    speaker: str  # "A" (Left Channel) or "B" (Right Channel)
    text: str
    voice: str
    rate: str = "+6%"
    pitch: str = "+0Hz"
    overlap_prev_ms: int = 0  # Positive value = start N ms BEFORE previous turn ends (full-duplex interruption!)
    pause_after_ms: int = 120
    tag: str = "ARGUMENTO EN VIVO"


HOT_DEBATE_SCRIPTS: Dict[str, Tuple[DebateScenario, List[DialogueTurn], str]] = {
    "ia_vs_ingenieros_2026": (
        DebateScenario(
            slug="ia_vs_ingenieros_2026",
            title="¿LA IA REEMPLAZARÁ A LOS INGENIEROS EN 2026?",
            subtitle="Agentes Autónomos de Código vs. Arquitectura Humana en Producción",
            speaker_a_name="Mateo Vega",
            speaker_a_role="CTO & Arquitecto de Sistemas Críticos",
            speaker_b_name="Sofía Kovács",
            speaker_b_role="Lead AI Agent Engineer • Ranuk Lab",
            voice_prompt="NATF2.pt",
            system_prompt="Debate técnico en español sobre agentes autónomos de software vs ingeniería tradicional en 2026.",
            sample_audio="ia_vs_ingenieros_2026.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="es-ES-AlvaroNeural",
                rate="+8%",
                text="Seamos realistas, Sofía: hoy todos hablan de agentes que programan solos, pero cuando un banco cae a las tres de la mañana, ningún modelo asume la culpa.",
                overlap_prev_ms=0,
                tag="POSTURA CRÍTICA",
            ),
            DialogueTurn(
                speaker="B",
                voice="es-MX-DaliaNeural",
                rate="+9%",
                text="¡Espera, Mateo! Ese era el debate de hace dos años. Hoy un enjambre de agentes detecta el fallo, valida el árbol sintáctico y despliega el parche en segundos.",
                overlap_prev_ms=520,
                tag="INTERRUPCIÓN FULL-DUPLEX",
            ),
            DialogueTurn(
                speaker="A",
                voice="es-ES-AlvaroNeural",
                rate="+9%",
                text="Claro, hasta que alucinan una librería que no existe y rompen producción—",
                overlap_prev_ms=380,
                tag="CONTRAARGUMENTO",
            ),
            DialogueTurn(
                speaker="B",
                voice="es-MX-DaliaNeural",
                rate="+9%",
                text="—Por eso no les das acceso ciego: les pones pruebas deterministas y auditoría automática. El ingeniero no desaparece, pasa a dirigir veinte agentes.",
                overlap_prev_ms=480,
                tag="SOLAPAMIENTO EN VIVO",
            ),
            DialogueTurn(
                speaker="A",
                voice="es-ES-AlvaroNeural",
                rate="+8%",
                text="En eso coincido al cien por ciento: muere el picador de código, pero nace el arquitecto de sistemas autónomos.",
                overlap_prev_ms=260,
                tag="CONSENSO EJECUTIVO",
            ),
        ],
        "glass_studio",
    ),
    "economia_x402_billeteras_ia": (
        DebateScenario(
            slug="economia_x402_billeteras_ia",
            title="¿IAs CON BILLETERA PROPIA? ECONOMÍA x402",
            subtitle="Pagos Máquina-a-Máquina en USDC vs. Banca Tradicional",
            speaker_a_name="Lucas Ferrara",
            speaker_a_role="Analista Fintech & Regulación Bancaria",
            speaker_b_name="Elena R.",
            speaker_b_role="Estratega Web3 & Protocolo HTTP x402",
            voice_prompt="VARF1.pt",
            system_prompt="Debate ágil sobre pagos máquina-a-máquina con el protocolo HTTP 402 en Base USDC.",
            sample_audio="economia_x402_billeteras_ia.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="es-AR-TomasNeural",
                rate="+8%",
                text="Darle una billetera cripto autónoma a una inteligencia artificial parece un riesgo enorme. ¿Qué pasa si un bot gasta diez mil dólares por un bucle infinito?",
                overlap_prev_ms=0,
                tag="RIESGO FINANCIERO",
            ),
            DialogueTurn(
                speaker="B",
                voice="es-AR-ElenaNeural",
                rate="+9%",
                text="Pará, pará, Lucas—¿y cómo pensás que un agente va a comprar cómputo o datos en tiempo real? ¿Pidéndole permiso al banco un viernes a la noche?",
                overlap_prev_ms=540,
                tag="INTERRUPCIÓN EN VIVO",
            ),
            DialogueTurn(
                speaker="A",
                voice="es-AR-TomasNeural",
                rate="+9%",
                text="No digo pedir permiso manual, pero tiene que existir un límite estricto—",
                overlap_prev_ms=410,
                tag="RÉPLICA RÁPIDA",
            ),
            DialogueTurn(
                speaker="B",
                voice="es-AR-ElenaNeural",
                rate="+9%",
                text="—¡Ese límite está programado en el contrato! Con el protocolo x402 en Base, el agente paga centavos de USDC por cada llamada verificada en milisegundos.",
                overlap_prev_ms=490,
                tag="FULL-DUPLEX OVERLAP",
            ),
            DialogueTurn(
                speaker="A",
                voice="es-AR-TomasNeural",
                rate="+8%",
                text="Ahí cambia todo: pasamos de pagar suscripciones mensuales infladas a micro-pagos exactos entre máquinas.",
                overlap_prev_ms=280,
                tag="CONCLUSIÓN CLAVE",
            ),
        ],
        "vertical_reel",
    ),
    "full_duplex_voice_revolution": (
        DebateScenario(
            slug="full_duplex_voice_revolution",
            title="THE DEATH OF WALKIE-TALKIE VOICE AI",
            subtitle="Why 180ms Full-Duplex Speech-to-Speech Replaces Legacy Voice Bots",
            speaker_a_name="Marcus Vance",
            speaker_a_role="Enterprise Voice Systems Architect",
            speaker_b_name="Aria Chen",
            speaker_b_role="NVIDIA PersonaPlex Full-Duplex Lead",
            voice_prompt="NATF2.pt",
            system_prompt="Technical debate comparing half-duplex STT-LLM-TTS pipelines against NVIDIA PersonaPlex 7B full-duplex audio.",
            sample_audio="full_duplex_voice_revolution.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+7%",
                text="For the last five years, every enterprise voice bot felt like talking over a broken walkie-talkie. You speak, wait two seconds of awkward silence, and hope it didn't reset.",
                overlap_prev_ms=0,
                tag="LEGACY BOT PROBLEM",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+8%",
                text="Hold on, Marcus—notice how I just jumped in mid-thought without breaking the stream? That happens because we eliminated the text bottleneck completely.",
                overlap_prev_ms=520,
                tag="LIVE INTERRUPT (180ms)",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="Right, because when you stream neural audio tokens at twenty-four kilohertz—",
                overlap_prev_ms=390,
                tag="BACKCHANNEL + SETUP",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+8%",
                text="—the model listens and speaks simultaneously on dual channels. It hears your hesitation, adapts its persona instantly, and closes real B2B deals.",
                overlap_prev_ms=470,
                tag="FULL-DUPLEX OVERLAP",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+7%",
                text="Once a customer experiences zero-latency turn-taking, legacy voice menus are officially dead.",
                overlap_prev_ms=260,
                tag="VERDICT",
            ),
        ],
        "split_wave",
    ),
    "open_vs_closed_ai_2026": (
        DebateScenario(
            slug="open_vs_closed_ai_2026",
            title="MODELOS ABIERTOS VS. GIGANTES CERRADOS",
            subtitle="¿Dónde correrá la inteligencia empresarial en 2026?",
            speaker_a_name="Diego Morales",
            speaker_a_role="VP de Infraestructura Cloud & APIs",
            speaker_b_name="Valeria Soto",
            speaker_b_role="Directora de IA Soberana & Open-Weights",
            voice_prompt="NATM1.pt",
            system_prompt="Debate ejecutivo sobre modelos open-weights locales como PersonaPlex 7B frente a APIs cerradas.",
            sample_audio="open_vs_closed_ai_2026.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="es-MX-JorgeNeural",
                rate="+8%",
                text="Valeria, para una empresa mediana es mucho más fácil pagar una API en la nube que mantener servidores propios con modelos abiertos.",
                overlap_prev_ms=0,
                tag="TESIS CLOUD API",
            ),
            DialogueTurn(
                speaker="B",
                voice="es-MX-DaliaNeural",
                rate="+8%",
                pitch="+2Hz",
                text="¡Un segundo, Diego! Eso funciona hasta que te cambian el precio, te bloquean por límite de tokens o auditan tus datos confidenciales.",
                overlap_prev_ms=500,
                tag="INTERRUPCIÓN FULL-DUPLEX",
            ),
            DialogueTurn(
                speaker="A",
                voice="es-MX-JorgeNeural",
                rate="+8%",
                text="Bueno, pero antes necesitabas un clúster entero para igualar la calidad—",
                overlap_prev_ms=390,
                tag="OBJECIÓN DE HARDWARE",
            ),
            DialogueTurn(
                speaker="B",
                voice="es-MX-DaliaNeural",
                rate="+8%",
                pitch="+2Hz",
                text="—Ya no. Hoy un modelo especializado de siete mil millones de parámetros como PersonaPlex corre voz full-duplex en tiempo real con privacidad total.",
                overlap_prev_ms=480,
                tag="DATO TÉCNICO CLAVE",
            ),
            DialogueTurn(
                speaker="A",
                voice="es-MX-JorgeNeural",
                rate="+8%",
                text="La combinación híbrida gana: modelos compactos propios en tiempo real y enrutamiento inteligente.",
                overlap_prev_ms=260,
                tag="SÍNTESIS",
            ),
        ],
        "split_wave",
    ),
}


def _decode_mono_24k(audio_file: Path, sample_rate: int = 24000) -> np.ndarray:
    ffmpeg = find_ffmpeg()
    raw = subprocess.check_output(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(audio_file),
            "-af",
            "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-48dB",
            "-f",
            "s16le",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "pipe:1",
        ],
        timeout=30,
    )
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    # Trim trailing near-silence so overlaps align tightly with spoken words
    non_silent = np.where(np.abs(samples) > 0.008)[0]
    if len(non_silent) > 100:
        end_idx = min(len(samples), int(non_silent[-1]) + int(sample_rate * 0.06))
        samples = samples[:end_idx]
    return samples


async def _synth_turn_mp3(turn: DialogueTurn, out_mp3: Path) -> None:
    voices_to_try = [turn.voice, "en-US-GuyNeural", "en-US-JennyNeural", "es-ES-AlvaroNeural"]
    last_err = None
    for attempt in range(4):
        v = voices_to_try[min(attempt, len(voices_to_try) - 1)]
        try:
            comm = edge_tts.Communicate(turn.text, voice=v, rate=turn.rate, pitch=turn.pitch)
            await comm.save(str(out_mp3))
            if out_mp3.exists() and out_mp3.stat().st_size > 200:
                return
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.6)
    raise RuntimeError(f"Failed to synthesize turn after retries: {last_err}")


def synthesize_duplex_debate(
    slug: str,
    output_wav: Path,
    sample_rate: int = 24000,
) -> Tuple[DebateScenario, Path, str]:
    """
    Synthesize a multi-turn debate into a true 24kHz Stereo WAV file where:
      - Left Channel (FL) = Speaker A
      - Right Channel (FR) = Speaker B
      - Turns with `overlap_prev_ms > 0` start while the other speaker is still talking,
        producing genuine full-duplex overlapping audio and exact millisecond captions.
    """
    if slug not in HOT_DEBATE_SCRIPTS:
        raise KeyError(f"Unknown debate slug '{slug}'. Available: {list(HOT_DEBATE_SCRIPTS)}")

    base_scenario, turns, preferred_style = HOT_DEBATE_SCRIPTS[slug]
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    meta_json = output_wav.with_suffix(".json")
    if output_wav.exists() and meta_json.exists() and output_wav.stat().st_size > 10000:
        cached_caps = json.loads(meta_json.read_text(encoding="utf-8"))
        cached_scenario = DebateScenario(
            slug=base_scenario.slug,
            title=base_scenario.title,
            subtitle=base_scenario.subtitle,
            speaker_a_name=base_scenario.speaker_a_name,
            speaker_a_role=base_scenario.speaker_a_role,
            speaker_b_name=base_scenario.speaker_b_name,
            speaker_b_role=base_scenario.speaker_b_role,
            voice_prompt=base_scenario.voice_prompt,
            system_prompt=base_scenario.system_prompt,
            sample_audio=output_wav.name,
            captions=cached_caps,
        )
        return cached_scenario, output_wav, preferred_style

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        async def _run_all() -> List[Path]:
            mp3_paths: List[Path] = []
            for idx, turn in enumerate(turns):
                p = tmp_path / f"turn_{idx}.mp3"
                await _synth_turn_mp3(turn, p)
                mp3_paths.append(p)
            return mp3_paths

        mp3_files = asyncio.run(_run_all())
        mono_arrays = [_decode_mono_24k(p, sample_rate=sample_rate) for p in mp3_files]

    # Calculate timeline placements with full-duplex overlaps
    placements: List[Tuple[int, int, DialogueTurn, np.ndarray]] = []
    cursor_sample = int(0.35 * sample_rate)

    for turn, arr in zip(turns, mono_arrays):
        if placements and turn.overlap_prev_ms > 0:
            overlap_samples = int((turn.overlap_prev_ms / 1000.0) * sample_rate)
            start_sample = max(0, cursor_sample - overlap_samples)
        else:
            start_sample = cursor_sample

        end_sample = start_sample + len(arr)
        placements.append((start_sample, end_sample, turn, arr))
        cursor_sample = end_sample + int((turn.pause_after_ms / 1000.0) * sample_rate)

    total_samples = cursor_sample + int(0.6 * sample_rate)
    left_ch = np.zeros(total_samples, dtype=np.float32)
    right_ch = np.zeros(total_samples, dtype=np.float32)

    captions: List[Dict[str, object]] = []
    for start_s, end_s, turn, arr in placements:
        # Apply gentle 15ms fade-in/out to prevent clicks
        fade_len = min(int(0.015 * sample_rate), len(arr) // 4)
        if fade_len > 1:
            arr = arr.copy()
            arr[:fade_len] *= np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
            arr[-fade_len:] *= np.linspace(1.0, 0.0, fade_len, dtype=np.float32)

        if turn.speaker == "A":
            left_ch[start_s:end_s] += arr
            spk_name = base_scenario.speaker_a_name
        else:
            right_ch[start_s:end_s] += arr
            spk_name = base_scenario.speaker_b_name

        captions.append(
            {
                "start": round(start_s / sample_rate, 3),
                "end": round(end_s / sample_rate, 3),
                "speaker": turn.speaker,
                "speaker_name": spk_name,
                "tag": turn.tag,
                "text": turn.text,
            }
        )

    # Normalize & write 16-bit stereo WAV
    stereo = np.stack([np.clip(left_ch, -0.98, 0.98), np.clip(right_ch, -0.98, 0.98)], axis=1)
    pcm16 = (stereo * 32767.0).astype(np.int16)

    with wave.open(str(output_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())

    meta_json.write_text(json.dumps(captions, ensure_ascii=False, indent=2), encoding="utf-8")

    updated_scenario = DebateScenario(
        slug=base_scenario.slug,
        title=base_scenario.title,
        subtitle=base_scenario.subtitle,
        speaker_a_name=base_scenario.speaker_a_name,
        speaker_a_role=base_scenario.speaker_a_role,
        speaker_b_name=base_scenario.speaker_b_name,
        speaker_b_role=base_scenario.speaker_b_role,
        voice_prompt=base_scenario.voice_prompt,
        system_prompt=base_scenario.system_prompt,
        sample_audio=output_wav.name,
        captions=captions,
    )
    return updated_scenario, output_wav, preferred_style
