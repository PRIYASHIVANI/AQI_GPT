import os
import numpy as np
import pandas as pd
import joblib

DEFAULT_MODEL_DIR = "models"

AVAILABLE_MODELS = {
    "random_forest": "random_forest.pkl",
    "gradient_boosting": "gradient_boosting.pkl",
    "ridge": "ridge.pkl",
}


def load_model(model_name: str, model_dir: str = DEFAULT_MODEL_DIR):
    path = os.path.join(model_dir, AVAILABLE_MODELS.get(model_name, f"{model_name}.pkl"))
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at {path}")
    return joblib.load(path)


def load_scaler(model_dir: str = DEFAULT_MODEL_DIR):
    path = os.path.join(model_dir, "scaler.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Scaler not found at {path}")
    return joblib.load(path)


def predict(model, X: pd.DataFrame) -> float:
    prediction = model.predict(X)
    return float(np.ravel(prediction)[0])


def batch_predict(model, X: pd.DataFrame) -> np.ndarray:
    return np.ravel(model.predict(X))
