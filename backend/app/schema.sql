create table if not exists categories (
    id          serial primary key,
    name        text not null unique,
    created_at  timestamptz not null default now()
);

create table if not exists products (
    id          serial primary key,
    name        text not null,
    sku         text unique,
    description text,
    price       numeric(12, 2) not null default 0,
    quantity    integer not null default 0,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- One value per (product, category): "Country" -> "Colombia", "Brand" -> "Bosch".
create table if not exists product_attributes (
    product_id  integer not null references products (id) on delete cascade,
    category_id integer not null references categories (id) on delete restrict,
    value       text not null,
    primary key (product_id, category_id)
);

-- A template is a reusable product skeleton: which categories to fill in,
-- plus default field values.
create table if not exists templates (
    id           serial primary key,
    name         text not null unique,
    category_ids integer[] not null default '{}',
    defaults     jsonb not null default '{}'::jsonb,
    created_at   timestamptz not null default now()
);
