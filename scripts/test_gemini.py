"""Story: "Validate Gemini API connectivity" - text-only and image+text prompts.

Run from the project folder:   python scripts/test_gemini.py
Needs GEMINI_API_KEY in your .env file. Never prints the key.
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402

from app import gemini_service  # noqa: E402
from app.config import get_settings  # noqa: E402


def main() -> int:
    s = get_settings()
    if not s.gemini_api_key:
        print("FAIL: GEMINI_API_KEY is empty. Copy .env.example to .env and paste your key.")
        return 1
    print(f"Models to try, in order: {s.gemini_models}")

    print("\n[1/2] Text-only prompt...")
    try:
        data, model = gemini_service.generate_json('Reply with JSON only: {"ok": true, "message": "hello from Gemini"}')
        print(f"  PASS with model '{model}': {data}")
    except gemini_service.GeminiUnavailable as exc:
        print(f"  FAIL: {exc}")
        return 1

    print("\n[2/2] Image + text prompt (a solid red square)...")
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (220, 20, 20)).save(buf, "PNG")
    try:
        data, model = gemini_service.generate_json(
            'Look at the image. Reply with JSON only: {"main_colour": "<colour name>"}', buf.getvalue(), "image/png")
        print(f"  PASS with model '{model}': {data}")
    except gemini_service.GeminiUnavailable as exc:
        print(f"  FAIL: {exc}")
        return 1

    print("\nBoth checks passed - text and multimodal Gemini calls work.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
