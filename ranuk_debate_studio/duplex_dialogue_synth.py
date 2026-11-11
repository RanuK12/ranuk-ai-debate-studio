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

from .personaplex_duo import DebateScenario, PRESET_SCENARIOS
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
    "mars_reactor_crisis": (
        DebateScenario(
            slug="mars_reactor_crisis",
            title="MARS REACTOR EMERGENCY: 24kHz FULL-DUPLEX",
            subtitle="Astronaut Alex vs. Mission Control • Unscripted Acoustic Turn-Taking",
            speaker_a_name="Flight Director",
            speaker_a_role="Ground Support • Houston Mission Control",
            speaker_b_name="Astronaut Alex",
            speaker_b_role="Mars Transit Vessel • Core Commander",
            voice_prompt="VARM0.pt",
            system_prompt="High-stress technical dialogue between astronaut and ground control during a reactor meltdown.",
            sample_audio="mars_reactor_crisis.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="B",
                voice="en-US-ChristopherNeural",
                rate="+10%",
                text="Houston, we have a critical runaway on the primary coolant loop! Core temp is spiking past twelve hundred degrees!",
                overlap_prev_ms=0,
                tag="EMERGENCY ALERT",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="Copy that, Alex, telemetry confirms thermal surge. We're initiating magnetic bypass—",
                overlap_prev_ms=350,
                tag="MISSION CONTROL ACK",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-ChristopherNeural",
                rate="+12%",
                pitch="+2Hz",
                text="Negative on the bypass! Valves three and four are completely unresponsive! If we don't vent the secondary manifold in thirty seconds, the containment housing is going to rupture!",
                overlap_prev_ms=520,
                tag="INTERRUPTION (URGENT)",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+9%",
                text="Understood, manual vent sequence is unlocked on panel delta. Vent now, Alex!",
                overlap_prev_ms=420,
                tag="AUTHORIZATION OVERLAP",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-ChristopherNeural",
                rate="+8%",
                text="Venting manifold... Pressure dropping back to nominal. We just saved the ship.",
                overlap_prev_ms=300,
                tag="CRISIS RESOLVED",
            ),
        ],
        "split_wave",
    ),
    "banking_b2b_closer": (
        DebateScenario(
            slug="banking_b2b_closer",
            title="AI B2B ENTERPRISE VOICE CLOSER",
            subtitle="Real-Time Fraud Interception with Zero Turn-Taking Latency",
            speaker_a_name="James Hammer",
            speaker_a_role="Cardholder • $1,200 Declined Checkout",
            speaker_b_name="Sanni Virtanen",
            speaker_b_role="AI Security Specialist • First Neuron Bank",
            voice_prompt="VARF1.pt",
            system_prompt="Enterprise fraud desk scenario resolving card decline in real-time.",
            sample_audio="banking_b2b_closer.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+7%",
                text="Hey, I'm stuck at Home Depot trying to buy a contractor toolset and my corporate card was just declined.",
                overlap_prev_ms=0,
                tag="CUSTOMER PROBLEM",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+8%",
                text="I'm right here with you, James. Looking up your account right now. Can you confirm your date of birth?",
                overlap_prev_ms=450,
                tag="INSTANT AGENT RESPONSE",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="March 7, 1982. The purchase is twelve hundred dollars—",
                overlap_prev_ms=300,
                tag="USER CONFIRMATION",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+8%",
                text="—Got it! The flag triggered because the attempt was in Miami while your usual billing is Seattle. I just authorized the transaction; swipe again in five seconds!",
                overlap_prev_ms=500,
                tag="REAL-TIME RESOLUTION",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="It went through! That was insanely fast. Thanks!",
                overlap_prev_ms=380,
                tag="SUCCESS",
            ),
        ],
        "split_wave",
    ),
    "interruption_benchmark": (
        DebateScenario(
            slug="interruption_benchmark",
            title="CAN YOU INTERRUPT AN AI MID-SENTENCE?",
            subtitle="Testing Sub-200ms Acoustic Interruption with PersonaPlex 7B",
            speaker_a_name="Marcus Reed",
            speaker_a_role="Voice AI Benchmark Engineer",
            speaker_b_name="Aria (PersonaPlex)",
            speaker_b_role="24kHz Full-Duplex Neural Voice Agent",
            voice_prompt="NATF2.pt",
            system_prompt="Voice AI benchmark testing instantaneous acoustic interruption without broken audio buffers.",
            sample_audio="interruption_benchmark.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+8%",
                text="When building full-duplex agents, traditional systems rely on silence detection after you speak, which creates an unavoidable—",
                overlap_prev_ms=0,
                tag="AGENT EXPLANATION",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+9%",
                text="Wait, Aria, stop right there! Did you hear me interrupt you just now?",
                overlap_prev_ms=650,
                tag="USER INTERRUPT (LIVE)",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="Yes, perfectly! I paused the generation buffer in one hundred and eighty milliseconds. No robotic stutter, no buffer delay.",
                overlap_prev_ms=480,
                tag="INSTANT RECOVERY",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="That's the difference between legacy IVR and true conversational intelligence.",
                overlap_prev_ms=320,
                tag="BENCHMARK VERDICT",
            ),
        ],
        "split_wave",
    ),
    "agi_timeline_2026": (
        DebateScenario(
            slug="agi_timeline_2026",
            title="WILL AGI ARRIVE BY 2026 OR 2030?",
            subtitle="Compute Bottlenecks & Grid Limits vs. Recursive Test-Time Reasoning",
            speaker_a_name="Dr. Ethan Ross",
            speaker_a_role="Principal AI Alignment Researcher • Stanford",
            speaker_b_name="Elena Vance",
            speaker_b_role="Founding Partner • Neural Frontier Capital",
            voice_prompt="NATM0.pt",
            system_prompt="High-stakes Silicon Valley debate on AGI timeline, energy constraints, and test-time compute.",
            sample_audio="agi_timeline_2026.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="The idea that we achieve true Artificial General Intelligence by next year is a mathematical fantasy. We are literally running out of power grids and gigawatts.",
                overlap_prev_ms=0,
                tag="ENERGY BOTTLENECK",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="Ethan, you are still thinking in pre-training compute! Test-time reasoning and reinforcement learning self-play changed the game completely.",
                overlap_prev_ms=520,
                tag="REASONING PIVOT",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="Self-play works in closed verifiable domains like mathematics, but when you hit ambiguous real-world physical systems—",
                overlap_prev_ms=390,
                tag="REAL-WORLD LIMIT",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="—That's why synthetic world simulators are scaling ten times faster than human video datasets. The intelligence trajectory is exponential, not linear.",
                overlap_prev_ms=480,
                tag="EXPONENTIAL SHIFT",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="Exponential until you hit the brick wall of physical chip fabrication and thermal dissipation.",
                overlap_prev_ms=280,
                tag="HARDWARE REALITY",
            ),
        ],
        "glass_studio",
    ),
    "humanoid_vs_digital_agents": (
        DebateScenario(
            slug="humanoid_vs_digital_agents",
            title="HUMANOID ROBOTS VS AI AGENTS: WHO WINS FIRST?",
            subtitle="Physical Mechanical Hardware vs. Pure Autonomous Software Fleets",
            speaker_a_name="Mark Calder",
            speaker_a_role="Robotics Lead • Boston Systems",
            speaker_b_name="Sarah Lin",
            speaker_b_role="AI Agent Systems Architect • Ranuk Lab",
            voice_prompt="NATM1.pt",
            system_prompt="Debate on whether physical humanoid robotics or digital agent swarms will capture economic value first.",
            sample_audio="humanoid_vs_digital_agents.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Software agents can write code all day, but eighty percent of global GDP is physical: logistics, manufacturing, and heavy construction.",
                overlap_prev_ms=0,
                tag="PHYSICAL ECONOMY",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-EmmaMultilingualNeural",
                rate="+9%",
                text="Hold on, Mark! A humanoid robot costs eighty thousand dollars, tears its actuators, and takes two years to deliver. A digital agent fleet deploys in five milliseconds globally.",
                overlap_prev_ms=540,
                tag="DEPLOYMENT SPEED",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Sure, until the power goes out or you need someone to physically connect high-voltage cables in a server farm—",
                overlap_prev_ms=380,
                tag="PHYSICAL INFRA",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-EmmaMultilingualNeural",
                rate="+9%",
                text="—The digital agents will make the revenue that funds your humanoid factories. Software eats the money first, hardware follows.",
                overlap_prev_ms=460,
                tag="CAPITAL FLOW",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="When you put a reasoning agent inside an eight-axis robot, that is when the entire labor market changes forever.",
                overlap_prev_ms=260,
                tag="CONVERGENCE",
            ),
        ],
        "split_wave",
    ),
    "rag_is_dead_context_revolution": (
        DebateScenario(
            slug="rag_is_dead_context_revolution",
            title="IS RAG OFFICIALLY DEAD? 10M TOKEN CONTEXT",
            subtitle="Native Attention In-Context vs. Fragile Vector Chunking Databases",
            speaker_a_name="Kevin Zhao",
            speaker_a_role="Vector Database Lead • Silicon Valley",
            speaker_b_name="Maya Patel",
            speaker_b_role="Senior LLM Architect • Autonomous Systems",
            voice_prompt="NATF0.pt",
            system_prompt="Debate on long-context attention vs traditional retrieval-augmented generation.",
            sample_audio="rag_is_dead_context_revolution.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-GuyNeural",
                rate="+8%",
                text="Saying RAG is dead is completely naive. Shoving ten million tokens into an attention window burns astronomical compute on every single user query.",
                overlap_prev_ms=0,
                tag="COMPUTE COST",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="Wait, Kevin! Have you looked at KV-cache compression and linear attention kernels? Vector chunking chops your context into blind paragraphs and destroys cross-document reasoning.",
                overlap_prev_ms=520,
                tag="SEMANTIC LOSS",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-GuyNeural",
                rate="+8%",
                text="Yes, but enterprise compliance requires strict document access control that you can only enforce at the vector index level—",
                overlap_prev_ms=400,
                tag="ENTERPRISE ACL",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="—Hierarchical attention solves that natively. Once context is cheap, managing brittle embeddings and similarity re-ranking is legacy tech.",
                overlap_prev_ms=470,
                tag="ATTENTION NATIVE",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-GuyNeural",
                rate="+8%",
                text="The winning architecture will be hybrid: smart graph retrieval feeding massive in-memory attention windows.",
                overlap_prev_ms=270,
                tag="HYBRID WINNER",
            ),
        ],
        "glass_studio",
    ),
    "deepseek_r1_vs_openai_monopoly": (
        DebateScenario(
            slug="deepseek_r1_vs_openai_monopoly",
            title="DID OPEN SOURCE WIN? DEEPSEEK R1 VS CLOSED APIS",
            subtitle="Six-Million-Dollar Distillation vs Multi-Billion-Dollar Proprietary Giants",
            speaker_a_name="Julian Sterling",
            speaker_a_role="Cloud Enterprise Director • Proprietary AI",
            speaker_b_name="Clara Novak",
            speaker_b_role="Open-Weights & AI Sovereignty Strategist",
            voice_prompt="VARF2.pt",
            system_prompt="Debate on open-weights reasoning models like DeepSeek R1 disrupting proprietary AI monopolies.",
            sample_audio="deepseek_r1_vs_openai_monopoly.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="Everyone is hyping open weights after DeepSeek, but open models can't maintain the massive multi-modal inference clusters required by Fortune 500 banks.",
                overlap_prev_ms=0,
                tag="ENTERPRISE MOAT",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="Julian, you missed the headline! DeepSeek matched frontier reasoning at two percent of the training cost using reinforcement learning and pure distillation.",
                overlap_prev_ms=510,
                tag="COST DISRUPTION",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="Cost is one thing, but proprietary labs still hold the proprietary test-time compute architectures that no one has published—",
                overlap_prev_ms=390,
                tag="SECRET ARCHITECTURE",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="—The community replicates those architectures in under forty-eight hours. The open source developer ecosystem is the largest research lab on Earth.",
                overlap_prev_ms=480,
                tag="OPEN COMMUNITY SPEED",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="When intelligence becomes a commodity, the real moats shift to proprietary data and real-time distribution.",
                overlap_prev_ms=280,
                tag="FINAL SHIFT",
            ),
        ],
        "split_wave",
    ),
    "ai_swe_agents_2026": (
        DebateScenario(
            slug="ai_swe_agents_2026",
            title="WILL AI DEV AGENTS KILL JUNIOR ROLES IN 2026?",
            subtitle="Autonomous Coding Swarms vs Human Architectural Judgment",
            speaker_a_name="Dave Miller",
            speaker_a_role="Senior Engineering Manager • Big Tech",
            speaker_b_name="Chloe Zhang",
            speaker_b_role="Autonomous Agent Systems Engineer • YC W26",
            voice_prompt="NATF1.pt",
            system_prompt="Debate on how autonomous software engineering agents impact developer jobs and junior hiring.",
            sample_audio="ai_swe_agents_2026.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-ChristopherNeural",
                rate="+8%",
                text="If companies stop hiring junior developers because AI writes the boilerplate, where do they expect future senior architects to come from in five years?",
                overlap_prev_ms=0,
                tag="PIPELINE CRISIS",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-EmmaMultilingualNeural",
                rate="+9%",
                text="Dave, junior developers aren't dying—their baseline is elevating! Instead of writing syntax errors for eight hours, a first-year engineer is orchestrating four autonomous dev loops.",
                overlap_prev_ms=530,
                tag="ELEVATED BASELINE",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-ChristopherNeural",
                rate="+8%",
                text="How can a junior orchestrate an agent if they don't understand memory leaks, distributed locks, or database indexing under high load—",
                overlap_prev_ms=410,
                tag="FUNDAMENTALS",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-EmmaMultilingualNeural",
                rate="+9%",
                text="—They learn by inspecting deterministic agent traces! It's active pair programming with the smartest codebase debugger in human history.",
                overlap_prev_ms=470,
                tag="ACCELERATED LEARNING",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-ChristopherNeural",
                rate="+8%",
                text="The engineers who master system design and verification will be ten times more valuable than ever.",
                overlap_prev_ms=270,
                tag="ARCHITECT VERDICT",
            ),
        ],
        "glass_studio",
    ),
    "quantum_vs_blackwell_gpus": (
        DebateScenario(
            slug="quantum_vs_blackwell_gpus",
            title="CAN QUANTUM AI BEAT NVIDIA's BLACKWELL CLUSTERS?",
            subtitle="Photonic & Neutral-Atom QPUs vs. Massive Tensor Silicon",
            speaker_a_name="Dr. Harrison Fox",
            speaker_a_role="Quantum Hardware Fellow • Institute of Physics",
            speaker_b_name="Liam Vance",
            speaker_b_role="NVIDIA GPU Cluster Architect",
            voice_prompt="VARM2.pt",
            system_prompt="Debate on whether quantum accelerators or massive classical GPU clusters will dominate next-gen AI training.",
            sample_audio="quantum_vs_blackwell_gpus.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="NVIDIA can stack one hundred thousand Blackwell chips, but classical matrix multiplication will always hit an asymptotic thermal ceiling that only quantum superposition can break.",
                overlap_prev_ms=0,
                tag="QUANTUM ADVANTAGE",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AndrewMultilingualNeural",
                rate="+9%",
                text="Harrison, quantum coherence breaks down the moment you look at it funny! Blackwell delivers twenty petaflops per chip in FP4 today in production, not twenty years from now.",
                overlap_prev_ms=530,
                tag="PRODUCTION REALITY",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Neutral-atom and photonic qubits achieved fault-tolerant error correction this year, cutting optimization cycles from weeks to minutes—",
                overlap_prev_ms=400,
                tag="ERROR CORRECTION",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AndrewMultilingualNeural",
                rate="+9%",
                text="—For chemical simulation, maybe! But for LLM attention and trillion-parameter token streams, classical optical interconnects dominate every single benchmark.",
                overlap_prev_ms=480,
                tag="BANDWIDTH DOMINANCE",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Hybrid quantum-classical algorithms will be the true holy grail by 2028.",
                overlap_prev_ms=260,
                tag="CONVERGENCE",
            ),
        ],
        "split_wave",
    ),
    "x402_ai_agent_wallets": (
        DebateScenario(
            slug="x402_ai_agent_wallets",
            title="WHY AI AGENTS NEED CRYPTO WALLETS: THE x402 STANDARD",
            subtitle="Machine-to-Machine Autonomous Micropayments in USDC vs Banking Rails",
            speaker_a_name="Robert Sterling",
            speaker_a_role="Fintech Compliance & Banking VP",
            speaker_b_name="Alyssa Vance",
            speaker_b_role="x402 Protocol Architect • Base Mainnet",
            voice_prompt="NATF2.pt",
            system_prompt="Debate on AI agents executing autonomous financial transactions via HTTP 402 Payment Required.",
            sample_audio="x402_ai_agent_wallets.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-GuyNeural",
                rate="+8%",
                text="Handing autonomous agents private keys to spend real money is a financial nightmare. Who goes to prison when an agent commits market manipulation?",
                overlap_prev_ms=0,
                tag="REGULATORY RISK",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="Robert, how else does an AI pay another AI for a GPU second or an API call? An agent can't open a Chase bank account or swipe a Visa card!",
                overlap_prev_ms=510,
                tag="MACHINE PAYMENTS",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-GuyNeural",
                rate="+8%",
                text="That's what corporate credit cards and monthly cloud subscriptions are for—",
                overlap_prev_ms=360,
                tag="LEGACY SUBSCRIPTIONS",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="—Monthly subscriptions are broken for micro-queries! The HTTP 402 standard lets an agent pay zero point zero zero one cents per call directly on Base USDC with zero counterparty risk.",
                overlap_prev_ms=480,
                tag="HTTP 402 PROTOCOL",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-GuyNeural",
                rate="+8%",
                text="Programmable money with cryptographic spend limits will become the foundational backbone of the machine economy.",
                overlap_prev_ms=270,
                tag="FUTURE STANDARDS",
            ),
        ],
        "glass_studio",
    ),
    "speech_to_speech_vs_cascade": (
        DebateScenario(
            slug="speech_to_speech_vs_cascade",
            title="WHY CASCADE VOICE AI (STT+LLM+TTS) IS DEAD",
            subtitle="1,200ms Latency Bottleneck vs 150ms Direct Neural Audio Tokens",
            speaker_a_name="Jason Cole",
            speaker_a_role="Enterprise Contact Center Systems VP",
            speaker_b_name="Dr. Priya Sharma",
            speaker_b_role="Neural Audio Lead • PersonaPlex",
            voice_prompt="VARF0.pt",
            system_prompt="Debate comparing legacy Whisper+LLM+TTS pipelines against direct full-duplex neural audio token models.",
            sample_audio="speech_to_speech_vs_cascade.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Most voice apps today still use Whisper for speech-to-text, Claude or GPT for reasoning, and ElevenLabs for voice. It works, and it's battle-tested.",
                overlap_prev_ms=0,
                tag="CASCADE PIPELINE",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="Jason, it feels like talking through a walkie-talkie with a satellite delay! You lose emotion, sarcasm, and tone the exact moment audio is flattened into plain text.",
                overlap_prev_ms=520,
                tag="LATENCY KILLER",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Sure, but native speech-to-speech models are much harder to guardrail and steer in regulated enterprise customer support—",
                overlap_prev_ms=400,
                tag="SAFETY CONCERNS",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="—PersonaPlex 7B proved you can steer full-duplex audio tokens natively at twenty-four kilohertz with sub-two-hundred-millisecond response and zero text latency.",
                overlap_prev_ms=470,
                tag="NEURAL SPEECH",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Any brand still using three-step cascade voice in 2026 will lose their customers to real-time conversation.",
                overlap_prev_ms=280,
                tag="INDUSTRY SHIFT",
            ),
        ],
        "split_wave",
    ),
    "hft_ai_vs_human_quants": (
        DebateScenario(
            slug="hft_ai_vs_human_quants",
            title="REINFORCEMENT LEARNING IN HFT: END OF HUMAN QUANTS?",
            subtitle="Sub-Millisecond Orderbook Reinforcement vs Macro Economic Discretion",
            speaker_a_name="Arthur Pendelton",
            speaker_a_role="Senior Macro Portfolio Manager • Citadel",
            speaker_b_name="Victor Vance",
            speaker_b_role="Algorithmic Trading Lead • High Frequency AI",
            voice_prompt="NATM3.pt",
            system_prompt="Debate on reinforcement learning algorithms dominating high-frequency order books over human discretionary traders.",
            sample_audio="hft_ai_vs_human_quants.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="Algorithms have dominated order execution for decades, but when geopolitical black swans hit, neural networks lack the historical intuition that only a veteran trader possesses.",
                overlap_prev_ms=0,
                tag="MACRO INTUITION",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-ChristopherNeural",
                rate="+9%",
                text="Arthur, human reaction time is three hundred milliseconds! By the time your brain registers a breaking headline, our reinforcement models have rebalanced five thousand positions across twenty exchanges.",
                overlap_prev_ms=530,
                tag="MICROSECOND ADVANTAGE",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="And when liquidity evaporates in a flash crash because every algorithm runs the exact same correlated policy—",
                overlap_prev_ms=390,
                tag="CORRELATION RISK",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-ChristopherNeural",
                rate="+9%",
                text="—Adaptive entropy models prevent herd behavior. Modern quant RL generates liquidity precisely when manual market makers pull their quotes.",
                overlap_prev_ms=480,
                tag="ADAPTIVE LIQUIDITY",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-AndrewMultilingualNeural",
                rate="+8%",
                text="The quants who combine algorithmic micro-speed with human macro risk guardrails will capture the highest alpha.",
                overlap_prev_ms=270,
                tag="ALPHA CONSENSUS",
            ),
        ],
        "glass_studio",
    ),
    "on_device_slm_vs_cloud": (
        DebateScenario(
            slug="on_device_slm_vs_cloud",
            title="WHY 7B LOCAL MODELS BEAT GIANT CLOUD LLMS",
            subtitle="Apple Silicon Neural Engine & Zero API Cost vs 100B Parameter Cloud Monoliths",
            speaker_a_name="Derek Young",
            speaker_a_role="Cloud SaaS Infrastructure Architect",
            speaker_b_name="Zoe Bennett",
            speaker_b_role="Edge AI & Local Inference Pioneer",
            voice_prompt="NATF3.pt",
            system_prompt="Debate on 7B small language models running locally on Mac M4 and edge devices vs multi-billion parameter cloud APIs.",
            sample_audio="on_device_slm_vs_cloud.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-GuyNeural",
                rate="+8%",
                text="Why would any enterprise settle for a quantized seven-billion model on a local laptop when they can stream responses from a multi-modal frontier model in the cloud?",
                overlap_prev_ms=0,
                tag="CLOUD SCALE",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-EmmaMultilingualNeural",
                rate="+9%",
                text="Derek, privacy and latency! On Apple M4, a quantized seven-billion model spits out two hundred tokens a second with zero network lag, zero cloud downtime, and zero data leakage.",
                overlap_prev_ms=520,
                tag="EDGE SPEED",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-GuyNeural",
                rate="+8%",
                text="Fine for summarizing emails, but for multi-step mathematical proofs and deep domain reasoning, small models still hallucinate—",
                overlap_prev_ms=410,
                tag="REASONING GAP",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-EmmaMultilingualNeural",
                rate="+9%",
                text="—Not with test-time search! Fine-tuned edge SLMs running local Monte Carlo rollouts match models twenty times their size without paying five hundred dollars a month in API bills.",
                overlap_prev_ms=470,
                tag="DISTILLED ACCURACY",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-GuyNeural",
                rate="+8%",
                text="Local inference for real-time speed, hybrid cloud for frontier complexity: that is the 2026 enterprise standard.",
                overlap_prev_ms=280,
                tag="EDGE HYBRID",
            ),
        ],
        "split_wave",
    ),
    "synthetic_data_wall": (
        DebateScenario(
            slug="synthetic_data_wall",
            title="ARE WE RUNNING OUT OF HUMAN DATA? SYNTHETIC AI",
            subtitle="Self-Play RLVR Verification vs Autophagous Model Collapse",
            speaker_a_name="Dr. Gregory Ross",
            speaker_a_role="AI Data Integrity Director • Research Institute",
            speaker_b_name="Natalie Chen",
            speaker_b_role="Synthetic Reasoning Lead • Frontier Labs",
            voice_prompt="VARF3.pt",
            system_prompt="Debate on training models on synthetic data vs recursive model collapse and the human text wall.",
            sample_audio="synthetic_data_wall.wav",
            captions=[],
        ),
        [
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Every major frontier lab has already ingested the entire public internet. If you train models on synthetic AI outputs, you get autophagous model collapse within three generations.",
                overlap_prev_ms=0,
                tag="MODEL COLLAPSE",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="Gregory, that only happens if you train on unverified synthetic junk! In reinforcement learning with verifiable rewards, models solve code and formal proofs where truth is mathematically verified.",
                overlap_prev_ms=530,
                tag="VERIFIABLE REWARDS",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Math and code are tiny subsets of human experience. You cannot synthesize novel human philosophy, cultural nuance, or emotional empathy—",
                overlap_prev_ms=390,
                tag="CULTURE & NUANCE",
            ),
            DialogueTurn(
                speaker="B",
                voice="en-US-AvaMultilingualNeural",
                rate="+9%",
                text="—AlphaGo didn't learn from human intuition: it played against itself millions of times and discovered moves no human imagined in four thousand years. Self-play breaks the human ceiling.",
                overlap_prev_ms=490,
                tag="SELF-PLAY BREAKTHROUGH",
            ),
            DialogueTurn(
                speaker="A",
                voice="en-US-BrianNeural",
                rate="+8%",
                text="Verifiable synthetic reasoning is the true bridge to superintelligence.",
                overlap_prev_ms=260,
                tag="SUPERINTELLIGENCE",
            ),
        ],
        "glass_studio",
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
    if slug in HOT_DEBATE_SCRIPTS:
        base_scenario, turns, preferred_style = HOT_DEBATE_SCRIPTS[slug]
    elif slug in PRESET_SCENARIOS:
        base_scenario = PRESET_SCENARIOS[slug]
        turns = []
        for cap in base_scenario.captions:
            spk = cap.get("speaker", "A")
            v = "en-US-AndrewMultilingualNeural" if spk == "A" else "en-US-AvaMultilingualNeural"
            turns.append(
                DialogueTurn(
                    speaker=spk,
                    voice=v,
                    rate="+8%",
                    text=cap.get("text", ""),
                    overlap_prev_ms=250 if len(turns) > 0 else 0,
                    tag=f"SPEAKER {spk}",
                )
            )
        preferred_style = "split_wave"
    else:
        try:
            from .debate_catalog_90d import get_scenario_and_turns
            base_scenario, turns, preferred_style = get_scenario_and_turns(slug)
        except Exception as e:
            raise KeyError(f"Unknown debate slug '{slug}'. Available: {list(HOT_DEBATE_SCRIPTS.keys()) + list(PRESET_SCENARIOS.keys())}. Error: {e}")
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
