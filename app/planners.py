"""Planner logic: input validation, rule-based budget engine, Gemini prompts, and result assembly.

Flow for every planner:
    validated request -> candidate products (mock catalog) -> Gemini picks & explains (JSON)
        -> we VERIFY the picks (real ids, within budget) -> otherwise rule-based fallback.
Gemini never invents products or prices: it can only choose from the candidate list we give it.
"""
import io
from typing import Literal, Optional

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, field_validator

from . import gemini_service
from .config import get_settings
from .gemini_service import GeminiUnavailable
from .products import (
    CATALOGS, HOME_ROOMS, HOME_STYLES, JEWELRY_OCCASIONS, JEWELRY_STYLES, PARTY_EVENTS,
)

MIN_BUDGET = 500
MAX_BUDGET = 10_000_000


# ------------------------------------------------------------------ request models
class _Base(BaseModel):
    budget: float = Field(..., description="Total budget in INR")
    notes: str = Field("", max_length=500)

    @field_validator("budget")
    @classmethod
    def _budget_range(cls, v: float) -> float:
        if not (MIN_BUDGET <= v <= MAX_BUDGET):
            raise ValueError(f"Budget must be between Rs {MIN_BUDGET:,} and Rs {MAX_BUDGET:,}.")
        return v


class HomeRequest(_Base):
    room: Literal["living room", "bedroom", "kitchen", "study"]
    style: Literal["modern", "minimal", "traditional", "cozy"] = "modern"
    quantity: int = Field(1, ge=1, le=5, description="How many such rooms to furnish")


class PartyRequest(_Base):
    event_type: Literal["birthday", "wedding", "anniversary", "housewarming", "baby shower", "corporate"]
    guests: int = Field(..., ge=1, le=500)
    veg_only: bool = False


class JewelryRequest(_Base):
    occasion: Literal["wedding", "festival", "party", "office", "casual"]
    style: Literal["traditional", "modern", "boho"] = "modern"
    outfit: str = Field("", max_length=300, description="Text description of the outfit")


# ------------------------------------------------------------------ image validation
ALLOWED_IMAGE_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


def validate_image(data: bytes) -> str:
    """Returns the MIME type or raises ValueError with a user-friendly message."""
    if len(data) > get_settings().max_image_bytes:
        raise ValueError("Image is too large (max 5 MB).")
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
            fmt = img.format
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise ValueError("Uploaded file is not a valid image.")
    if fmt not in ALLOWED_IMAGE_FORMATS:
        raise ValueError("Only JPG, PNG or WEBP images are supported.")
    return ALLOWED_IMAGE_FORMATS[fmt]


# ------------------------------------------------------------------ candidates & pricing
def _unit_cost(item: dict, req) -> float:
    if item["unit"] == "per_person":
        return item["price"] * req.guests
    return item["price"]


def _budget_for_selection(category: str, req) -> float:
    """Budget available for one 'unit' of the plan (home: per room)."""
    if category == "home":
        return req.budget / req.quantity
    return req.budget


def candidates_for(category: str, req) -> list[dict]:
    items = CATALOGS[category]
    if category == "home":
        pool = [i for i in items if req.room in i["tags"]]
    elif category == "party":
        pool = [i for i in items if req.event_type in i["tags"]]
        if req.veg_only:
            pool = [i for i in pool if "non-veg" not in i["name"].lower()]
        pool = [i for i in pool if i.get("capacity", 10**9) >= req.guests]
    else:
        pool = [i for i in items if req.occasion in i["tags"]]
    return pool


def _relevance(item: dict, category: str, req) -> int:
    score = 0
    if category == "home":
        score += 2 * (req.style in item["tags"])
    elif category == "jewelry":
        score += 2 * (req.style in item["tags"])
        outfit = (req.outfit + " " + req.notes).lower()
        score += sum(1 for t in item["tags"] if t in outfit)
    return score


