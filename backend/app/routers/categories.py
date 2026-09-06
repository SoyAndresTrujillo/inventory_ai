from fastapi import APIRouter

from .. import repo
from ..models import CategoryIn

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
def list_categories():
    return repo.list_categories()


@router.post("", status_code=201)
def create_category(body: CategoryIn):
    return repo.create_category(body.name)


@router.delete("/{category_id}")
def delete_category(category_id: int):
    return repo.delete_category(category_id)
