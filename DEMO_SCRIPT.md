# Live Demo Script (≈10 minutes)

**Before you start:** venv active, `.env` has your key, run `python scripts/test_gemini.py` once (both PASS), delete `pocketsmart.db` for a clean start, then `python -m app.main`. Have two browser tabs: the app and http://127.0.0.1:8000/docs.

**Step 1 — Launch application**
Action: Show the terminal running `python -m app.main`, then open http://127.0.0.1:8000.
Explain: FastAPI served by Uvicorn; on startup it creates the SQLite tables and checks the Gemini key.
Expected Result: Landing page with the three planner cards, Testimonials link, footer.

**Step 2 — Register**
Action: Click Register; try username `ab` with a bad email first, then `demo_user`, `demo@example.com`, password `demo123`.
Explain: Server-side validation; password is hashed with salted PBKDF2, never stored in plain text.
Expected Result: Error message first, then redirect to Login with a green “Account created” message.

**Step 3 — Login (and wrong password)**
Action: Enter a wrong password, then the correct one.
Explain: Success creates a JWT stored in an HttpOnly cookie; `/token` gives the same JWT to API clients.
Expected Result: “Invalid username or password”, then the Dashboard.

**Step 4 — Dashboard**
Action: Point out the counters and planner shortcuts.
Explain: Data comes from the `history` table for this user only.
Expected Result: “0 recommendations so far”, empty recent table.

**Step 5 — Home Interior Planner**
Action: Home planner → Room: Bedroom, Style: Modern, Rooms: 1, Budget: 45000 → Get recommendations.
Explain: Backend filters the catalog to bedroom items, sends the list + rules to Gemini, then verifies the answer.
Expected Result: Cards for bed/mattress/lamp etc., “Gemini AI · model” badge, planned total ≤ ₹45,000 with progress bar.

**Step 6 — Show dynamic UI**
Action: Sort “Price: high to low”, filter Platform “IKEA”.
Explain: Plain JavaScript reorders/hides cards in the browser without reloading.
Expected Result: Cards reorder; only IKEA cards remain visible.

**Step 7 — Party Planner**
Action: Party → Birthday, 30 guests, ₹40,000, tick Vegetarian → submit.
Explain: Food price is per person × guests; venue capacity must cover 30; veg filter removes non-veg options.
Expected Result: Venue + Veg buffet (₹450 × 30 guests) + decor; total under ₹40,000.

**Step 8 — Jewelry Planner with image**
Action: Jewelry → Wedding, Traditional, outfit “green silk saree”, upload any outfit photo, ₹9,000.
Explain: Multimodal Gemini call — image and text together; Pillow validates type and size before it is sent.
Expected Result: “Outfit analysis” paragraph plus matching jewelry cards within ₹9,000.

**Step 9 — Input validation**
Action: In Home planner enter budget 10 (or use browser dev tools to bypass the min attribute) and submit; then upload a `.txt` renamed to `.png` in Jewelry.
Explain: Two layers: HTML limits in the browser and Pydantic/Pillow checks on the server.
Expected Result: Red error: “Budget must be between Rs 500 and Rs 10,000,000” / “not a valid image”.

**Step 10 — Fallback (resilience)**
Action: Stop the server, temporarily blank `GEMINI_API_KEY` in `.env`, restart, run a Home plan.
Explain: If AI is unavailable the rule-based engine keeps the app working (Epic 5, story 4).
Expected Result: Yellow banner “AI service unavailable…”, badge “Rule-based fallback”, plan still ≤ budget. Restore the key afterwards.

**Step 11 — History and API**
Action: Open History, reopen an old plan; then in the `/docs` tab show `/generate-home`, `/token`, `/session-info`, `/history`.
Explain: Every result is stored as JSON; each user can only read their own rows.
Expected Result: Table of past plans; reopening shows identical cards; Swagger UI lists all endpoints.

**Step 12 — Tests and logout**
Action: In terminal run `python -m pytest -q`, then click Logout.
Explain: 30 tests cover auth, validation, planners, fallback, fake-Gemini scenarios and user isolation.
Expected Result: `30 passed`; redirect to Login; Dashboard URL now redirects to Login.
