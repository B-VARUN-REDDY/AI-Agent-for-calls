"""The live patient voice pipeline: Twilio audio -> STT -> LLM -> TTS -> Twilio.

Design choices that matter for voice quality:
- The bot LISTENS FIRST. We never queue an opening line, so the clinic agent
  greets and we respond — like a real caller.
- Short, natural turns are enforced by the persona prompt (see scenarios.py).
- An `end_call` tool lets the patient LLM hang up once its goal is resolved,
  instead of looping forever.

pipecat-ai import paths shift between releases; if one fails, reconcile it with
the version in requirements.txt. The offline transcript/analysis tooling does
not depend on any of this.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import WebSocket

from . import config
from .scenarios import build_system_prompt, load_scenario

TRANSCRIPTS_DIR = Path(__file__).resolve().parent.parent / "transcripts"


def _write_transcript(call_sid: str, scenario_id: str, turns: list) -> None:
    """Write the speaker-labeled, timestamped transcript captured during the call."""
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for elapsed, speaker, text in turns:
        if not text:
            continue
        minutes, secs = divmod(int(elapsed), 60)
        lines.append(f"[{minutes}:{secs:02d}] {speaker}: {text}")
    path = TRANSCRIPTS_DIR / f"{scenario_id}_{call_sid}.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[transcript] wrote {path} ({len(lines)} turns)")


async def run_bot(websocket: WebSocket) -> None:
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.processors.transcript_processor import TranscriptProcessor
    from pipecat.serializers.twilio import TwilioFrameSerializer
    from pipecat.services.anthropic.llm import AnthropicLLMService
    from pipecat.services.deepgram.stt import DeepgramSTTService
    from pipecat.transports.websocket.fastapi import (
        FastAPIWebsocketParams,
        FastAPIWebsocketTransport,
    )

    # ---- Read Twilio's opening frames to learn the stream + our parameters ---
    messages = websocket.iter_text()
    await messages.__anext__()  # "connected"
    start = json.loads(await messages.__anext__())  # "start"
    stream_sid = start["start"]["streamSid"]
    call_sid = start["start"]["callSid"]
    params = start["start"].get("customParameters", {})
    scenario = load_scenario(params.get("scenario", "simple_scheduling"))

    serializer = TwilioFrameSerializer(
        stream_sid=stream_sid,
        call_sid=call_sid,
        account_sid=config.TWILIO_ACCOUNT_SID,
        auth_token=config.TWILIO_AUTH_TOKEN,
    )

    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(),
            serializer=serializer,
        ),
    )

    stt = DeepgramSTTService(
        api_key=config.DEEPGRAM_API_KEY,
        sample_rate=config.TELEPHONY_SAMPLE_RATE,
    )
    # TTS provider is config-driven so you can A/B Cartesia vs ElevenLabs after
    # a real call by flipping TTS_PROVIDER in .env — no code change.
    if config.TTS_PROVIDER == "elevenlabs":
        from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

        tts = ElevenLabsTTSService(
            api_key=config.ELEVENLABS_API_KEY,
            voice_id=config.ELEVENLABS_VOICE_ID,
            model=config.ELEVENLABS_MODEL,
            sample_rate=config.TELEPHONY_SAMPLE_RATE,
        )
    else:
        from pipecat.services.cartesia.tts import CartesiaTTSService

        tts = CartesiaTTSService(
            api_key=config.CARTESIA_API_KEY,
            voice_id=config.CARTESIA_VOICE_ID,
            model=config.CARTESIA_MODEL,
            sample_rate=config.TELEPHONY_SAMPLE_RATE,
        )
    llm = AnthropicLLMService(
        api_key=config.ANTHROPIC_API_KEY,
        model=config.PATIENT_LLM_MODEL,
    )

    # The end_call tool: the patient decides when the scenario is done.
    tools = [
        {
            "name": "end_call",
            "description": "End the phone call after you have said goodbye.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Why the call is ending."}
                },
                "required": ["reason"],
            },
        }
    ]

    async def end_call(params):  # pipecat passes a FunctionCallParams object
        await params.result_callback({"status": "ended"})
        await task.cancel()

    llm.register_function("end_call", end_call)

    context = OpenAILLMContext(
        messages=[{"role": "system", "content": build_system_prompt(scenario)}],
        tools=tools,
    )
    context_aggregator = llm.create_context_aggregator(context)

    # Capture a speaker-labeled transcript live: the agent (Athena) arrives via
    # STT as role "user"; our patient bot's speech is role "assistant".
    transcript = TranscriptProcessor()
    turns: list = []
    t0 = time.monotonic()

    @transcript.event_handler("on_transcript_update")
    async def _on_transcript(processor, frame):
        for msg in frame.messages:
            speaker = "Agent" if msg.role == "user" else "Patient"
            turns.append((time.monotonic() - t0, speaker, (msg.content or "").strip()))

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            transcript.user(),
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            transcript.assistant(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=config.TELEPHONY_SAMPLE_RATE,
            audio_out_sample_rate=config.TELEPHONY_SAMPLE_RATE,
            allow_interruptions=True,
        ),
    )

    # Listen-first: no opening frame is queued. We wait for the agent to speak.
    runner = PipelineRunner(handle_sigint=False)
    try:
        await runner.run(task)
    finally:
        _write_transcript(call_sid, scenario.id, turns)
