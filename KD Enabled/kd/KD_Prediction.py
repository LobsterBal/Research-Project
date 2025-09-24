#!/usr/bin/env python3
# kd/KD_prediction.py
# Usage: python KD_prediction.py --model random_forest_model.pkl --input keystroke_data.json

import joblib
import pandas as pd
import json
import argparse
import os
import sys

def build_features_from_json_dict(data):
    seq = data.get("keystroke_sequence", [])
    total_time = data.get("total_recording_time", 0.0)

    features = []
    for item in seq:
        # match train order: hold, updown, downdown, upup
        features.append(item.get("hold_time", 0.0))
        features.append(item.get("up_down_time", 0.0))
        features.append(item.get("down_down_time", 0.0))
        features.append(item.get("up_up_time", 0.0))
    features.append(total_time)
    return features

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--train-csv", default=None, help="optional: training dataset CSV used only to derive column order")
    args = parser.parse_args()

    model_path = args.model
    input_path = args.input

    if not os.path.exists(model_path):
        print(json.dumps({"error": "model not found"}))
        sys.exit(2)
    if not os.path.exists(input_path):
        print(json.dumps({"error": "input not found"}))
        sys.exit(2)

    clf = joblib.load(model_path)

    with open(input_path, "r") as f:
        data = json.load(f)

    features = build_features_from_json_dict(data)

    # If the model expects a DataFrame with exact columns, we try to read training CSV to get column names.
    if args.train_csv and os.path.exists(args.train_csv):
        df_train = pd.read_csv(args.train_csv)
        feature_columns = df_train.drop(columns=["label"]).columns.tolist()
        if len(feature_columns) != len(features):
            # fallback: use numeric column names
            feature_columns = [f"f{i}" for i in range(len(features))]
        X = pd.DataFrame([features], columns=feature_columns)
    else:
        X = pd.DataFrame([features])

    pred = int(clf.predict(X)[0])
    prob = clf.predict_proba(X)[0].astype(float).tolist()

    out = {"pred": pred, "prob": prob}
    print(json.dumps(out))
    sys.stdout.flush()

if __name__ == "__main__":
    main()