# ------------------------------------------------------------------ rule-based engine (fallback)
def rule_based_pick(category: str, req, pool: list[dict]) -> list[str]:
    """Greedy, budget-respecting selection. Deterministic and explainable (used when Gemini fails)."""
    budget = _budget_for_selection(category, req)
    ranked = sorted(pool, key=lambda i: (-_relevance(i, category, req), _unit_cost(i, req)))
    picked: list[dict] = []
    remaining = budget

    def take(item: dict) -> bool:
        nonlocal remaining
        cost = _unit_cost(item, req)
        if cost <= remaining and item not in picked:
            picked.append(item)
            remaining -= cost
            return True
        return False

    if category == "party":
        # Must-haves first: the best venue and food that fit inside a share of the budget.
        for cat, share in (("venue", 0.35), ("food", 0.55)):
            opts = [i for i in ranked if i["category"] == cat and _unit_cost(i, req) <= budget * share]
            opts = opts or [i for i in ranked if i["category"] == cat]
            opts.sort(key=lambda i: -_unit_cost(i, req))  # spend the share on the best option that fits
            for it in opts:
                if take(it):
                    break
        for it in ranked:
            if it["category"] == "decor":
                take(it)
    else:
        # One item from each category first (variety), then fill the leftover budget.
        seen_cats: set[str] = set()
        for it in ranked:
            if it["category"] not in seen_cats and take(it):
                seen_cats.add(it["category"])
        for it in ranked:
            take(it)
    return [i["id"] for i in picked]


# ------------------------------------------------------------------ prompts
def _describe_request(category: str, req) -> str:
    if category == "home":
        return (f"Room: {req.room}. Style: {req.style}. Number of such rooms: {req.quantity}. "
                f"Budget PER ROOM: Rs {req.budget / req.quantity:,.0f} (total Rs {req.budget:,.0f}).")
    if category == "party":
        return (f"Event: {req.event_type}. Guests: {req.guests}. Vegetarian only: {req.veg_only}. "
                f"Total budget: Rs {req.budget:,.0f}. A party normally needs one venue, one food option and some decor.")
    return (f"Occasion: {req.occasion}. Preferred style: {req.style}. Outfit description: {req.outfit or 'not given'}. "
            f"Total budget: Rs {req.budget:,.0f}.")


def build_prompt(category: str, req, pool: list[dict], has_image: bool) -> str:
    lines = [
        f'- id="{i["id"]}" | {i["name"]} | {i["category"]} | {i["platform"]} | '
        f'Rs {_unit_cost(i, req):,.0f}{" (per-person price x guests)" if i["unit"] == "per_person" else ""} | tags: {", ".join(i["tags"])}'
        for i in pool
    ]
    image_rule = (
        "An image of the user's outfit is attached. First describe the outfit (colours, neckline, formality) in "
        '"outfit_analysis", then choose jewelry that matches it.\n' if has_image else ""
    )
    return f"""You are PocketSmart AI, a careful budget-shopping assistant for Indian users. All prices are in INR.

USER REQUEST ({category} planner):
{_describe_request(category, req)}
Extra notes from user: {req.notes or 'none'}

{image_rule}CANDIDATE PRODUCTS (you may ONLY choose from this list, never invent products or prices):
{chr(10).join(lines)}

RULES:
1. Choose the best combination of candidate products for the user's needs.
2. The SUM of the chosen items' prices must NOT exceed the budget ({'per room budget' if category == 'home' else 'total budget'}: Rs {_budget_for_selection(category, req):,.0f}).
3. Prefer variety across categories over many items of one category.
4. Write each reason in at most 20 words, specific to this user.
5. Reply with ONLY valid JSON in exactly this shape:
{{"summary": "2-3 sentence overview of the plan", "outfit_analysis": "string or empty", "picks": [{{"id": "candidate id", "reason": "why this fits"}}], "tips": ["1-3 short money-saving tips"]}}"""


