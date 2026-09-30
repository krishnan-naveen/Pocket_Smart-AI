# Presentation Content — PocketSmart AI (14 slides)

**Slide 1 — Title**
PocketSmart AI: Your Smart Budget & Recommendation Assistant
Naan Mudhalvan · Google Cloud Generative AI · Presented by: <your name / team>

**Slide 2 — Problem Statement**
* Budget planning is scattered across many apps
* Easy to overspend or miss essentials (party = venue + food + decor)
* Hard to match jewelry to an outfit within a budget

**Slide 3 — Proposed Solution**
* One web app, three planners: Home, Party, Jewelry
* Gemini AI picks and explains products
* Code verifies every plan stays within budget

**Slide 4 — Objectives**
* Integrate Google Gemini (text + image)
* Build a secure FastAPI backend with login and history
* Deliver budget-checked, explainable recommendations
* Always give a result, even if AI fails

**Slide 5 — Features**
* Register / Login / Logout (JWT)
* Home, Party, Jewelry planners; outfit image upload
* Card results with sort and platform filter
* Dashboard and recommendation history
* Rule-based fallback

**Slide 6 — Technology Stack**
Python · FastAPI · Uvicorn · Jinja2 · HTML/CSS/JS · SQLite · PyJWT · Google Gemini (google-genai SDK) · Pillow · pytest

**Slide 7 — System Architecture**
Browser → FastAPI routes → Planner engine → (Gemini | Rule engine) → Verification → SQLite → Result cards
*(draw as the diagram in PROJECT_KNOWLEDGE.md §6)*

**Slide 8 — AI / Generative AI Approach**
* Prompt = request + closed candidate list + budget rule + JSON schema
* Multimodal: outfit image + text
* Output validated: real ids only, total ≤ budget
* Fallback chain: primary model → backup models → rule engine

**Slide 9 — Implementation**
* 16 HTML templates, 3 route modules, 6 backend modules
* 12+ endpoints: `/generate-home|party|jewelry`, `/token`, `/session-info`, `/history` …
* Simulated Amazon / IKEA / Zomato / OYO catalog

**Slide 10 — Results**
* 30 automated tests passing
* Browser walkthrough of every page completed, no unexpected console errors
* Plans always ≤ budget (e.g. ₹45,000 bedroom → ₹43,833; ₹40,000 party for 30 → ₹32,097)
* Live Gemini test: *add your own screenshot after running `scripts/test_gemini.py`*

**Slide 11 — Benefits**
* Saves time and prevents overspending
* Transparent reasons for each pick
* Reliable: never returns an over-budget or fake product
* Secure: hashed passwords, HttpOnly cookies, no secrets in code

**Slide 12 — Limitations**
* Simulated product data/prices
* Small catalog
* SQLite/demo-scale deployment

**Slide 13 — Future Scope**
* Live product APIs and price tracking
* Cloud Run + managed database deployment
* More planners (travel, wardrobe)
* Spending analytics charts

**Slide 14 — Conclusion**
PocketSmart AI shows how Generative AI plus simple, verifiable code can produce trustworthy budget recommendations. Thank you — questions?
