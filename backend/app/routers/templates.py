from fastapi import APIRouter

from .. import repo
from ..models import TemplateIn

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("")
def list_templates():
    return repo.list_templates()


@router.post("", status_code=201)
def create_template(body: TemplateIn):
    return repo.create_template(body.name, body.categories, body.defaults)


@router.delete("/{template_id}")
def delete_template(template_id: int):
    return repo.delete_template(template_id)
