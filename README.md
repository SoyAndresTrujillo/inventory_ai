# Inventory + AI

Inventory management where products, categories and templates can be handled either
through the UI or by chatting with an AI assistant (text, photos, Excel, CSV, XML,
JSON, PDF, or voice dictation).

Scope of this MVP: `docs/first_idea.md`.

## Stack

| Piece    | Choice                                              |
| -------- | --------------------------------------------------- |
| Frontend | Next.js 16 (App Router) + Tailwind v4, `frontend/`   |
| Backend  | FastAPI + psycopg 3, `backend/`                     |
| Database | Postgres 17 in Docker, `docker-compose.yml`         |
| AI       | Pluggable: Ollama (default), OpenAI, Anthropic — `backend/app/ai/` |

## Run

```bash
# 1. database
docker compose up -d

# 2. backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # defaults to local Ollama, no key needed
.venv/bin/uvicorn app.main:app --reload --port 8000

# 3. frontend
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

The schema is created on backend startup (`backend/app/schema.sql`). API docs at
http://localhost:8000/docs.

The default provider is local Ollama, so `ollama serve` must be running with the
model pulled:

```bash
ollama pull glm-4.7-flash:latest
```

Smoke tests (need the database up; no model is called):

```bash
backend/.venv/bin/python backend/test_repo.py
backend/.venv/bin/python backend/test_ai.py
```

## Modules

**Categories** — the attributes that describe a product (Country, State, City, Brand…).
Create them first; they show up as fields in the product form.

**Products** — name, SKU, price, quantity, description, plus one value per category.

**Templates** — a reusable product skeleton: which categories to fill in and default
values. Picking a template in the product form narrows the fields and prefills defaults.

**AI** — chat that creates, updates and deletes products, one at a time or in bulk.
It reads text, Excel, CSV, XML and JSON (plus images and PDF on vision-capable
providers), asks a question when data is missing or ambiguous, and ends with a summary
of what it created, updated or deleted. Voice input uses the browser's Web Speech API
(Chrome/Edge), so audio is transcribed before it reaches the server.

## AI providers

`AI_PROVIDER` in `backend/.env` picks the adapter. Nothing else in the app changes.

| Value       | Runs on                          | Notes                                   |
| ----------- | -------------------------------- | --------------------------------------- |
| `ollama`    | local, `glm-4.7-flash:latest`    | default, no cost, no key, text only     |
| `openai`    | OpenAI API                       | set `OPENAI_API_KEY` + `OPENAI_MODEL`   |
| `anthropic` | Anthropic API                    | set `ANTHROPIC_API_KEY`                 |

Structure (`backend/app/ai/`):

```
tools.py               system prompt + tool registry (JSON Schema + repo calls)
base.py                the port every adapter implements, file parsing
openai_provider.py     Adapter — serves Ollama and OpenAI (base_url differs)
anthropic_provider.py  Adapter — Messages API wire shape
__init__.py            PROVIDERS registry, picks one by env
```

**Adapter** pattern: each SDK has an incompatible shape (`parameters` + `tool_calls`
vs `input_schema` + `tool_use` blocks); each adapter translates to the same port.
**Strategy** is the same code seen from `chat.py` — interchangeable, chosen at runtime.
Adding a provider is one adapter plus one line in `PROVIDERS`; the tools and the prompt
never change.

Images and PDFs are rejected with an explicit error when the selected model can't read
them (`AI_VISION=1` overrides), rather than being silently dropped.

## API

| Method | Path                | Purpose                              |
| ------ | ------------------- | ------------------------------------ |
| GET    | `/categories`       | List categories                      |
| POST   | `/categories`       | Create category                      |
| DELETE | `/categories/{id}`  | Delete (blocked while in use)        |
| GET    | `/products`         | List, `?search=` filters             |
| POST   | `/products`         | Create                               |
| PATCH  | `/products/{id}`    | Partial update                       |
| DELETE | `/products/{id}`    | Delete                               |
| GET    | `/templates`        | List templates                       |
| POST   | `/templates`        | Create / overwrite by name           |
| DELETE | `/templates/{id}`   | Delete                               |
| POST   | `/chat`             | One AI turn (multipart: `message`, `history`, `files`) |

The AI tools call the same `backend/app/repo.py` functions the REST routes use, so
both paths enforce the same rules.

## Not built yet

Invoices, payments, payment reminders, stock in/out movements and reports — listed as
context in `docs/first_idea.md`, outside the MVP scope. Also no auth or multi-tenancy:
anyone reaching the backend can read and write everything.
