from typing import Any

from pydantic import BaseModel, Field


class CategoryIn(BaseModel):
    name: str


class ProductIn(BaseModel):
    name: str
    sku: str | None = None
    description: str | None = None
    price: float = 0
    quantity: int = 0
    attributes: dict[str, str] = Field(default_factory=dict)


class ProductPatch(BaseModel):
    name: str | None = None
    sku: str | None = None
    description: str | None = None
    price: float | None = None
    quantity: int | None = None
    attributes: dict[str, str] | None = None


class TemplateIn(BaseModel):
    name: str
    categories: list[str] = Field(default_factory=list)
    defaults: dict[str, Any] = Field(default_factory=dict)
