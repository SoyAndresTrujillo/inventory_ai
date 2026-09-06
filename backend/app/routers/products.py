from fastapi import APIRouter

from .. import repo
from ..models import ProductIn, ProductPatch

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def list_products(search: str | None = None, limit: int = 200):
    return repo.list_products(search, limit)


@router.get("/{product_id}")
def get_product(product_id: int):
    return repo.get_product(product_id)


@router.post("", status_code=201)
def create_product(body: ProductIn):
    return repo.create_product(**body.model_dump())


@router.patch("/{product_id}")
def update_product(product_id: int, body: ProductPatch):
    return repo.update_product(product_id, **body.model_dump(exclude_unset=True))


@router.delete("/{product_id}")
def delete_product(product_id: int):
    return repo.delete_product(product_id)
