"use client";

import { useEffect, useState } from "react";
import { api, type Category } from "@/lib/api";

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  const load = () => api.categories.list().then(setCategories).catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await api.categories.create(name);
      setName("");
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function remove(id: number) {
    setError("");
    try {
      await api.categories.remove(id);
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Categories</h1>
        <p className="mt-1 text-sm text-muted">
          Attributes that describe a product — Country, State, City, Brand, and so on.
        </p>
      </div>

      <form onSubmit={submit} className="card flex gap-3">
        <input
          className="input"
          required
          placeholder="Category name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button className="btn whitespace-nowrap">Add</button>
      </form>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="card">
        {categories.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted">No categories yet.</p>
        ) : (
          <ul className="divide-y divide-line">
            {categories.map((category) => (
              <li key={category.id} className="flex items-center justify-between py-3">
                <span className="text-sm">{category.name}</span>
                <button className="btn-ghost" onClick={() => remove(category.id)}>
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
