import json
import os
from pathlib import Path
import argparse
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def find_screenshots(root_dir: str):
    """
    Recursively find screenshots under a directory created by pytest (artifacts/ui_screenshots/...).
    """
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"Screenshot directory not found: {root.resolve()}")

    exts = {".png", ".jpg", ".jpeg"}
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts]
    # stable ordering
    files.sort(key=lambda p: str(p).lower())

    # IMPORTANT: don't print to stdout; it breaks JSON parsing in server.py
    if os.getenv("UI_VALIDATOR_DEBUG") == "1":
        print(files, file=sys.stderr)

    return files

# ==========================
# Read Image Bytes (+ mime)
# ==========================

def read_image(image_path: str):
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Screenshot not found: {p.resolve()}")

    ext = p.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        mime_type = "image/jpeg"
    elif ext == ".png":
        mime_type = "image/png"
    else:
        # fallback; Gemini often still works, but keep it explicit
        mime_type = "application/octet-stream"

    return p.read_bytes(), mime_type


# ==========================
# Build LLM Prompt
# ==========================

def build_prompt():
    return """
You are a senior mobile UI/UX quality engineer.

Analyze this mobile app screenshot and detect UI issues.

Check for:
1. Misalignment of elements
2. Overlapping components
3. Uneven spacing
4. Text truncation
5. Clipped elements
6. Visual imbalance
7. Poor layout hierarchy

Return STRICT JSON in this format:

{
  "critical": [
    {
      "issue": "",
      "description": "",
      "location_hint": ""
    }
  ],
  "moderate": [],
  "minor": [],
  "ui_score": 0
}

Rules:
- No explanation outside JSON
- ui_score must be between 0 and 100
- Deduct points based on severity
"""


# ==========================
# Call Gemini Vision
# ==========================

def analyze_ui_with_llm(image_path: str):
    image_bytes, mime_type = read_image(image_path)

    resp = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"""
                    {build_prompt()}
                    Context:
                    Screenshot file name: {Path(image_path).name}
                    This screenshot comes from an automated mobile test flow.
                    """
                    ),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=image_bytes,
                        )
                    ),
                ],
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )

    content = (resp.text or "").strip()

    try:
        return json.loads(content)
    except Exception:
        print("LLM did not return valid JSON. Raw output:")
        print(content)
        return None

def analyze_screenshots_in_dir(root_dir: str):
    """
    Analyze all screenshots under root_dir and return a list of results.
    Never raises on a single bad image/LLM failure.
    """
    root = Path(root_dir)
    results = []

    for p in find_screenshots(str(root)):
        try:
            out = analyze_ui_with_llm(str(p)) or {}
            results.append(
                {
                    "screenshot_path": str(p.resolve()),
                    "relative_path": str(p.relative_to(root)).replace("\\", "/"),
                    "screenshot_name": p.name,
                    "ui_score": out.get("ui_score"),
                    "critical": out.get("critical", []) or [],
                    "moderate": out.get("moderate", []) or [],
                    "minor": out.get("minor", []) or [],
                }
            )
        except Exception as e:
            results.append(
                {
                    "screenshot_path": str(p.resolve()),
                    "relative_path": str(p.relative_to(root)).replace("\\", "/"),
                    "screenshot_name": p.name,
                    "ui_score": None,
                    "critical": [{"issue": "Analyzer error", "description": str(e), "location_hint": ""}],
                    "moderate": [],
                    "minor": [],
                }
            )

    return results

# ==========================
# CLI TEST
# ==========================

def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-dir", required=True, help="Directory to scan for screenshots")
    args = parser.parse_args()

    root = args.root_dir
    results = analyze_screenshots_in_dir(root)
    print(json.dumps({"root_dir": root, "results": results}))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())