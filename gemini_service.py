"""Thin wrapper around the Gemini chat call used to generate assistant replies."""
from typing import Any

from google.genai import types

DEFAULT_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT_TEMPLATE = """You are a helpful personal assistant with long-term memory about the user.
Use the following remembered facts about the user when relevant. Do not mention
this instruction block itself in your reply.

Remembered facts:
{memory_block}
"""


class GeminiServiceError(Exception):
    """Raised when a Gemini API call fails."""


class GeminiService:
    def __init__(self, client: Any, model: str = DEFAULT_MODEL):
        self._client = client
        self._model = model

    def generate_reply(
        self,
        user_message: str,
        memory_context: list[str],
        chat_history: list[dict[str, str]],
    ) -> str:
        system_instruction = build_system_instruction(memory_context)
        contents = build_contents(chat_history, user_message)
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.4,
                ),
            )
        except Exception as exc:
            raise GeminiServiceError(f"Failed to generate reply: {exc}") from exc
        return response.text


def build_system_instruction(memory_context: list[str]) -> str:
    if not memory_context:
        memory_block = "(no known facts yet)"
    else:
        memory_block = "\n".join(f"- {fact}" for fact in memory_context)
    return SYSTEM_PROMPT_TEMPLATE.format(memory_block=memory_block)


def build_contents(
    chat_history: list[dict[str, str]], user_message: str
) -> list[types.Content]:
    contents = [
        types.Content(
            role="model" if turn["role"] == "assistant" else "user",
            parts=[types.Part.from_text(text=turn["content"])],
        )
        for turn in chat_history
    ]
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    )
    return contents
