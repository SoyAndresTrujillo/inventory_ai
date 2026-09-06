"""All database access. Shared by the REST routers and the AI tools."""

from typing import Any

from psycopg.types.json import Jsonb

from .db import pool

PRODUCT_SELECT = """
    select p.id, p.name, p.sku, p.description, p.price, p.quantity,
           p.created_at, p.updated_at,
           coalesce(
               jsonb_object_agg(c.name, pa.value) filter (where c.id is not null),
               '{}'::jsonb
           ) as attributes
    from products p
    left join product_attributes pa on pa.product_id = p.id
    left join categories c on c.id = pa.category_id
"""


class NotFound(Exception):
    pass


class Invalid(Exception):
    pass


# --- categories ---------------------------------------------------------


def list_categories() -> list[dict[str, Any]]:
    with pool.connection() as conn:
        return conn.execute("select * from categories order by name").fetchall()


def create_category(name: str) -> dict[str, Any]:
    name = name.strip()
    if not name:
        raise Invalid("Category name cannot be empty")
    with pool.connection() as conn:
        row = conn.execute(
            """insert into categories (name) values (%s)
               on conflict (name) do update set name = excluded.name
               returning *""",
            (name,),
        ).fetchone()
    return row


def delete_category(category_id: int) -> dict[str, Any]:
    with pool.connection() as conn:
        in_use = conn.execute(
            "select 1 from product_attributes where category_id = %s limit 1",
            (category_id,),
        ).fetchone()
        if in_use:
            raise Invalid("Category is used by at least one product")
        row = conn.execute(
            "delete from categories where id = %s returning *", (category_id,)
        ).fetchone()
    if row is None:
        raise NotFound(f"Category {category_id} not found")
    return row


# --- products -----------------------------------------------------------


def list_products(search: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    sql = PRODUCT_SELECT
    params: list[Any] = []
    if search:
        sql += " where p.name ilike %s or p.sku ilike %s or p.description ilike %s"
        params += [f"%{search}%"] * 3
    sql += " group by p.id order by p.id desc limit %s"
    params.append(limit)
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchall()


def get_product(product_id: int) -> dict[str, Any]:
    with pool.connection() as conn:
        row = conn.execute(
            PRODUCT_SELECT + " where p.id = %s group by p.id", (product_id,)
        ).fetchone()
    if row is None:
        raise NotFound(f"Product {product_id} not found")
    return row


def _apply_attributes(conn, product_id: int, attributes: dict[str, str]) -> None:
    """Replace a product's attributes. Category names must already exist."""
    rows = conn.execute("select id, name from categories").fetchall()
    known = {r["name"].lower(): r["id"] for r in rows}
    resolved = {}
    for raw_name, value in attributes.items():
        category_id = known.get(raw_name.strip().lower())
        if category_id is None:
            names = ", ".join(sorted(r["name"] for r in rows)) or "(none)"
            raise Invalid(
                f"Unknown category '{raw_name}'. "
                f"Existing categories: {names}. "
                "Create the category first."
            )
        resolved[category_id] = str(value)

    conn.execute("delete from product_attributes where product_id = %s", (product_id,))
    for category_id, value in resolved.items():
        conn.execute(
            "insert into product_attributes (product_id, category_id, value) values (%s, %s, %s)",
            (product_id, category_id, value),
        )


def create_product(
    name: str,
    sku: str | None = None,
    description: str | None = None,
    price: float = 0,
    quantity: int = 0,
    attributes: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not name or not name.strip():
        raise Invalid("Product name is required")
    with pool.connection() as conn:
        existing = (
            conn.execute("select id from products where sku = %s", (sku,)).fetchone()
            if sku
            else None
        )
        if existing:
            raise Invalid(f"SKU '{sku}' already exists (product {existing['id']})")
        row = conn.execute(
            """insert into products (name, sku, description, price, quantity)
               values (%s, %s, %s, %s, %s) returning id""",
            (name.strip(), sku, description, price, quantity),
        ).fetchone()
        _apply_attributes(conn, row["id"], attributes or {})
    return get_product(row["id"])


def update_product(
    product_id: int,
    name: str | None = None,
    sku: str | None = None,
    description: str | None = None,
    price: float | None = None,
    quantity: int | None = None,
    attributes: dict[str, str] | None = None,
) -> dict[str, Any]:
    fields = {
        "name": name,
        "sku": sku,
        "description": description,
        "price": price,
        "quantity": quantity,
    }
    fields = {k: v for k, v in fields.items() if v is not None}
    with pool.connection() as conn:
        if conn.execute(
            "select 1 from products where id = %s", (product_id,)
        ).fetchone() is None:
            raise NotFound(f"Product {product_id} not found")
        if fields:
            assignments = ", ".join(f"{k} = %s" for k in fields)
            conn.execute(
                f"update products set {assignments}, updated_at = now() where id = %s",
                [*fields.values(), product_id],
            )
        if attributes is not None:
            _apply_attributes(conn, product_id, attributes)
    return get_product(product_id)


def delete_product(product_id: int) -> dict[str, Any]:
    product = get_product(product_id)
    with pool.connection() as conn:
        conn.execute("delete from products where id = %s", (product_id,))
    return product


# --- templates ----------------------------------------------------------


def list_templates() -> list[dict[str, Any]]:
    with pool.connection() as conn:
        return conn.execute(
            """select t.*,
                      coalesce(
                          (select array_agg(c.name order by c.name)
                           from categories c where c.id = any (t.category_ids)),
                          '{}'
                      ) as categories
               from templates t order by t.name"""
        ).fetchall()


def create_template(
    name: str, categories: list[str], defaults: dict[str, Any] | None = None
) -> dict[str, Any]:
    if not name or not name.strip():
        raise Invalid("Template name is required")
    with pool.connection() as conn:
        known = {
            r["name"].lower(): r["id"]
            for r in conn.execute("select id, name from categories").fetchall()
        }
        ids = []
        for raw_name in categories:
            category_id = known.get(raw_name.strip().lower())
            if category_id is None:
                raise Invalid(f"Unknown category '{raw_name}'. Create it first.")
            ids.append(category_id)
        row = conn.execute(
            """insert into templates (name, category_ids, defaults)
               values (%s, %s, %s)
               on conflict (name) do update
                   set category_ids = excluded.category_ids,
                       defaults = excluded.defaults
               returning id""",
            (name.strip(), ids, Jsonb(defaults or {})),
        ).fetchone()
    return next(t for t in list_templates() if t["id"] == row["id"])


def delete_template(template_id: int) -> dict[str, Any]:
    with pool.connection() as conn:
        row = conn.execute(
            "delete from templates where id = %s returning *", (template_id,)
        ).fetchone()
    if row is None:
        raise NotFound(f"Template {template_id} not found")
    return row
