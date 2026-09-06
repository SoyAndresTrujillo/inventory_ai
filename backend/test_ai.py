"""Smoke test for the AI module's provider-neutral parts. No model is called.

    docker compose up -d && backend/.venv/bin/python backend/test_ai.py
"""

import json
import uuid

from app import ai, repo
from app.ai import tools
from app.ai.base import Attachment, check_supported
from app.db import init_schema, pool

SUFFIX = uuid.uuid4().hex[:8]


def main() -> None:
    pool.open(wait=True)
    init_schema()

    # every tool exposes a usable JSON Schema
    for tool in tools.TOOLS:
        assert tool.name and tool.description, tool
        assert tool.parameters["type"] == "object", tool.name
        assert tool.parameters["additionalProperties"] is False, tool.name

    # both adapters translate the same registry into their own wire shape
    openai_adapter = ai.PROVIDERS["ollama"]()
    assert {s["function"]["name"] for s in openai_adapter._schemas()} == set(tools.BY_NAME)
    from app.ai.anthropic_provider import AnthropicProvider

    claude_adapter = AnthropicProvider(name="anthropic", model="claude-opus-5", api_key="test")
    assert {s["name"] for s in claude_adapter._schemas()} == set(tools.BY_NAME)
    assert "input_schema" in claude_adapter._schemas()[0], "Anthropic uses input_schema"

    # tools execute against the real database
    category = json.loads(tools.run("create_category", {"name": f"Country {SUFFIX}"}))
    created = json.loads(
        tools.run(
            "create_product",
            {
                "name": f"Drill {SUFFIX}",
                "sku": f"AI-{SUFFIX}",
                "price": 89.9,
                "quantity": 5,
                "attributes": {category["name"]: "Colombia"},
            },
        )
    )
    assert created["attributes"] == {category["name"]: "Colombia"}

    # every failure comes back as text the model can react to, never as an exception
    assert tools.run("nope", {}).startswith("ERROR: unknown tool")
    assert tools.run("create_product", {"nope": 1}).startswith("ERROR: wrong arguments")
    assert tools.run("delete_product", {"product_id": 10**9}).startswith("ERROR: Product")
    assert "Unknown category" in tools.run(
        "create_product", {"name": "x", "attributes": {"NoSuchCategory": "y"}}
    )

    # unsupported input fails loudly instead of being dropped
    try:
        check_supported(openai_adapter, [Attachment("image", "photo.png", media_type="image/png")])
        raise AssertionError("image on a text-only provider must raise")
    except ai.AIError as exc:
        assert "cannot read images" in str(exc)

    try:
        ai._provider("gemini")
        raise AssertionError("unknown provider must raise")
    except ai.AIError as exc:
        assert "Unknown AI_PROVIDER" in str(exc)

    tools.run("delete_product", {"product_id": created["id"]})
    repo.delete_category(category["id"])
    print("ok")


if __name__ == "__main__":
    main()
