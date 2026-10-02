# Teaching Guide — PocketSmart AI (from beginner level)

## 1. What is PocketSmart AI?
A website where you type a **budget** (say ₹40,000) and what you want (a bedroom, a birthday party, jewelry for a wedding). The app suggests products that fit the budget and tells you *why*, using Google's **Gemini** AI. It also makes sure the total never crosses your budget.

## 2. Problem statement
Planning a purchase means opening many shopping apps, comparing prices and mentally adding numbers. People overspend or forget things (a party needs venue *and* food *and* decor). PocketSmart does the planning in one place.

## 3. How the solution works (story version)
1. You register and log in (like any website).
2. You choose a planner and fill a small form.
3. The server prepares a **shortlist** of real-looking products that match your choice.
4. It gives the shortlist + your request to Gemini and says: “Pick the best combination, stay under budget, answer in JSON.”
5. The server **double-checks** Gemini (are the products real? is the sum under budget?). If Gemini fails, a simple rule-based program picks instead.
6. You see cards with price, platform, reason and a search link. The plan is saved in your history.

## 4. Technology stack — what each piece is
| Technology | Plain-English meaning | Where used |
|---|---|---|
| **Python** | Programming language | Everything in `app/` |
| **FastAPI** | Framework to create web addresses (routes) that run Python functions; auto-validates input | `app/main.py`, `app/routes/` |
| **Uvicorn** | The server program that runs FastAPI | `python -m app.main` |
| **Jinja2** | Fills HTML templates with data (`{{ user.username }}`) | `templates/` |
| **HTML/CSS/JavaScript** | Page structure, looks, behaviour (sending forms with `fetch`, sorting cards) | `templates/`, `static/` |
| **SQLite** | A database stored in one file | `app/database.py` |
| **JWT** | A signed “ticket” proving you logged in | `app/auth.py` |
| **PBKDF2** | Scrambles passwords so they can’t be read from the DB | `app/auth.py` |
| **Pydantic** | Defines/validates the shape of input data | `planners.py` |
| **Gemini + google-genai** | Google’s AI model and its Python library | `gemini_service.py` |
| **Pillow** | Checks uploaded images are real images | `planners.py` |
| **pytest** | Runs automatic tests | `tests/` |

## 5. Architecture
**User → Application → Budget Data → AI/Logic → Recommendation → User**

* User: browser form. 
* Application: FastAPI route (`/generate-home`) checks you’re logged in and validates input.
* Budget data: your budget + the product catalog (`products.py`).
* AI/Logic: Gemini chooses; Python verifies; rule engine is the backup.
* Recommendation: JSON → saved in SQLite → rendered as cards.

## 6. Folder structure — important files
* `app/main.py` – starts everything, connects routes, CORS, error pages.
* `app/routes/planner_routes.py` – the three `/generate-*` endpoints and planner pages.
* `app/planners.py` – **the brain**: validation, prompt, verification, rule engine.
* `app/gemini_service.py` – talks to Gemini; retries other models on failure.
* `app/products.py` – simulated catalog.
* `app/auth.py`, `app/routes/auth_routes.py` – login system.
* `templates/` – the pages; `_results.html` is the recommendation card layout.
* `tests/test_app.py` – 30 tests proving it works.

## 7. Important code (explained logically)
**a) Never trust the AI blindly** (`planners._verify_picks`):
```python
by_id = {i["id"]: i for i in pool}          # only real products
... if pid in by_id and pid not in seen: ...  # drop invented/duplicate ids
while chosen and total > limit: chosen.pop()  # trim until within budget
```
Idea: AI proposes, code disposes. This is a real-world pattern called *output validation / guardrails*.

**b) Fallback** (`run_planner`): `try: Gemini … except GeminiUnavailable: rule-based`. The user always gets an answer.

**c) Auth**: password → `pbkdf2_hmac` with a random salt; login creates a JWT stored in an **HttpOnly cookie** (JavaScript can’t steal it).

**d) Party maths**: food is priced *per person*, so cost = price × guests; venue must have capacity ≥ guests.

## 8. AI / Generative AI
* **Service:** Google Gemini through the Gen AI SDK, with an API key from Google AI Studio.
* **Why:** it understands free-text needs (“small room, need storage”), reads outfit **images**, and writes natural explanations — things a plain `if` statement can’t.
* **Input:** a prompt containing the user request, extra notes, the candidate list with prices, rules, the exact JSON format; optionally an image.
* **Processing:** the model predicts the best matching combination and text (it is a probabilistic language model, so we validate the output).
* **Output:** JSON `{summary, outfit_analysis, picks:[{id, reason}], tips}`.
* **Use:** picks are verified, converted to cards; summary and tips are shown; the source badge says “Gemini AI”.
* **Prompt engineering done:** role, closed candidate list (prevents hallucination), hard budget rule, short reasons, strict JSON, low temperature (0.4).

## 9. How to run
```powershell
cd $HOME\Documents\PocketSmart-AI
.venv\Scripts\Activate.ps1
python scripts/test_gemini.py     # optional check
python -m app.main                # then open http://127.0.0.1:8000
python -m pytest -v               # tests
```

## 10. How to demonstrate
Use **DEMO_SCRIPT.md** (12 steps, about 8–10 minutes).

## 11. Common errors
| Error | Meaning | Fix |
|---|---|---|
| Yellow banner “AI service unavailable” | Gemini call failed; app used fallback | Read banner text; fix key/model/quota |
| 401 Not authenticated | Not logged in / cookie expired | Log in again |
| 422 “Budget must be between…” | Input validation | Enter ₹500 – ₹1 crore |
| 422 “not a valid image” | Wrong upload | Use JPG/PNG/WEBP ≤ 5 MB |
| `ModuleNotFoundError` | Wrong folder or venv not active | `cd` into project, activate venv |

## 12. Viva questions
See **VIVA_PREPARATION.md** for the full list with answers. Five you must know:
1. *Why FastAPI?* Fast, automatic validation and docs (`/docs`), async support.
2. *How do you stop AI from exceeding the budget?* Candidate list + verification + trimming + fallback.
3. *How are passwords stored?* Salted PBKDF2 hash, never plain text.
4. *What if Gemini is down?* Rule-based engine takes over; user still gets a valid plan.
5. *Is the product data real?* No — simulated, as the brief allows; links are real search URLs.
