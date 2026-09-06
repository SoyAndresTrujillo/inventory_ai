"use client";

import { useEffect, useState } from "react";
import { api, type Category, type Template } from "@/lib/api";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [name, setName] = useState("");
  const [picked, setPicked] = useState<string[]>([]);
  const [defaults, setDefaults] = useState({ price: "", quantity: "" });
  const [error, setError] = useState("");

  const load = () => api.templates.list().then(setTemplates).catch((e) => setError(e.message));

  useEffect(() => {
    load();
    api.categories.list().then(setCategories).catch(() => {});
  }, []);

  function toggle(categoryName: string) {
    setPicked((current) =>
      current.includes(categoryName)
        ? current.filter((n) => n !== categoryName)
        : [...current, categoryName],
    );
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api.templates.create({
        name,
        categories: picked,
        defaults: Object.fromEntries(
          Object.entries(defaults).filter(([, value]) => value.trim()),
        ),
      });
      setName("");
      setPicked([]);
      setDefaults({ price: "", quantity: "" });
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Templates</h1>
        <p className="mt-1 text-sm text-muted">
          Reusable product skeletons: which categories to fill in, plus default values.
        </p>
      </div>

      <form onSubmit={submit} className="card space-y-4">
        <div>
          <label className="label">Template name</label>
          <input
            className="input"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div>
          <label className="label">Categories</label>
          <div className="flex flex-wrap gap-2">
            {categories.length === 0 && (
              <p className="text-sm text-muted">Create a category first.</p>
            )}
            {categories.map((category) => (
              <button
                type="button"
                key={category.id}
                onClick={() => toggle(category.name)}
                className={`rounded-full border px-3 py-1 text-sm transition ${
                  picked.includes(category.name)
                    ? "border-accent bg-accent text-white"
                    : "border-line text-muted hover:text-foreground"
                }`}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>

        <div className="grid max-w-sm grid-cols-2 gap-3">
          <div>
            <label className="label">Default price</label>
            <input
              className="input"
              type="number"
              step="0.01"
              min="0"
              value={defaults.price}
              onChange={(e) => setDefaults({ ...defaults, price: e.target.value })}
            />
          </div>
          <div>
            <label className="label">Default qty</label>
            <input
              className="input"
              type="number"
              min="0"
              value={defaults.quantity}
              onChange={(e) => setDefaults({ ...defaults, quantity: e.target.value })}
            />
          </div>
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <button className="btn">Save template</button>
      </form>

      <div className="card">
        {templates.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted">No templates yet.</p>
        ) : (
          <ul className="divide-y divide-line">
            {templates.map((template) => (
              <li key={template.id} className="flex items-start justify-between gap-4 py-3">
                <div>
                  <p className="text-sm font-medium">{template.name}</p>
                  <p className="mt-0.5 text-xs text-muted">
                    {template.categories.join(" · ") || "No categories"}
                  </p>
                </div>
                <button
                  className="btn-ghost"
                  onClick={async () => {
                    await api.templates.remove(template.id);
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
