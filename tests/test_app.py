"""Automated tests. Run with:  python -m pytest -v
Gemini is never called for real here: it is either unset (fallback path) or replaced by a fake."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import gemini_service, planners


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-that-is-long-enough-123456")
    from app.main import app
    with TestClient(app) as c:
        yield c


def register_and_login(c, username="kani", password="secret12"):
    r = c.post("/register", data={"username": username, "email": f"{username}@example.com", "password": password},
               follow_redirects=False)
    assert r.status_code == 303
    r = c.post("/login", data={"username": username, "password": password}, follow_redirects=False)
    assert r.status_code == 303 and "access_token" in r.headers.get("set-cookie", "")


def png_bytes(color=(200, 30, 60)):
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buf, "PNG")
    return buf.getvalue()


# ---------------------------------------------------------------- pages & auth
def test_public_pages(client):
    for path in ["/", "/testimonials", "/login", "/register", "/health"]:
        assert client.get(path).status_code == 200


def test_protected_pages_redirect_to_login(client):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert client.get("/generate-home").status_code in (401, 405)


def test_register_validation_and_duplicate(client):
    r = client.post("/register", data={"username": "a", "email": "bad", "password": "1"})
    assert r.status_code == 400
    register_and_login(client)
    r = client.post("/register", data={"username": "kani", "email": "x@y.com", "password": "secret12"})
    assert r.status_code == 409


def test_login_wrong_password(client):
    register_and_login(client)
    client.get("/logout")
    r = client.post("/login", data={"username": "kani", "password": "wrongpass"})
    assert r.status_code == 401 and "Invalid username or password" in r.text


def test_token_endpoint_and_bearer_auth(client):
    register_and_login(client)
    client.cookies.clear()
    r = client.post("/token", data={"username": "kani", "password": "secret12"})
    assert r.status_code == 200
    tok = r.json()["access_token"]
    assert client.get("/session-info").json() == {"logged_in": False}
    info = client.get("/session-info", headers={"Authorization": f"Bearer {tok}"}).json()
    assert info["logged_in"] and info["username"] == "kani"
    assert client.post("/token", data={"username": "kani", "password": "nope"}).status_code == 401


def test_logout_clears_session(client):
    register_and_login(client)
    assert client.get("/session-info").json()["logged_in"]
    client.get("/logout")
    assert not client.get("/session-info").json()["logged_in"]


# ---------------------------------------------------------------- planners (fallback path, no Gemini key)
def test_home_fallback_within_budget(client):
    register_and_login(client)
    r = client.post("/generate-home", json={"room": "living room", "style": "modern", "quantity": 1, "budget": 50000})
    assert r.status_code == 200
    d = r.json()
    assert d["source"] == "fallback" and d["warning"]
    assert d["items"] and d["total_cost"] <= 50000
    assert {i["category"] for i in d["items"]} >= {"furniture", "decor", "lighting"}


def test_home_quantity_multiplies_cost_and_respects_total_budget(client):
    register_and_login(client)
    d = client.post("/generate-home", json={"room": "bedroom", "quantity": 3, "budget": 90000}).json()
    assert d["total_cost"] <= 90000
    assert all(i["quantity"] == 3 for i in d["items"])


def test_party_plan_has_venue_food_and_stays_in_budget(client):
    register_and_login(client)
    d = client.post("/generate-party", json={"event_type": "birthday", "guests": 30, "budget": 40000}).json()
    cats = {i["category"] for i in d["items"]}
    assert {"venue", "food"} <= cats
    assert d["total_cost"] <= 40000
    food = next(i for i in d["items"] if i["category"] == "food")
    assert food["cost"] == food["unit_price"] * 30


def test_party_veg_only_excludes_nonveg(client):
    register_and_login(client)
    d = client.post("/generate-party", json={"event_type": "birthday", "guests": 20, "budget": 60000, "veg_only": True}).json()
    assert all("non-veg" not in i["name"].lower() for i in d["items"])


def test_jewelry_with_image_upload(client):
    register_and_login(client)
    r = client.post("/generate-jewelry", data={"budget": "8000", "occasion": "wedding", "style": "traditional",
                                               "outfit": "red silk saree"},
                    files={"image": ("outfit.png", png_bytes(), "image/png")})
    assert r.status_code == 200
    assert r.json()["total_cost"] <= 8000


def test_jewelry_rejects_non_image(client):
    register_and_login(client)
    r = client.post("/generate-jewelry", data={"budget": "8000", "occasion": "party"},
                    files={"image": ("x.png", b"not an image", "image/png")})
    assert r.status_code == 422 and "valid image" in r.json()["detail"]


# ---------------------------------------------------------------- input validation
@pytest.mark.parametrize("payload", [
    {"room": "living room", "budget": 10},                  # below minimum
    {"room": "living room", "budget": -5000},               # negative
    {"room": "garage", "budget": 20000},                    # unknown room
    {"room": "living room", "budget": "abc"},               # not a number
    {"room": "living room", "budget": 20000, "quantity": 0},
])
def test_home_invalid_input_rejected(client, payload):
    register_and_login(client)
    assert client.post("/generate-home", json=payload).status_code == 422


def test_party_invalid_guests(client):
    register_and_login(client)
    assert client.post("/generate-party", json={"event_type": "birthday", "guests": 0, "budget": 20000}).status_code == 422
    assert client.post("/generate-party", json={"event_type": "birthday", "guests": 9999, "budget": 20000}).status_code == 422


def test_very_low_budget_returns_empty_or_small_plan_without_crashing(client):
    register_and_login(client)
    r = client.post("/generate-home", json={"room": "study", "budget": 500})
    assert r.status_code == 200 and r.json()["total_cost"] <= 500


def test_planner_requires_login(client):
    assert client.post("/generate-home", json={"room": "bedroom", "budget": 20000}).status_code == 401


# ---------------------------------------------------------------- Gemini path (faked)
def _fake(monkeypatch, data, model="fake-model"):
    monkeypatch.setattr(gemini_service, "generate_json", lambda *a, **k: (data, model))


def test_gemini_picks_used_when_valid(client, monkeypatch):
    register_and_login(client)
    _fake(monkeypatch, {"summary": "Nice plan", "picks": [{"id": "h1", "reason": "Comfy sofa"}, {"id": "h6", "reason": "Soft light"}],
                        "tips": ["Wait for sale"]})
    d = client.post("/generate-home", json={"room": "living room", "budget": 40000}).json()
    assert d["source"] == "gemini" and d["model"] == "fake-model"
    assert [i["name"] for i in d["items"]] == ["3-seater fabric sofa", "Arc floor lamp"]
    assert d["summary"] == "Nice plan"


def test_gemini_hallucinated_ids_are_dropped(client, monkeypatch):
    register_and_login(client)
    _fake(monkeypatch, {"picks": [{"id": "zzz", "reason": "fake"}, {"id": "h2", "reason": "ok"}]})
    d = client.post("/generate-home", json={"room": "living room", "budget": 40000}).json()
    assert d["source"] == "gemini" and len(d["items"]) == 1 and d["items"][0]["name"] == "Compact coffee table"


def test_gemini_over_budget_is_trimmed(client, monkeypatch):
    register_and_login(client)
    _fake(monkeypatch, {"picks": [{"id": "h1", "reason": "a"}, {"id": "h3", "reason": "b"}, {"id": "h6", "reason": "c"}]})
    d = client.post("/generate-home", json={"room": "living room", "budget": 26000}).json()
    assert d["total_cost"] <= 26000 and d["source"] == "gemini"


def test_gemini_all_invalid_falls_back(client, monkeypatch):
    register_and_login(client)
    _fake(monkeypatch, {"picks": [{"id": "nope"}]})
    d = client.post("/generate-home", json={"room": "living room", "budget": 40000}).json()
    assert d["source"] == "fallback" and d["items"]


def test_gemini_error_falls_back(client, monkeypatch):
    register_and_login(client)

    def boom(*a, **k):
        raise gemini_service.GeminiUnavailable("quota exceeded")
    monkeypatch.setattr(gemini_service, "generate_json", boom)
    d = client.post("/generate-party", json={"event_type": "wedding", "guests": 50, "budget": 150000}).json()
    assert d["source"] == "fallback" and "quota exceeded" in d["warning"]


def test_json_parser_handles_code_fences_and_garbage():
    assert gemini_service._parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert gemini_service._parse_json('Sure! {"a": 2} hope that helps') == {"a": 2}
    with pytest.raises(gemini_service.GeminiUnavailable):
        gemini_service._parse_json("no json here")


# ---------------------------------------------------------------- history & session data
def test_history_saved_and_user_isolated(client):
    register_and_login(client)
    hid = client.post("/generate-home", json={"room": "kitchen", "budget": 20000}).json()["history_id"]
    assert client.get("/history").json()[0]["id"] == hid
    assert client.get(f"/history/{hid}").status_code == 200
    assert "Home Interior Recommendations" in client.get(f"/history/{hid}").text
    sd = client.get("/session-data").json()
    assert sd["total_recommendations"] == 1 and sd["by_category"] == {"home": 1}
    # another user cannot open it
    client.get("/logout")
    register_and_login(client, username="other")
    assert client.get(f"/history/{hid}").status_code == 404
    assert client.get("/history").json() == []


def test_recommendations_details_endpoint(client):
    register_and_login(client)
    r = client.get("/recommendations-details", params={"category": "party", "budget": 30000, "preference": "birthday"})
    assert r.status_code == 200 and r.json()["category"] == "party"
    assert client.get("/recommendations-details", params={"category": "cars", "budget": 30000}).status_code == 422


def test_all_pages_render_after_login(client):
    register_and_login(client)
    for p in ["/dashboard", "/home-planner", "/party-planner", "/jewelry-planner", "/history-page"]:
        assert client.get(p).status_code == 200, p


def test_image_validator():
    assert planners.validate_image(png_bytes()) == "image/png"
    with pytest.raises(ValueError):
        planners.validate_image(b"junk")
