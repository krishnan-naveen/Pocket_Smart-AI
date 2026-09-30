"""Public pages: landing page, testimonials, health check."""
from fastapi import APIRouter, Request

from .. import gemini_service
from ..config import get_settings
from ..templating import render

router = APIRouter()

# Sample stories written for this demo project (not real customers).
TESTIMONIALS = [
    {"name": "Sample user - Priya, Chennai", "text": "Planned my living room makeover under Rs 40,000 and it split the budget across furniture, lighting and decor.", "tag": "Home"},
    {"name": "Sample user - Arun, Salem", "text": "Got a full birthday party plan for 30 guests with venue, food and decor that stayed inside my budget.", "tag": "Party"},
    {"name": "Sample user - Meera, Coimbatore", "text": "I uploaded my saree photo and the jewelry suggestions actually matched the colours.", "tag": "Jewelry"},
]


@router.get("/")
async def index(request: Request):
    return render(request, "index.html")


@router.get("/testimonials")
async def testimonials(request: Request):
    return render(request, "testimonials.html", testimonials=TESTIMONIALS)


@router.get("/health")
async def health():
    s = get_settings()
    return {"status": "ok", "gemini_configured": gemini_service.is_configured(), "model": s.gemini_model}
