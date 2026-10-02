"""PocketSmart AI - FastAPI entry point.

Run:  python -m app.main      (or)      uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import database
from .config import get_settings
from .routes import auth_routes, planner_routes, public_routes
from .templating import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables and warn (never crash) if the Gemini key is missing."""
    database.init_db()
    s = get_settings()
    if not s.gemini_api_key:
        print("[startup] WARNING: GEMINI_API_KEY not set - the app will use rule-based fallback recommendations.")
    else:
        print(f"[startup] Gemini configured. Primary model: {s.gemini_model}")
    yield


app = FastAPI(title="PocketSmart AI", description="Smart budget & recommendation assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=get_settings().static_dir), name="static")

app.include_router(public_routes.router)
app.include_router(auth_routes.router)
app.include_router(planner_routes.router)


def _wants_html(request: Request) -> bool:
    return "text/html" in request.headers.get("accept", "") and not request.url.path.startswith(
        ("/generate-", "/session-", "/token", "/history", "/recommendations-details"))


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401 and _wants_html(request):
        return RedirectResponse("/login", status_code=303)
    if _wants_html(request):
        return render(request, "error.html", status_code=exc.status_code, message=exc.detail)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    msg = "; ".join(f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in exc.errors())
    return JSONResponse({"detail": msg or "Invalid input."}, status_code=422)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
