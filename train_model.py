"""
Train AQI prediction models and save to models/ directory.
Run: python train_model.py
"""
import os
import json
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from utils.data import load_dataset
from utils.preprocessing import prepare_training_data, FEATURE_COLS

MODEL_DIR = "models"


def train_and_save():
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Loading dataset...")
    df = load_dataset()
    print(f"  {len(df)} rows, {df['City'].nunique()} cities, {df['Date'].min().date()} to {df['Date'].max().date()}")

    print("Preparing features...")
    X, y, scaler = prepare_training_data(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Target scaler for neural network (NNs converge better with normalized targets)
    y_scaler = StandardScaler()
    y_train_scaled = y_scaler.fit_transform(y_train.values.reshape(-1, 1)).ravel()

    models = {
        "random_forest": RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1),
        "gradient_boosting": GradientBoostingRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42),
        "ridge": Ridge(alpha=1.0),
    }

    nn_model = MLPRegressor(
        hidden_layer_sizes=(256, 128, 64),
        activation="relu",
        solver="adam",
        max_iter=2000,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=50,
        random_state=42,
        learning_rate="adaptive",
        learning_rate_init=0.005,
        batch_size=32,
    )

    results = {}

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        print(f"  MAE:  {mae:.2f}")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  R²:   {r2:.4f}")

        model_path = os.path.join(MODEL_DIR, f"{name}.pkl")
        joblib.dump(model, model_path)
        print(f"  Saved to {model_path}")

        importance = None
        if hasattr(model, "feature_importances_"):
            importance = dict(zip(FEATURE_COLS, model.feature_importances_.tolist()))

        results[name] = {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2": round(r2, 4),
            "feature_importance": importance,
        }

    # Train neural network with scaled targets
    print(f"\nTraining neural_network...")
    nn_model.fit(X_train, y_train_scaled)

    y_pred_scaled = nn_model.predict(X_test)
    y_pred_nn = y_scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()

    mae = mean_absolute_error(y_test, y_pred_nn)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_nn))
    r2 = r2_score(y_test, y_pred_nn)

    print(f"  MAE:  {mae:.2f}")
    print(f"  RMSE: {rmse:.2f}")
    print(f"  R²:   {r2:.4f}")

    nn_bundle = {"model": nn_model, "y_scaler": y_scaler}
    nn_path = os.path.join(MODEL_DIR, "neural_network.pkl")
    joblib.dump(nn_bundle, nn_path)
    print(f"  Saved to {nn_path}")

    results["neural_network"] = {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "feature_importance": None,
    }

    scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    print(f"\nScaler saved to {scaler_path}")

    metrics_path = os.path.join(MODEL_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Metrics saved to {metrics_path}")

    print("\nTraining complete.")


if __name__ == "__main__":
    train_and_save()
