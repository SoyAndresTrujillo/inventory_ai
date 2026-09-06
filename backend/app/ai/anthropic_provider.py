"""Adapter for the Anthropic Messages API.

Same tools, different wire shape: input_schema instead of parameters, tool_use
content blocks instead of tool_calls, tool results in a user turn.
"""

import base64
import json
from typing import Any

import anthropic

from . import tools
from .base import MAX_ITERATIONS, AIError, Attachment, Message, check_supported


class AnthropicProvider:
    supports_images = True

    def __init__(self, name: str, model: str, api_key: str, timeout: float = 600.0) -> None:
        if not api_key:
            raise AIError("ANTHROPIC_API_KEY is not set. Add it to backend/.env and restart.")
        self.name = name
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout)

    def _schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools.TOOLS
        ]

    def _user_content(self, message: str, attachments: list[Attachment]) -> Any:
        blocks: list[dict[str, Any]] = []
        for attachment in attachments:
            if attachment.kind == "text":
                blocks.append(
                    {
                        "type": "text",
                        "text": f"Attached file {attachment.filename}:\n{attachment.text}",
                    }
                )
            else:
                blocks.append(
                    {
                        "type": "image" if attachment.kind == "image" else "document",
                        "source": {
                            "type": "base64",
                            "media_type": attachment.media_type,
                            "data": base64.b64encode(attachment.data).decode(),
                        },
                    }
                )
        if message.strip():
            blocks.append({"type": "text", "text": message})
        return blocks

    def run(self, history: list[Message], message: str, attachments: list[Attachment]) -> str:
        check_supported(self, attachments)

        messages: list[dict[str, Any]] = [
            {"role": m.role, "content": m.content} for m in history
        ]
        messages.append({"role": "user", "content": self._user_content(message, attachments)})

        for _ in range(MAX_ITERATIONS):
            try:
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=16000,
                    system=tools.SYSTEM,
                    tools=self._schemas(),
                    messages=messages,
                )
            except anthropic.APIStatusError as exc:
                raise AIError(f"{self.name} error {exc.status_code}: {exc.message}") from exc
            except anthropic.APIConnectionError as exc:
                raise AIError("Could not reach the Anthropic API.") from exc

            if response.stop_reason == "refusal":
                return "The request was declined by the model's safety system."

            calls = [block for block in response.content if block.type == "tool_use"]
            if not calls:
                return "\n".join(
                    block.text for block in response.content if block.type == "text"
                ).strip()

            messages.append({"role": "assistant", "content": response.content})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": call.id,
                            "content": tools.run(
                                call.name,
                                call.input if isinstance(call.input, dict) else json.loads(call.input),
                            ),
                        }
                        for call in calls
                    ],
                }
            )

        return (
            f"Stopped after {MAX_ITERATIONS} tool steps without finishing. "
            "Split the request into smaller batches."
        )
