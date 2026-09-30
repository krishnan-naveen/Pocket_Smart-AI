"""Shared Jinja2 environment and a small render() helper that always passes the current user."""
from fastapi import Request
from fastapi.templating import Jinja2Templates

from . import auth
from .config import get_settings

templates = Jinja2Templates(directory=get_settings().templates_dir)


def inr(value) -> str:
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "₹0"


templates.env.filters["inr"] = inr


def render(request: Request, name: str, status_code: int = 200, **context):
    context.setdefault("user", auth.get_optional_user(request))
    return templates.TemplateResponse(request, name, context, status_code=status_code)
