# PocketSmart AI — Project Knowledge

## 1. Project title
**PocketSmart AI: Your Smart Budget & Recommendation Assistant** (Naan Mudhalvan — Google Cloud Generative AI track)

## 2. Problem statement
People planning a purchase (furnishing a room, hosting a party, choosing jewelry) struggle to split a fixed budget across many products and platforms. Browsing Amazon, IKEA, Zomato, OYO etc. one by one is slow, and it is easy to overspend.

## 3. Objective
Build a web application where a logged-in user enters a budget and preferences and receives AI-generated, budget-checked product recommendations for three domains: **Home Interior, Party, Jewelry** (jewelry also accepts an outfit image).

## 4. Proposed solution
1. User registers/logs in (JWT session).
2. User fills a planner form (budget, room/event/occasion, optional notes, optional image).
3. The backend selects matching products from a simulated catalog and asks **Google Gemini** to choose the best combination and explain each pick (JSON output).
4. The backend **verifies** Gemini's answer (real product ids only, total ≤ budget). If Gemini is unavailable or returns something unusable, a **rule-based budget engine** produces the plan instead.
5. The result is shown as cards, saved to the user's history, and can be reopened later.

## 5. Features (all implemented and tested)
| Area | Feature |
|---|---|
| Auth | Register, login, logout, JWT (`/token`), cookie session, `/session-info`, `/session-data` |
| Planners | Home (room, style, quantity), Party (event, guests, veg-only), Jewelry (occasion, style, outfit text + optional image) |
| AI | Gemini text and text+image prompts, JSON output, model fallback chain |
| Budget logic | Total never exceeds budget; per-person pricing × guests; per-room budget × quantity |
| Fallback | Rule-based recommendations when AI fails (Epic 5, story 4) |
| History | `/history` API + History page, reopen any past plan |
| UI | Home, Testimonials, Footer, Register, Login, Dashboard, 3 planner pages, 3 recommendation pages, History; sort/filter with JavaScript |
| Validation | Budget range, enums, guests range, image type/size, text length |

## 6. Architecture
```
Browser (HTML + Jinja2 templates + vanilla JS)
      │  fetch() / form posts
      ▼
FastAPI app  (app/main.py)  ── CORS, static files, exception handlers
  ├─ routes/public_routes.py   /  /testimonials  /health
  ├─ routes/auth_routes.py     /register /login /logout /token /session-info /session-data
  └─ routes/planner_routes.py  /generate-home /generate-party /generate-jewelry
                               /recommendations-details /history  + planner/result pages
        │
        ▼
  planners.py  ── validation → candidates (products.py) → prompt → gemini_service.py → verify picks
        │                                                    │ (on any failure)
        │                                                    ▼
        │                                         rule_based_pick()  (fallback)
        ▼
  database.py (SQLite: users, history)
```

## 7. Technology stack
Python 3.10+, **FastAPI** + Uvicorn, Jinja2 templates, vanilla JavaScript, SQLite (`sqlite3`), PyJWT, PBKDF2 (hashlib), **Google Gen AI SDK (`google-genai`)** calling **Gemini**, Pillow (image validation), pytest + httpx (tests).

## 8. Google Cloud / Generative AI services
* **Gemini API via Google AI Studio API key** — this is what the project page instructs (“Get API key”). No paid Google Cloud service is required.
* Model is configurable in `.env` (`GEMINI_MODEL`, `GEMINI_FALLBACK_MODELS`). The project page mentions “Gemini 1.5 Flash”; Google has since moved to newer model names, so the default is `gemini-3.5-flash` with fallbacks. Check <https://ai.google.dev/gemini-api/docs/models> if a model name stops working.

## 9. Folder structure
```
PocketSmart-AI/
├── app/
│   ├── main.py              FastAPI app, startup, CORS, error handlers, uvicorn entry
│   ├── config.py            Settings from .env
│   ├── auth.py              Password hashing, JWT, current-user dependencies
│   ├── database.py          SQLite tables + queries
│   ├── gemini_service.py    Gemini calls (text + image), JSON parsing, model fallback
│   ├── planners.py          Request models, validation, prompts, verification, rule engine
│   ├── products.py          Simulated catalog (Amazon, IKEA, Zomato, OYO...)
│   ├── templating.py        Jinja2 setup + render helper
│   └── routes/              public_routes.py, auth_routes.py, planner_routes.py
├── templates/               base + 15 pages/partials
├── static/css/style.css, static/js/app.js
├── tests/test_app.py        30 automated tests
├── scripts/test_gemini.py   Gemini connectivity check (text + image)
├── docs/screenshots/        Evidence screenshots
├── .env.example, .gitignore, requirements.txt
└── *.md                     Documentation set
```

## 10. Data flow (one request)
`POST /generate-home {room, budget…}` → Pydantic validation (422 if bad) → `candidates_for()` filters the catalog → `build_prompt()` lists candidates with prices → `gemini_service.generate_json()` → `_verify_picks()` (drop unknown ids, trim to budget) → `save_history()` → JSON response with `history_id` → browser redirects to `/history/{id}` which renders the cards.

## 11. AI workflow
Prompt = role + user request + **candidate list (ids, prices)** + rules + exact JSON schema. Gemini can only *choose* from the list, so it cannot invent products or prices. For jewelry with an image, the image is sent as an extra part and Gemini also returns an `outfit_analysis`. Temperature 0.4, `response_mime_type=application/json`.

## 12. Recommendation workflow (rule-based engine)
* Home/Jewelry: rank by relevance (style/outfit tag match), take one item per category first (variety), then fill leftover budget.
* Party: reserve a share for venue (≤35%) and food (≤55%), then add decor. Venue capacity must cover guests; food price × guests.
* Home `quantity`: selection uses `budget ÷ rooms`; displayed cost is × rooms.

## 13. Database
SQLite file `pocketsmart.db` (auto-created). `users(id, username UNIQUE, email, password_hash, created_at)`; `history(id, user_id, category, budget, request_json, result_json, source, created_at)`. Passwords are stored as salted PBKDF2-SHA256 (200k rounds), never in plain text. History queries always filter by `user_id`, so users cannot see each other's data.

## 14. Installation, configuration, running
See **SETUP_GUIDE.md** (step-by-step). Quick version: `pip install -r requirements.txt`, copy `.env.example` → `.env`, add `GEMINI_API_KEY`, run `python -m app.main`, open <http://127.0.0.1:8000>.

## 15. Testing
* `python -m pytest -v` → 30 tests (auth, validation, all planners, fallback, fake-Gemini paths, history isolation, pages).
* `python scripts/test_gemini.py` → live Gemini text + image connectivity (needs your key).
* Manual browser walkthrough with screenshots in `docs/screenshots/`.

## 16. Troubleshooting
See SETUP_GUIDE.md §10 and CLASSMATE_TEACHING_GUIDE.md §11.

## 17. Limitations
* Product data and prices are **simulated** (the brief allows mock/simulated scraping; real scraping violates site terms).
* Recommendation quality depends on the small catalog.
* SQLite and cookie sessions suit a demo, not large-scale production.
* Live Gemini behaviour was not verified by the build agent (no API key available) — run `scripts/test_gemini.py` once yourself.

## 18. Future scope
Real affiliate/product APIs, price-tracking, more planners (travel, wardrobe), Cloud Run deployment, Firestore/PostgreSQL, email verification, chart-based spending dashboard, Gemini function-calling for structured output.
