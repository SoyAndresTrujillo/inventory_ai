"""Adapter for any OpenAI-compatible chat completions API.

Serves both Ollama (local, http://localhost:11434/v1) and OpenAI itself - the
difference is base_url, model and api_key, which is config, not code.
"""

import base64
import json
from typing import Any

import openai

from . import tools
from .base import MAX_ITERATIONS, AIError, Attachment, Message, check_supported


class OpenAICompatProvider:
    def __init__(
        self,
        name: str,
        model: str,
        api_key: str,
        base_url: str | None = None,
        supports_images: bool = False,
        timeout: float = 600.0,
    ) -> None:
        if not model:
            raise AIError(f"No model configured for AI_PROVIDER={name}. Set it in backend/.env.")
        self.name = name
        self.model = model
        self.supports_images = supports_images
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def _schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools.TOOLS
        ]

    def _user_content(self, message: str, attachments: list[Attachment]) -> Any:
        parts: list[dict[str, Any]] = []
        text = message
        for attachment in attachments:
            if attachment.kind == "text":
                text = f"Attached file {attachment.filename}:\n{attachment.text}\n\n{text}"
            elif attachment.kind == "image":
                encoded = base64.b64encode(attachment.data).decode()
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{attachment.media_type};base64,{encoded}"},
                    }
                )
            elif attachment.kind == "pdf":
                encoded = base64.b64encode(attachment.data).decode()
                parts.append(
                    {
                        "type": "file",
                        "file": {
                            "filename": attachment.filename,
                            "file_data": f"data:application/pdf;base64,{encoded}",
                        },
                    }
                )
        if not parts:
            return text
        return [{"type": "text", "text": text}, *parts]

    def run(self, history: list[Message], message: str, attachments: list[Attachment]) -> str:
        check_supported(self, attachments)

        messages: list[dict[str, Any]] = [{"role": "system", "content": tools.SYSTEM}]
        messages += [{"role": m.role, "content": m.content} for m in history]
        messages.append({"role": "user", "content": self._user_content(message, attachments)})

        for _ in range(MAX_ITERATIONS):
            try:
                response = self._client.chat.completions.create(
                    model=self.model, messages=messages, tools=self._schemas()
                )
            except openai.APIStatusError as exc:
                raise AIError(f"{self.name} error {exc.status_code}: {exc.message}") from exc
            except openai.APIConnectionError as exc:
                raise AIError(
                    f"Could not reach {self.name} at {self._client.base_url}. Is it running?"
                ) from exc

            choice = response.choices[0].message
            calls = choice.tool_calls or []
            if not calls:
                return (choice.content or "").strip()

            messages.append(
                {
                    "role": "assistant",
                    "content": choice.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in calls
                    ],
                }
            )

            for call in calls:
                try:
                    arguments = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    result = f"ERROR: arguments for '{call.function.name}' were not valid JSON"
                else:
                    result = tools.run(call.function.name, arguments)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

        return (
            f"Stopped after {MAX_ITERATIONS} tool steps without finishing. "
            "Split the request into smaller batches."
        )
