from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import repo
from .ai import AIError
from .db import init_schema, pool
from .routers import categories, chat, products, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True)
    init_schema()
    yield
    pool.close()


app = FastAPI(title="Inventory + AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(repo.NotFound)
async def not_found(request: Request, exc: repo.NotFound):
    return JSONResponse({"detail": str(exc)}, status_code=404)


@app.exception_handler(repo.Invalid)
async def invalid(request: Request, exc: repo.Invalid):
    return JSONResponse({"detail": str(exc)}, status_code=400)


@app.exception_handler(AIError)
async def ai_error(request: Request, exc: AIError):
    return JSONResponse({"detail": str(exc)}, status_code=502)


app.include_router(categories.router)
app.include_router(products.router)
app.include_router(templates.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"ok": True}
