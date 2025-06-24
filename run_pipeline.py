import os
import json

from handwriting_processor import generate_strokes_json
from gpt_prompt import get_gemini_response
from stroke_writer import match_text_to_strokes
from gcode_writer import write_gcode

# Get absolute base directory (where this script lives)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define folder paths relative to BASE_DIR
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# File paths
HANDWRITING_IMG = os.path.join(UPLOADS_DIR, "handwriting.jpg")
PROMPT_FILE = os.path.join(UPLOADS_DIR, "submission.json")
STROKES_JSON = os.path.join(OUTPUT_DIR, "strokes.json")
FINAL_GCODE = os.path.join(OUTPUT_DIR, "final_output.gcode")

def run_pipeline():
    print("🔁 Starting full handwriting-to-GCode pipeline...")

    # Step 1: Extract handwriting strokes from the image
    print("🖊️  Extracting handwriting strokes...")
    generate_strokes_json(HANDWRITING_IMG, STROKES_JSON)

    # Step 2: Read user prompt from submission.json
    print("📖 Reading prompt from submission.json...")
    with open(PROMPT_FILE, "r") as f:
        prompt_data = json.load(f)
    prompt_text = prompt_data.get("prompt", "")
    if not prompt_text:
        raise ValueError("⚠️  No prompt found in submission.json.")

    # Step 3: Generate text using Gemini API
    print("🤖 Generating text with Gemini...")
    generated_text = get_gemini_response(prompt_text)
    if not generated_text:
        raise RuntimeError("❌ Failed to generate text from Gemini.")
    print("📝 Gemini output:\n", generated_text)

    # Step 4: Match generated text to handwriting strokes
    print("✍️  Matching text to handwriting strokes...")
    stroke_paths = match_text_to_strokes(generated_text, STROKES_JSON)

    # Step 5: Write G-code from stroke paths
    print("🧾 Writing final G-code...")
    write_gcode(stroke_paths, FINAL_GCODE)

    print(f"✅ Pipeline complete! G-code saved to: {FINAL_GCODE}")

if __name__ == "__main__":
    run_pipeline()
