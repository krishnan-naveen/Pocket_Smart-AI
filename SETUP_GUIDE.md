# PocketSmart AI — Setup Guide (Windows, step by step)

Follow every step in order. Commands are for **Windows PowerShell** unless noted.

## 1. Install prerequisites
1. **Python 3.10 – 3.13** from <https://www.python.org/downloads/>. During install tick **“Add python.exe to PATH”**.
   Check: `python --version`
   > If you only have Python 3.14 or a very new version and a package fails to install, use a conda/venv with Python 3.12.
2. **VS Code** (optional but recommended) from <https://code.visualstudio.com/>.
3. **Git** (optional) from <https://git-scm.com/>.
4. A **Google account** (for the Gemini API key).

## 2. Open the project
The project folder is `PocketSmart-AI` (in your Documents folder). Open PowerShell there:
```powershell
cd $HOME\Documents\PocketSmart-AI
dir        # you should see app, templates, static, tests, requirements.txt ...
```

## 3. Create a virtual environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
If PowerShell blocks the script: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.
Your prompt should now start with `(.venv)`.

## 4. Install dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Google / Gemini setup (free API key)
1. Go to <https://aistudio.google.com/apikey> and sign in.
2. Accept the terms, click **Create API key** (choose or create a project when asked).
3. **Copy the key.** Treat it like a password.
4. Optional: at <https://ai.google.dev/gemini-api/docs/models> check the current model names.

## 6. Configuration (`.env`)
```powershell
copy .env.example .env
notepad .env
```
Fill in:
```
GEMINI_API_KEY=paste-your-key-here
GEMINI_MODEL=gemini-3.5-flash
SECRET_KEY=any-long-random-text-you-invent
```
Save. **Never** commit or share `.env` (it is already in `.gitignore`). If a key is ever leaked, delete it in AI Studio and create a new one.

## 7. Environment variables reference
| Variable | Meaning | Default |
|---|---|---|
| `GEMINI_API_KEY` | Your AI Studio key | empty → app uses rule-based fallback |
| `GEMINI_MODEL` | First model tried | `gemini-3.5-flash` |
| `GEMINI_FALLBACK_MODELS` | Comma list tried next | `gemini-3.5-flash-lite,gemini-2.5-flash` |
| `SECRET_KEY` | Signs login tokens | insecure dev value — change it |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Login lifetime | 120 |
| `DATABASE_PATH` | SQLite file | `pocketsmart.db` |

## 8. Run the application
First verify Gemini works (Story “Validate Gemini API connectivity”):
```powershell
python scripts/test_gemini.py
```
Expected: `PASS` for the text prompt and `PASS` for the image prompt. Then start the server:
```powershell
python -m app.main
```
Open <http://127.0.0.1:8000>. Stop the server with **Ctrl+C**.

## 9. Test the application
```powershell
python -m pytest -v
```
Expected: `30 passed`. These tests never call the real Gemini.
Manual test: register → login → each planner → History → Logout (see DEMO_SCRIPT.md).

## 10. Troubleshooting
| Problem | Fix |
|---|---|
| `python` not recognised | Reinstall Python with “Add to PATH”, or use `py` instead of `python` |
| Activate.ps1 blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `pip install` fails on a package | Use Python 3.12 in a fresh venv; update pip |
| `ModuleNotFoundError: app` | Run commands from the `PocketSmart-AI` folder |
| Yellow “AI service unavailable” banner | Key empty/wrong, quota reached, or model name retired. Read the message in the banner; run `python scripts/test_gemini.py`; change `GEMINI_MODEL` |
| `404 model not found` in banner | Model renamed — pick a current name from the models page |
| `429` / quota | Wait a minute or switch to a lighter model (`gemini-3.5-flash-lite`) |
| Port 8000 busy | `uvicorn app.main:app --port 8001` |
| Login loops back to login | Browser blocking cookies for 127.0.0.1; use Chrome/Edge normally |
| Reset all data | Stop the server and delete `pocketsmart.db` |
