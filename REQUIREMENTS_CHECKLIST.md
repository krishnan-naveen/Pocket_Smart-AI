# Requirements Verification (against the MySkillWallet project page)

Source: the project page's Prerequisites, Workflow, Epics 1–5 and Conclusion sections, read on 30 Sep 2026. No evaluation rubric, submission form, downloadable resource or deadline text was visible on the page (“Resources: No resources available”). Faculty submission format is unknown — confirm it with your faculty.

**Page inconsistency:** the *Workflow* page says “Flask”, but the Epic 2/3/4 titles, story text and code sample say **FastAPI** (`Depends`, `TemplateResponse`, `uvicorn`). This project follows **FastAPI**.
**Outdated item:** the page says “Gemini 1.5 Flash Pro”. That model family is no longer offered, so the model name is configurable (default `gemini-3.5-flash`).

| # | Requirement (from page) | Implemented? | Tested? | Evidence |
|---|---|---|---|---|
| E1-S1 | Google account + Gemini API access (“Get API key”) | **You must do this** (needs your Google login) | – | SETUP_GUIDE §5 |
| E1-S2 | Configure API key, test integration incl. text + image | Yes (`.env`, `gemini_service.py`, `scripts/test_gemini.py`) | **Not live-tested** (no key available to the build agent). Code paths tested with fake Gemini | `tests/test_app.py::test_gemini_*` |
| E1-S3 | Prompts for budget interpretation & recommendations | Yes (`planners.build_prompt`) | Structure tested; real-model answer quality unverified | PROJECT_KNOWLEDGE §11 |
| E1-Validate | Sample Python call, text-only and image+text | Yes | Pending your run of `python scripts/test_gemini.py` | script output |
| E2-S1 | FastAPI init, import libraries, load `.env` | Yes (`app/main.py`, `config.py`) | Yes | server start log |
| E2-S2 | `/generate-home`, `/generate-party`, `/generate-jewelry` (text + optional image) | Yes | Yes | tests + screenshots 07, 09, 11 |
| E2-S2b | Link websites (Amazon, Flipkart, IKEA…) for products | Yes, simulated catalog + real search links | Yes | `products.py`, result cards |
| E2-S3 | Login `/login`, Register `/register`, Logout `/logout` | Yes | Yes | tests, screenshots 03–05 |
| E2-S4 | `/token` JWT, `/session-info`, `/session-data` | Yes | Yes | `test_token_endpoint_and_bearer_auth` |
| E3-S1 | Routes for Home/Party/Jewelry planners, User Auth, Session Info | Yes | Yes | as above |
| E3-S2 | `/recommendations-details` (budget, preferences, category) | Yes | Yes | `test_recommendations_details_endpoint` |
| E3-S3 | `/history` past queries & results | Yes (API + page) | Yes | `test_history_saved_and_user_isolated`, screenshot 12 |
| E3-S3b | CORS & static routing | Yes | Static served in browser run | `main.py` |
| E3-S4 | `/startup` initialisation and `main` (uvicorn) entry | Yes (lifespan startup, `python -m app.main`) | Yes | server log |
| E3 | Modular structure; mock/simulated scraping | Yes | – | folder structure |
| E4-S1 | Home page with budget input + category selectors | Yes (landing page with 3 planner cards + planner forms) | Yes | screenshot 01 |
| E4-S2 | Individual forms per planner connected to POST routes | Yes | Yes | screenshots 06, 10 |
| E4-S3 | Cards showing suggestions, details, prices | Yes | Yes | screenshots 07, 09, 11 |
| E4-S4 | Dynamic result display with JavaScript | Yes (fetch submit, sort, filter) | Yes | browser run |
| E5 pages | Home, Testimonials, Footer, Register, Login, Dashboard, 3 planner + 3 recommendation pages, History | Yes, all 12 | Yes | screenshots 01–12 |
| E5-S1 | Test real-world budgets across the three domains | Yes | Yes | tests + browser run |
| E5-S2 | Evaluate response quality, budget adherence, platform accuracy | Budget adherence tested (always ≤ budget); Gemini quality **pending live run** | Partly | tests |
| E5-S3 | Optimise prompts, add validations for edge cases | Yes | Yes | 11 validation/edge tests |
| E5-S4 | Fallback/default recommendations if AI insufficient | Yes | Yes | `test_gemini_*_falls_back` |
| E5 “Deployment” | Epic title mentions deployment, but no deployment story/instructions exist on the page | Not required by visible page; deployment notes in PROJECT_KNOWLEDGE §18 | – | – |
| Conclusion | Report section (outcomes, future scope) | PROJECT_KNOWLEDGE §17–18 | – | – |
| E4 note | “Templates Directory Structure” is shown as an image on the page; the image could not be read | Templates follow the page list of pages | – | `templates/` |

## Still needed from you
1. Create the Gemini API key and put it in `.env` (never share it).
2. Run `python scripts/test_gemini.py` — expect two PASS lines. Screenshot it as evidence.
3. Run one plan of each type with the real key and check the badge says “Gemini AI”.
4. Ask faculty what to submit (code, report, screenshots, PPT) — the page does not say.
5. Mark stories complete on MySkillWallet yourself; I did not click completion/submit controls.