# ------------------------------------------------------------------ result assembly
def _line_item(item: dict, req, reason: str, category: str) -> dict:
    qty = req.guests if item["unit"] == "per_person" else 1
    cost = _unit_cost(item, req)
    if category == "home":
        cost_total = cost * req.quantity
    else:
        cost_total = cost
    return {
        "name": item["name"], "category": item["category"], "platform": item["platform"],
        "unit_price": item["price"], "unit": item["unit"], "quantity": qty * (req.quantity if category == "home" else 1),
        "cost": cost_total, "reason": reason, "url": item["url"],
    }


def _fallback_reason(item: dict, category: str, req) -> str:
    if category == "home":
        return f"A {item['category']} essential for a {req.style} {req.room}, chosen to fit the budget."
    if category == "party":
        return f"Covers the {item['category']} needs of a {req.event_type} for {req.guests} guests within budget."
    return f"A {item['category']} piece suited to a {req.occasion} occasion in {req.style} style."


def _verify_picks(raw_picks, pool: list[dict], req, category: str) -> list[tuple[dict, str]]:
    """Keep only real candidate ids, drop duplicates, then drop the last items until within budget."""
    by_id = {i["id"]: i for i in pool}
    chosen: list[tuple[dict, str]] = []
    seen: set[str] = set()
    for p in raw_picks if isinstance(raw_picks, list) else []:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id", ""))
        if pid in by_id and pid not in seen:
            seen.add(pid)
            chosen.append((by_id[pid], str(p.get("reason", "")).strip()[:200]))
    limit = _budget_for_selection(category, req)
    while chosen and sum(_unit_cost(i, req) for i, _ in chosen) > limit:
        chosen.pop()
    return chosen


def run_planner(category: str, req, image: Optional[bytes] = None, image_mime: Optional[str] = None) -> dict:
    pool = candidates_for(category, req)
    result_meta = {"source": "fallback", "model": None, "warning": None, "outfit_analysis": ""}
    summary, tips = "", []
    chosen: list[tuple[dict, str]] = []

    if not pool:
        raise ValueError("No matching products found for these choices. Try a different option.")

    try:
        data, model = gemini_service.generate_json(
            build_prompt(category, req, pool, has_image=bool(image)), image, image_mime
        )
        chosen = _verify_picks(data.get("picks"), pool, req, category)
        if not chosen:
            raise GeminiUnavailable("Gemini picks were empty, invalid or over budget.")
        summary = str(data.get("summary", "")).strip()[:600]
        tips = [str(t)[:160] for t in (data.get("tips") or [])][:3] if isinstance(data.get("tips"), list) else []
        result_meta.update(source="gemini", model=model, outfit_analysis=str(data.get("outfit_analysis", ""))[:500])
    except GeminiUnavailable as exc:
        result_meta["warning"] = (
            "AI service unavailable, showing rule-based recommendations instead. "
            f"({str(exc)[:200]})"
        )

    if not chosen:  # fallback path
        by_id = {i["id"]: i for i in pool}
        chosen = [(by_id[i], _fallback_reason(by_id[i], category, req)) for i in rule_based_pick(category, req, pool)]
        summary = (
            f"Best-fit picks for your Rs {req.budget:,.0f} budget, chosen by PocketSmart's built-in budget rules."
        )
        tips = ["Compare prices across platforms before buying.", "Buy bulky items during sale seasons to save more."]

    for i, (item, reason) in enumerate(chosen):
        if not reason:
            chosen[i] = (item, _fallback_reason(item, category, req))

    items = [_line_item(i, req, r, category) for i, r in chosen]
    total = round(sum(x["cost"] for x in items), 2)
    return {
        "category": category,
        "budget": req.budget,
        "summary": summary,
        "items": items,
        "total_cost": total,
        "remaining": round(req.budget - total, 2),
        "tips": tips,
        "note": "Prices and links are simulated for this demo project.",
        **result_meta,
    }
