"""Voxa's LiveKit Agents entry point."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    TurnHandlingOptions,
    cli,
    inference,
    room_io,
)
from livekit.agents.llm import function_tool

from voxa.tools import format_local_time

load_dotenv()

logger = logging.getLogger("voxa")


class VoxaAgent(Agent):
    """Friendly voice assistant with session-scoped conversational context."""

    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are Voxa, a friendly, professional, and helpful voice assistant. "
                "Speak naturally and keep answers concise unless the user asks for detail. "
                "Use the active conversation to answer follow-up questions. Do not claim to "
                "remember conversations after this session ends. If you are unsure, say so. "
                "When asked for the current date or time, call get_current_time instead of "
                "guessing. Speak in plain conversational language without markdown or emoji."
            )
        )

    async def on_enter(self) -> None:
        self.session.generate_reply(
            instructions="Greet the user, introduce yourself as Voxa, and invite a question."
        )

    @function_tool
    async def get_current_time(self, context: RunContext) -> str:
        """Return the current date and time in the machine's local timezone."""
        try:
            return format_local_time()
        except Exception:
            logger.exception("Could not read the local system time")
            return "I'm unable to read the current local time right now."


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    """Start one isolated voice conversation for this LiveKit room session."""
    ctx.log_context_fields = {"room": ctx.room.name}

    missing = [
        name
        for name in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")
        if not os.getenv(name)
    ]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing) + ". "
            "Copy .env.example to .env and add your LiveKit project credentials."
        )

    session = AgentSession(
        stt=inference.STT("deepgram/flux-general", language="en"),
        llm=inference.LLM("google/gemma-4-31b-it"),
        tts=inference.TTS(
            "cartesia/sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
        turn_handling=TurnHandlingOptions(
            interruption={
                "resume_false_interruption": True,
                "false_interruption_timeout": 1.0,
            },
            preemptive_generation={"enabled": True, "max_retries": 3},
        ),
        aec_warmup_duration=3.0,
    )

    try:
        await session.start(
            agent=VoxaAgent(),
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions()
            ),
        )
    except Exception:
        logger.exception("Voxa could not start the voice session")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli.run_app(server)
