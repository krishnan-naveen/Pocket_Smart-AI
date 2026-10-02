# Viva Preparation — PocketSmart AI

## Basic project questions
**Q: What does your project do?** It takes a budget and preferences and returns AI-generated, budget-checked product recommendations for home interiors, parties and jewelry.
**Q: Who is the user?** Anyone planning a purchase on a fixed budget; they must register and log in.
**Q: What is unique?** AI picks are *verified by code* (real products, total ≤ budget) and a rule-based fallback guarantees an answer.
**Q: Is the product data real?** No, it is a simulated catalog (allowed by the brief: “mock API calls or simulated scraping”). Links are real search URLs on each platform.
**Q: Which endpoints exist?** `/generate-home`, `/generate-party`, `/generate-jewelry`, `/recommendations-details`, `/history`, `/register`, `/login`, `/logout`, `/token`, `/session-info`, `/session-data`, plus pages and `/health`.

## Programming questions
**Q: Why FastAPI?** Type-hint based validation, automatic Swagger docs at `/docs`, async support, and it is what the project’s Epic 3 specifies.
**Q: What is Pydantic?** A library that defines data models with types and constraints; invalid input raises a validation error (HTTP 422).
**Q: What is `Depends`?** FastAPI dependency injection; `Depends(get_current_user)` runs the auth check before the route body.
**Q: What does Jinja2 do?** Renders HTML templates by inserting Python values and loops.
**Q: Why a `try/except GeminiUnavailable`?** So any AI failure (no key, quota, network, bad JSON) triggers the fallback instead of a 500 error.
**Q: How does the party cost work?** Per-person items cost `price × guests`; per-event items cost their price; venue capacity must be ≥ guests.
**Q: What does `quantity` do in Home planner?** Selection uses `budget ÷ quantity` for one room; displayed cost is multiplied back by quantity.
**Q: Sync vs async?** Route functions are `async`; the Gemini call is a blocking network call, acceptable at demo scale (production: run in a thread pool or use the async client).

## AI questions
**Q: What is a hallucination and how did you handle it?** A model inventing facts. We give Gemini a closed candidate list and drop any id not in it.
**Q: What is temperature?** Randomness control; we use 0.4 for consistent, mostly deterministic answers.
**Q: Why not a pure rule-based system?** It cannot read free text or outfit images or write tailored explanations — but we keep it as a safety net.
**Q: What does the rule-based engine do?** Ranks items by tag relevance, takes one per category first, then fills the remaining budget greedily; for parties it reserves budget shares for venue and food.

## Generative AI questions
**Q: What is Gemini?** Google’s family of multimodal large language models.
**Q: What does multimodal mean?** The model accepts several input types — here text and images.
**Q: How do you send an image?** As a `Part.from_bytes(data, mime_type)` alongside the text prompt using the `google-genai` SDK.
**Q: How do you force JSON?** `response_mime_type="application/json"` in the config, plus a schema in the prompt, plus defensive parsing (strip code fences, extract `{…}`).
**Q: What is prompt engineering in your project?** Role, structured context (candidate list), hard constraints (budget), output schema, short reasons, low temperature.
**Q: The page says Gemini 1.5 Flash — why a different model?** Google has replaced 1.5 with newer models; the model name is an environment variable and the app falls back through a list.

## Google Cloud questions
**Q: Which Google service did you use?** The Gemini API through Google AI Studio (API key), as the project instructions describe.
**Q: Is a paid Google Cloud service required?** No; the AI Studio free tier is enough for the demo (limits apply).
**Q: How would you move it to Google Cloud?** Containerise with Docker, deploy on Cloud Run, store the key in Secret Manager, use Vertex AI/Gemini with service-account auth, and Cloud SQL or Firestore instead of SQLite.

## Database / data questions
**Q: Which database and why?** SQLite — zero setup, single file, perfect for a college demo.
**Q: What tables?** `users` and `history`.
**Q: How are SQL injections prevented?** All queries use parameterised placeholders (`?`).
**Q: How do you ensure users only see their own history?** Every history query includes `WHERE user_id = ?` using the id from the verified token; a test proves user B gets 404 for user A’s item.

## Architecture questions
**Q: Explain the flow.** Browser → FastAPI route (auth + validation) → planner engine (catalog → Gemini → verify | fallback) → SQLite → template render.
**Q: Why split into modules?** Separation of concerns: routes, auth, database, AI service and business logic can be changed and tested independently.
**Q: What is CORS?** Browser rule restricting cross-origin requests; we allow only localhost origins.
**Q: Cookie vs Bearer token?** Browser pages use an HttpOnly cookie; API clients use the `Authorization: Bearer` header from `/token`.

## Testing questions
**Q: How did you test?** 30 pytest tests (auth, validation, planners, fallback, fake Gemini responses, history isolation, page rendering), a scripted real-browser walkthrough with screenshots, and `scripts/test_gemini.py` for live Gemini.
**Q: How do you test AI code without calling the AI?** Replace `gemini_service.generate_json` with a fake that returns controlled data (valid, hallucinated, over-budget, error).
**Q: Edge cases covered?** Budget too low/negative/non-numeric, unknown room, 0 or 9999 guests, non-image upload, duplicate username, wrong password, unauthenticated access.

## Security questions
**Q: How are passwords protected?** Random 16-byte salt + PBKDF2-HMAC-SHA256, 200,000 rounds, constant-time comparison.
**Q: Where is the API key?** Only in `.env` (git-ignored) loaded as an environment variable; never printed or committed.
**Q: What protects the session cookie?** `HttpOnly` (no JS access) and `SameSite=Lax`; tokens expire after 120 minutes.
**Q: What would you add for production?** HTTPS + `Secure` cookies, rate limiting, CSRF tokens on forms, a strong `SECRET_KEY` from a secret manager, email verification.
**Q: File upload risks?** Size limit (5 MB), decoded and verified with Pillow, only JPEG/PNG/WEBP; the image is not saved to disk.

## Future scope questions
**Q: Next improvements?** Live product APIs and price tracking, Cloud Run deployment, analytics charts, more planners, Gemini function calling, user feedback loop to improve ranking.
**Q: Biggest limitation?** Simulated catalog; recommendation quality is bounded by its size.
