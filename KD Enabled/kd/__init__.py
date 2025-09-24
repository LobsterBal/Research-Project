# kd/__init__.py
import os
import json
import subprocess
import sys

BASE_DIR = os.path.dirname(__file__)
RECORDER = os.path.join(BASE_DIR, "KD_Recorder.py")
PREDICTOR = os.path.join(BASE_DIR, "KD_Prediction.py")
DATA_FILE = os.path.join(BASE_DIR, "keystroke_data.json")

def record_keystrokes():
    """Launch KD_Recorder.py to capture keystrokes until Enter is pressed."""
    print("🔑 Start typing (press Enter to finish)...")
    subprocess.run([sys.executable, RECORDER], check=True)
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError("No keystroke data recorded")
    return DATA_FILE

def predict(model_path, train_csv=None):
    """Run KD_Prediction.py with given model + recorded keystrokes."""
    args = [sys.executable, PREDICTOR, "--model", model_path, "--input", DATA_FILE]
    if train_csv:
        args += ["--train-csv", train_csv]
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return json.loads(result.stdout.strip())
