import os
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import json

from run_pipeline import run_pipeline

app = Flask(__name__)

# Set paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# === Serve your main HTML ===
@app.route('/')
def index():
    return render_template('ScribeAI.html')  # Looks inside templates/

# === Handle uploaded image + prompt ===
@app.route('/process', methods=['POST'])
def process():
    file = request.files.get('file')
    prompt = request.form.get('prompt', '')
    if not file or not prompt:
        return "Missing image or prompt", 400

    # Save handwriting image
    filename = secure_filename('handwriting.jpg')
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(image_path)

    # Save prompt as submission.json
    with open(os.path.join(UPLOAD_FOLDER, 'submission.json'), 'w') as f:
        json.dump({'prompt': prompt}, f)

    # Run pipeline
    try:
        run_pipeline()
    except Exception as e:
        return f"Pipeline error: {str(e)}", 500

    return redirect(url_for('download_gcode'))

# === Serve final G-code ===
@app.route('/output/final_output.gcode')
def download_gcode():
    return send_from_directory(OUTPUT_FOLDER, 'final_output.gcode', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
