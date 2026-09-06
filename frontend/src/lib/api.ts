const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Category = { id: number; name: string };

export type Product = {
  id: number;
  name: string;
  sku: string | null;
  description: string | null;
  price: number;
  quantity: number;
  attributes: Record<string, string>;
};

export type Template = {
  id: number;
  name: string;
  categories: string[];
  defaults: Record<string, unknown>;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers:
      init?.body instanceof FormData
        ? init.headers
        : { "content-type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  categories: {
    list: () => request<Category[]>("/categories"),
    create: (name: string) =>
      request<Category>("/categories", { method: "POST", body: JSON.stringify({ name }) }),
    remove: (id: number) => request<Category>(`/categories/${id}`, { method: "DELETE" }),
  },
  products: {
    list: (search = "") =>
      request<Product[]>(`/products${search ? `?search=${encodeURIComponent(search)}` : ""}`),
    create: (body: Partial<Product>) =>
      request<Product>("/products", { method: "POST", body: JSON.stringify(body) }),
    update: (id: number, body: Partial<Product>) =>
      request<Product>(`/products/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    remove: (id: number) => request<Product>(`/products/${id}`, { method: "DELETE" }),
  },
  templates: {
    list: () => request<Template[]>("/templates"),
    create: (body: { name: string; categories: string[]; defaults: Record<string, unknown> }) =>
      request<Template>("/templates", { method: "POST", body: JSON.stringify(body) }),
    remove: (id: number) => request<Template>(`/templates/${id}`, { method: "DELETE" }),
  },
  chat: (message: string, history: { role: string; content: string }[], files: File[]) => {
    const form = new FormData();
    form.append("message", message);
    form.append("history", JSON.stringify(history));
    files.forEach((f) => form.append("files", f));
    return request<{ reply: string; provider: string }>("/chat", { method: "POST", body: form });
  },
};
