#!/usr/bin/env python3
# kd/KD_Recorder.py
# Requires: pynput
# Writes kd/keystroke_data.json

from pynput import keyboard
import time
import json
import os
import string
import sys
import subprocess

OUT_PATH = os.path.join(os.path.dirname(__file__), "keystroke_data.json")

# Allow letters, digits, punctuation, and space
ALLOWED_CHARS = set(string.ascii_letters + string.digits + string.punctuation + " ")

def normalize_key(key):
    try:
        if hasattr(key, "char") and key.char is not None:
            if key.char in ALLOWED_CHARS:
                return key.char
            else:
                return None
        else:
            return None
    except Exception:
        return None


class KeystrokeDynamicsRecorder:
    def __init__(self):
        self.key_press_times = {}
        self.key_release_times = {}
        self.down_times = {}
        self.event_log = []
        self.start_recording_time = None
        self.end_recording_time = None
        self.sequence_data = []
        self.total_recording_time = 0.0
        self.is_recording_active = False
        self.typed_chars = []  # store actual password characters

    def on_press(self, key):
        current_time = time.time()
        key_id = normalize_key(key)
        if key_id is None:
            return
        self.event_log.append(('press', key_id, current_time))
        if self.start_recording_time is None:
            self.start_recording_time = current_time
            self.is_recording_active = True
        if key_id not in self.key_press_times:
            self.key_press_times[key_id] = current_time
        self.typed_chars.append(key_id)  # record password char

    def on_release(self, key):
        current_time = time.time()
        key_id = normalize_key(key)

        # Exit cleanly on Enter
        if key == keyboard.Key.enter:
            self.end_recording_time = current_time
            self.is_recording_active = False
            self.save_results()
            return False  # stop listener

        if key_id is None:
            return

        self.event_log.append(('release', key_id, current_time))

        if key_id in self.key_press_times:
            press_time = self.key_press_times[key_id]
            hold_time = current_time - press_time
            self.down_times[key_id] = hold_time
            self.key_release_times[key_id] = current_time

            self._process_sequence()

            del self.key_press_times[key_id]
            if key_id in self.key_release_times:
                del self.key_release_times[key_id]

    def _process_sequence(self):
        sorted_events = sorted(self.event_log, key=lambda x: x[2])
        if len(sorted_events) < 2:
            return
        last_event = sorted_events[-1]
        last_key_id = last_event[1]
        last_event_timestamp = last_event[2]
        last_event_type = last_event[0]

        hold_time = self.down_times.get(last_key_id, 0.0)

        up_down_time = 0.0
        down_down_time = 0.0
        up_up_time = 0.0

        current_key_press_time = None
        for i in range(len(sorted_events)-1, -1, -1):
            event_type, k_id, ts = sorted_events[i]
            if event_type == 'press' and k_id == last_key_id:
                current_key_press_time = ts
                break

        prev_key_press_time = None
        prev_key_release_time = None
        search_limit_timestamp = current_key_press_time if current_key_press_time is not None else last_event_timestamp

        for i in range(len(sorted_events)-1, -1, -1):
            event_type, k_id, ts = sorted_events[i]
            if ts < search_limit_timestamp and k_id != last_key_id:
                if prev_key_press_time is None and event_type == 'press':
                    prev_key_press_time = ts
                if prev_key_release_time is None and event_type == 'release':
                    prev_key_release_time = ts
            if prev_key_press_time is not None and prev_key_release_time is not None:
                break

        if prev_key_release_time is not None and current_key_press_time is not None:
            up_down_time = max(0.0, current_key_press_time - prev_key_release_time)
        if prev_key_press_time is not None and current_key_press_time is not None:
            down_down_time = max(0.0, current_key_press_time - prev_key_press_time)
        if prev_key_release_time is not None and last_event_type == 'release':
            up_up_time = max(0.0, last_event_timestamp - prev_key_release_time)

        self.sequence_data.append({
            'key': last_key_id,
            'hold_time': hold_time,
            'up_down_time': up_down_time,
            'down_down_time': down_down_time,
            'up_up_time': up_up_time,
            'event_timestamp': last_event_timestamp
        })

    def _calculate_total_time(self):
        if self.start_recording_time is not None and self.end_recording_time is not None:
            self.total_recording_time = self.end_recording_time - self.start_recording_time
        else:
            self.total_recording_time = 0.0

    def save_results(self, path=OUT_PATH):
        self._calculate_total_time()
        data_to_save = {
            "total_recording_time": self.total_recording_time,
            "keystroke_sequence": self.sequence_data
        }
        with open(path, "w") as f:
            json.dump(data_to_save, f, indent=4)


def capture_password_with_kd():
    """
    Capture password and keystroke data using pynput + run KD prediction.
    Returns (password, kd_ok).

    - kd_ok is True only if KD model predicts legit user; False otherwise.
    - Even if KD fails (feature mismatch, wrong length, or model error), password is returned.
    """
    recorder = KeystrokeDynamicsRecorder()
    print("🔑 Please type your password (press Enter to finish)...")

    try:
        with keyboard.Listener(on_press=recorder.on_press,
                               on_release=recorder.on_release) as listener:
            listener.join()
    except Exception as e:
        print(f"⚠ Error capturing keystrokes: {e}")
        return "", False

    password = "".join(recorder.typed_chars)
    kd_ok = False  # default if KD fails

    # Run KD prediction
    kd_dir = os.path.dirname(__file__)
    model_path = os.path.join(kd_dir, "random_forest_model.pkl")
    input_path = os.path.join(kd_dir, "keystroke_data.json")

    try:
        result = subprocess.run(
            [sys.executable, os.path.join(kd_dir, "KD_Prediction.py"),
             "--model", model_path, "--input", input_path],
            check=True,
            capture_output=True,
            text=True
        )
        out = json.loads(result.stdout)
        pred = out.get("pred", 0)
        kd_ok = pred == 1

    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
        # Any KD prediction error is handled gracefully
        print(password)
        print("⚠ KD verification failed (feature mismatch or model error).")
        kd_ok = False

    return password, kd_ok


if __name__ == "__main__":
    pwd, ok = capture_password_with_kd()
    print("Captured password:", pwd, "success:", ok)
