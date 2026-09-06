"""Smoke test for the repo layer. Needs the Postgres container running.

    docker compose up -d && backend/.venv/bin/python backend/test_repo.py
"""

import uuid

from app import repo
from app.db import init_schema, pool

SUFFIX = uuid.uuid4().hex[:8]


def main() -> None:
    pool.open(wait=True)
    init_schema()

    country = repo.create_category(f"Country {SUFFIX}")
    brand = repo.create_category(f"Brand {SUFFIX}")
    assert repo.create_category(country["name"])["id"] == country["id"], "should upsert"

    product = repo.create_product(
        name=f"Drill {SUFFIX}",
        sku=f"DR-{SUFFIX}",
        price=89.9,
        quantity=12,
        attributes={country["name"].lower(): "Colombia", brand["name"]: "Bosch"},
    )
    assert product["attributes"] == {country["name"]: "Colombia", brand["name"]: "Bosch"}

    updated = repo.update_product(product["id"], quantity=20)
    assert updated["quantity"] == 20 and updated["name"] == product["name"]
    assert updated["attributes"] == product["attributes"], "attributes survive a partial update"

    try:
        repo.create_product(name="x", attributes={"NoSuchCategory": "y"})
        raise AssertionError("unknown category must be rejected")
    except repo.Invalid:
        pass
    assert not repo.list_products(search="NoSuchCategory"), "failed create must roll back"

    try:
        repo.create_product(name="dup", sku=product["sku"])
        raise AssertionError("duplicate SKU must be rejected")
    except repo.Invalid:
        pass

    template = repo.create_template(
        f"Power tool {SUFFIX}", [country["name"], brand["name"]], {"quantity": 1}
    )
    assert sorted(template["categories"]) == sorted([country["name"], brand["name"]])

    try:
        repo.delete_category(country["id"])
        raise AssertionError("category in use must not be deletable")
    except repo.Invalid:
        pass

    repo.delete_product(product["id"])
    try:
        repo.get_product(product["id"])
        raise AssertionError("deleted product must be gone")
    except repo.NotFound:
        pass

    repo.delete_template(template["id"])
    repo.delete_category(country["id"])
    repo.delete_category(brand["id"])
    print("ok")


if __name__ == "__main__":
    main()
