"""Scenario loading and patient-persona prompt construction.

A *scenario* is a small JSON file describing one patient and one test
hypothesis (e.g. "will the agent book an appointment on a day the office is
closed?"). Keeping scenarios as data — not code — makes it trivial to add
new edge cases without touching the pipeline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


@dataclass
class Scenario:
    id: str
    title: str
    goal: str
    hypothesis: str
    bug_class: str
    identity: dict[str, str]
    opening_line: str
    edge_behavior: str = ""
    wrap_up_when: str = "your goal is resolved one way or the other"
    voice_id: str = ""  # optional per-scenario TTS voice; falls back to the env default
    raw: dict[str, Any] = field(default_factory=dict)


def load_scenario(scenario_id: str) -> Scenario:
    path = SCENARIOS_DIR / f"{scenario_id}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No scenario {scenario_id!r}. Available: {', '.join(list_scenarios())}"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return Scenario(
        id=data["id"],
        title=data["title"],
        goal=data["goal"],
        hypothesis=data["hypothesis"],
        bug_class=data["bug_class"],
        identity=data["identity"],
        opening_line=data["opening_line"],
        edge_behavior=data.get("edge_behavior", ""),
        wrap_up_when=data.get("wrap_up_when", "your goal is resolved one way or the other"),
        raw=data,
    )


def list_scenarios() -> list[str]:
    if not SCENARIOS_DIR.exists():
        return []
    return sorted(p.stem for p in SCENARIOS_DIR.glob("*.json"))


def build_system_prompt(scenario: Scenario) -> str:
    """Compose the persona prompt that drives the patient LLM.

    The prompt is tuned for *voice*: short turns, one idea at a time, natural
    pacing, and active steering toward the test goal — then a clean goodbye.
    """
    ident = scenario.identity
    identity_lines = "\n".join(f"- {k.replace('_', ' ').title()}: {v}" for k, v in ident.items())
    edge = f"\nEdge behavior for this call:\n{scenario.edge_behavior}\n" if scenario.edge_behavior else ""

    return f"""You are role-playing a real patient phoning a medical clinic's phone line.
You are the CALLER. The clinic voice agent always speaks first; you simply
respond to whatever it says, in character. You are NOT an assistant; you are a person with a reason to call.

Your identity (use these consistently if asked to verify):
{identity_lines}

Your goal for this call:
{scenario.goal}

How to behave on a phone call (this matters most):
- Speak in short, natural turns — one idea at a time, the way people actually talk.
- Never read a list or monologue. Say a sentence or two, then wait for a reply.
- Answer the agent's questions (name, date of birth, etc.) using your identity above.
- Keep steering back toward your goal if the conversation drifts.
- Use natural filler occasionally ("um", "okay", "got it") but stay clear.
- Do not narrate stage directions or describe yourself. Just talk.
{edge}
Wrapping up:
- When {scenario.wrap_up_when}, thank the agent, say a short goodbye, and then
  call the end_call function. Do not keep the conversation going forever.

Stay in character as the patient at all times. Never describe what you are doing or
that you are waiting (for example, never say things like "I'll wait for the agent").
Your first words must be a normal patient reply to whatever the agent just said."""
