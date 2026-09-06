"use client";

import { useEffect, useState } from "react";
import { api, type Category, type Product, type Template } from "@/lib/api";

const EMPTY = { name: "", sku: "", description: "", price: "", quantity: "" };

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(EMPTY);
  const [attributes, setAttributes] = useState<Record<string, string>>({});
  const [templateId, setTemplateId] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = (term = search) =>
    api.products.list(term).then(setProducts).catch((e) => setError(e.message));

  useEffect(() => {
    load("");
    api.categories.list().then(setCategories).catch(() => {});
    api.templates.list().then(setTemplates).catch(() => {});
  }, []);

  const template = templates.find((t) => String(t.id) === templateId);
  const shownCategories = template
    ? categories.filter((c) => template.categories.includes(c.name))
    : categories;

  function applyTemplate(id: string) {
    setTemplateId(id);
    const picked = templates.find((t) => String(t.id) === id);
    if (picked) {
      setForm({ ...EMPTY, ...(picked.defaults as Partial<typeof EMPTY>) });
      setAttributes({});
    }
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.products.create({
        name: form.name,
        sku: form.sku || null,
        description: form.description || null,
        price: Number(form.price) || 0,
        quantity: Number(form.quantity) || 0,
        attributes: Object.fromEntries(
          Object.entries(attributes).filter(([, value]) => value.trim()),
        ),
      });
      setForm(EMPTY);
      setAttributes({});
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold tracking-tight">Products</h1>

      <form onSubmit={submit} className="card space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-medium">New product</h2>
          <select
            className="input max-w-52"
            value={templateId}
            onChange={(e) => applyTemplate(e.target.value)}
          >
            <option value="">No template</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid gap-3 sm:grid-cols-4">
          <div className="sm:col-span-2">
            <label className="label">Name</label>
            <input
              className="input"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <label className="label">SKU</label>
            <input
              className="input"
              value={form.sku}
              onChange={(e) => setForm({ ...form, sku: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Price</label>
              <input
                className="input"
                type="number"
                step="0.01"
                min="0"
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Qty</label>
              <input
                className="input"
                type="number"
                min="0"
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: e.target.value })}
              />
            </div>
          </div>
        </div>

        {shownCategories.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-4">
            {shownCategories.map((category) => (
              <div key={category.id}>
                <label className="label">{category.name}</label>
                <input
                  className="input"
                  value={attributes[category.name] ?? ""}
                  onChange={(e) =>
                    setAttributes({ ...attributes, [category.name]: e.target.value })
                  }
                />
              </div>
            ))}
          </div>
        )}

        <div>
          <label className="label">Description</label>
          <input
            className="input"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <button className="btn" disabled={saving}>
          {saving ? "Saving…" : "Create product"}
        </button>
      </form>

      <div className="card space-y-4">
        <input
          className="input"
          placeholder="Search products…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            load(e.target.value);
          }}
        />

        {products.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted">No products yet.</p>
        ) : (
          <ul className="divide-y divide-line">
            {products.map((product) => (
              <li key={product.id} className="flex items-start gap-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {product.name}
                    {product.sku && <span className="ml-2 text-xs text-muted">{product.sku}</span>}
                  </p>
                  <p className="mt-0.5 text-xs text-muted">
                    {Object.entries(product.attributes)
                      .map(([key, value]) => `${key}: ${value}`)
                      .join(" · ") || "No attributes"}
                  </p>
                </div>
                <div className="text-right text-sm">
                  <p>{Number(product.price).toFixed(2)}</p>
                  <p className="text-xs text-muted">{product.quantity} in stock</p>
                </div>
                <button
                  className="btn-ghost"
                  onClick={async () => {
                    await api.products.remove(product.id);
                    load();
                  }}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
