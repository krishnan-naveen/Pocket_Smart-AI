"""/generate-home, /generate-party, /generate-jewelry, /recommendations-details, /history.

The three generate-* endpoints accept a JSON body (or multipart form for jewelry with an image)
and return the recommendation JSON. They also save the result to the user's history.
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from .. import auth, database, planners
from ..products import (HOME_ROOMS, HOME_STYLES, JEWELRY_OCCASIONS, JEWELRY_STYLES, PARTY_EVENTS)
from ..templating import render

router = APIRouter()


def _validation_message(exc: ValidationError) -> str:
    parts = []
    for e in exc.errors():
        field = ".".join(str(x) for x in e["loc"]) or "input"
        msg = e["msg"].replace("Value error, ", "")
        parts.append(f"{field}: {msg}")
    return "; ".join(parts)


def _run(category: str, req, user: dict, image: Optional[bytes] = None, mime: Optional[str] = None) -> dict:
    try:
        result = planners.run_planner(category, req, image, mime)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    result["history_id"] = database.save_history(
        user["id"], category, req.budget, req.model_dump(), result, result["source"]
    )
    return result


def _parse(model, data: dict):
    try:
        return model(**data)
    except ValidationError as exc:
        raise HTTPException(422, _validation_message(exc))


# ------------------------------------------------------------------ API endpoints
@router.post("/generate-home")
async def generate_home(payload: dict, user: dict = Depends(auth.get_current_user)):
    return _run("home", _parse(planners.HomeRequest, payload), user)


@router.post("/generate-party")
async def generate_party(payload: dict, user: dict = Depends(auth.get_current_user)):
    return _run("party", _parse(planners.PartyRequest, payload), user)


@router.post("/generate-jewelry")
async def generate_jewelry(
    budget: float = Form(...), occasion: str = Form(...), style: str = Form("modern"),
    outfit: str = Form(""), notes: str = Form(""),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(auth.get_current_user),
):
    req = _parse(planners.JewelryRequest, {"budget": budget, "occasion": occasion, "style": style,
                                            "outfit": outfit, "notes": notes})
    data, mime = None, None
    if image is not None and image.filename:
        data = await image.read()
        try:
            mime = planners.validate_image(data)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
    return _run("jewelry", req, user, data, mime)


@router.get("/recommendations-details")
async def recommendations_details(category: str, budget: float, preference: str = "",
                                  user: dict = Depends(auth.get_current_user)):
    """Detailed recommendations for a category using a single 'preference' word
    (room / event type / occasion). Does not need a full form - handy for API clients."""
    cat = category.lower()
    if cat == "home":
        room = preference if preference in HOME_ROOMS else "living room"
        req = _parse(planners.HomeRequest, {"budget": budget, "room": room})
    elif cat == "party":
        ev = preference if preference in PARTY_EVENTS else "birthday"
        req = _parse(planners.PartyRequest, {"budget": budget, "event_type": ev, "guests": 20})
    elif cat == "jewelry":
        oc = preference if preference in JEWELRY_OCCASIONS else "party"
        req = _parse(planners.JewelryRequest, {"budget": budget, "occasion": oc})
    else:
        raise HTTPException(422, "category must be one of: home, party, jewelry")
    return _run(cat, req, user)


@router.get("/history")
async def history_api(user: dict = Depends(auth.get_current_user)):
    return [{"id": h["id"], "category": h["category"], "budget": h["budget"], "source": h["source"],
             "created_at": h["created_at"], "total_cost": h["result"].get("total_cost")}
            for h in database.list_history(user["id"])]


# ------------------------------------------------------------------ HTML pages
def _need_login(request: Request):
    user = auth.get_optional_user(request)
    return user, (None if user else RedirectResponse("/login", status_code=303))


@router.get("/dashboard")
async def dashboard(request: Request):
    user, redirect = _need_login(request)
    if redirect:
        return redirect
    hist = database.list_history(user["id"], limit=5)
    total = len(database.list_history(user["id"], limit=1000))
    return render(request, "dashboard.html", recent=hist, total=total)


@router.get("/history-page")
async def history_page(request: Request):
    user, redirect = _need_login(request)
    if redirect:
        return redirect
    return render(request, "history.html", items=database.list_history(user["id"]))


@router.get("/history/{item_id}")
async def history_item(request: Request, item_id: int):
    user, redirect = _need_login(request)
    if redirect:
        return redirect
    item = database.get_history_item(user["id"], item_id)
    if not item:
        raise HTTPException(404, "Recommendation not found.")
    return render(request, f"{item['category']}_recommendations.html", result=item["result"], req=item["request"])


@router.get("/home-planner")
async def home_planner(request: Request):
    user, redirect = _need_login(request)
    return redirect or render(request, "home_planner.html", rooms=HOME_ROOMS, styles=HOME_STYLES)


@router.get("/party-planner")
async def party_planner(request: Request):
    user, redirect = _need_login(request)
    return redirect or render(request, "party_planner.html", events=PARTY_EVENTS)


@router.get("/jewelry-planner")
async def jewelry_planner(request: Request):
    user, redirect = _need_login(request)
    return redirect or render(request, "jewelry_planner.html", occasions=JEWELRY_OCCASIONS, styles=JEWELRY_STYLES)
