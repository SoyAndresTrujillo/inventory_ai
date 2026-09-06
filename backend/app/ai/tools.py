"""The agent's contract: system prompt + the tools it can call.

Provider neutral on purpose. Schemas are plain JSON Schema, bodies call repo.py
directly, so every provider adapter shares one definition of what the AI can do.
"""

import json
from dataclasses import dataclass
from typing import Any, Callable

from .. import repo

SYSTEM = """You are the inventory assistant for an inventory management app.

You can create, update and delete products, and create categories, one at a time
or in bulk. Products are described by categories (e.g. Country, State, City, Brand)
and each product holds one value per category.

Rules:
- Use the tools for every change. Never claim a change you did not make with a tool.
- A product needs at least a name. If the user's input is missing something required
  or is ambiguous (which product to update, which of two similar names they mean,
  a price that could be a quantity), ask a short question instead of guessing.
- Attribute values must use categories that already exist. If a needed category is
  missing, ask the user whether to create it, then use create_category.
- For bulk work, call the tools repeatedly - one call per product.
- Read attached files, spreadsheets and images as product data.
- Finish every turn that changed data with a short summary report listing what was
  created, updated and deleted, one line per product, and note anything you skipped
  and why.
- Stay inside product/category/template management. Decline unrelated requests."""


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    fn: Callable[..., Any]


def _obj(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


ATTRIBUTES = {
    "type": "object",
    "additionalProperties": {"type": "string"},
    "description": (
        'Category name to value, e.g. {"Country": "Colombia", "Brand": "Bosch"}. '
        "Every category name must already exist."
    ),
}

TOOLS: list[Tool] = [
    Tool(
        name="list_categories",
        description="List all existing categories (the attributes products can be described by).",
        parameters=_obj({}),
        fn=lambda: repo.list_categories(),
    ),
    Tool(
        name="create_category",
        description="Create a category, e.g. Country, State, City, Brand.",
        parameters=_obj({"name": {"type": "string", "description": "Category name."}}, ["name"]),
        fn=lambda name: repo.create_category(name),
    ),
    Tool(
        name="list_products",
        description="List products, optionally filtered by a text search on name, SKU or description.",
        parameters=_obj(
            {
                "search": {
                    "type": "string",
                    "description": "Free text filter. Omit to get the most recent products.",
                }
            }
        ),
        fn=lambda search="": repo.list_products(search or None),
    ),
    Tool(
        name="create_product",
        description="Create one product.",
        parameters=_obj(
            {
                "name": {"type": "string", "description": "Product name. Required."},
                "sku": {"type": "string", "description": "Unique stock keeping unit code."},
                "description": {"type": "string"},
                "price": {"type": "number", "description": "Unit price."},
                "quantity": {"type": "integer", "description": "Units in stock."},
                "attributes": ATTRIBUTES,
            },
            ["name"],
        ),
        fn=lambda name, sku="", description="", price=0, quantity=0, attributes=None: repo.create_product(
            name=name,
            sku=sku or None,
            description=description or None,
            price=price,
            quantity=quantity,
            attributes=attributes or {},
        ),
    ),
    Tool(
        name="update_product",
        description="Update one product. Only the fields you pass are changed.",
        parameters=_obj(
            {
                "product_id": {
                    "type": "integer",
                    "description": "Id of the product. Use list_products to find it.",
                },
                "name": {"type": "string"},
                "sku": {"type": "string"},
                "description": {"type": "string"},
                "price": {"type": "number"},
                "quantity": {"type": "integer"},
                "attributes": {
                    **ATTRIBUTES,
                    "description": ATTRIBUTES["description"]
                    + " Replaces the whole set, so include the values you want to keep.",
                },
            },
            ["product_id"],
        ),
        fn=lambda product_id, name="", sku="", description="", price=None, quantity=None, attributes=None: repo.update_product(
            product_id,
            name=name or None,
            sku=sku or None,
            description=description or None,
            price=price,
            quantity=quantity,
            attributes=attributes,
        ),
    ),
    Tool(
        name="delete_product",
        description="Delete one product permanently.",
        parameters=_obj(
            {
                "product_id": {
                    "type": "integer",
                    "description": "Id of the product. Use list_products to find it.",
                }
            },
            ["product_id"],
        ),
        fn=lambda product_id: repo.delete_product(product_id),
    ),
    Tool(
        name="list_templates",
        description="List product templates (reusable sets of categories and default values).",
        parameters=_obj({}),
        fn=lambda: repo.list_templates(),
    ),
]

BY_NAME = {tool.name: tool for tool in TOOLS}


def run(name: str, arguments: dict[str, Any]) -> str:
    """Execute one tool call. Every failure comes back as text the model can act on."""
    tool = BY_NAME.get(name)
    if tool is None:
        return f"ERROR: unknown tool '{name}'. Available: {', '.join(BY_NAME)}"
    if not isinstance(arguments, dict):
        return f"ERROR: arguments for '{name}' must be a JSON object"
    try:
        return json.dumps(tool.fn(**arguments), default=str)
    except (repo.Invalid, repo.NotFound) as exc:
        return f"ERROR: {exc}"
    except TypeError as exc:
        return f"ERROR: wrong arguments for '{name}': {exc}"
