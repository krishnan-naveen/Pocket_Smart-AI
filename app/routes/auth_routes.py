"""/register, /login, /logout, /token  (+ /session-info, /session-data)"""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from .. import auth, database
from ..config import get_settings
from ..templating import render

router = APIRouter()


def _set_cookie(resp, token: str) -> None:
    resp.set_cookie(auth.COOKIE_NAME, token, httponly=True, samesite="lax",
                    max_age=get_settings().token_minutes * 60)


@router.get("/register")
async def register_page(request: Request):
    return render(request, "register.html")


@router.post("/register")
async def register(request: Request, username: str = Form(""), email: str = Form(""), password: str = Form("")):
    username, email = username.strip(), email.strip()
    error = auth.validate_registration(username, email, password)
    if error:
        return render(request, "register.html", error=error, form={"username": username, "email": email}, status_code=400)
    if not database.create_user(username, email, auth.hash_password(password)):
        return render(request, "register.html", error="That username is already taken.",
                      form={"username": username, "email": email}, status_code=409)
    return RedirectResponse("/login?registered=1", status_code=303)


@router.get("/login")
async def login_page(request: Request, registered: int = 0):
    if auth.get_optional_user(request):
        return RedirectResponse("/dashboard", status_code=303)
    return render(request, "login.html", success="Account created! Please log in." if registered else None)


@router.post("/login")
async def login(request: Request, username: str = Form(""), password: str = Form("")):
    user = auth.authenticate(username.strip(), password)
    if not user:
        return render(request, "login.html", error="Invalid username or password.",
                      form={"username": username}, status_code=401)
    resp = RedirectResponse("/dashboard", status_code=303)
    _set_cookie(resp, auth.create_access_token(user["id"], user["username"]))
    return resp


@router.get("/logout")
@router.post("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(auth.COOKIE_NAME)
    return resp


@router.post("/token")
async def token(form: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password flow: returns a JWT for API clients (use as 'Authorization: Bearer <token>')."""
    user = auth.authenticate(form.username, form.password)
    if not user:
        raise HTTPException(401, "Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": auth.create_access_token(user["id"], user["username"]), "token_type": "bearer"}


@router.get("/session-info")
async def session_info(user: dict | None = Depends(auth.get_optional_user)):
    if not user:
        return {"logged_in": False}
    return {"logged_in": True, "user_id": user["id"], "username": user["username"]}


@router.get("/session-data")
async def session_data(user: dict = Depends(auth.get_current_user)):
    history = database.list_history(user["id"], limit=200)
    by_cat: dict[str, int] = {}
    for h in history:
        by_cat[h["category"]] = by_cat.get(h["category"], 0) + 1
    last = history[0] if history else None
    return {
        "user_id": user["id"], "username": user["username"], "member_since": user["created_at"],
        "total_recommendations": len(history), "by_category": by_cat,
        "last_recommendation": {"id": last["id"], "category": last["category"], "budget": last["budget"],
                                "created_at": last["created_at"]} if last else None,
    }
