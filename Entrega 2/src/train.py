"""Entrenamiento de modelos para Titanic (RF, MLP, HGB y opcional XGB).

Uso:
    python -m src.train --data data/tested.csv --models rf mlp hgb --save_dir models

Guarda:
- models/rf.pkl, models/mlp.pkl, models/hgb.pkl, (opcional) models/xgb.pkl
- reports/metrics/cv_results_*.csv

Todas las semillas fijadas en 42 para reproducibilidad.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedKFold
from sklearn.neural_network import MLPClassifier

from .features import build_pipeline
from .utils import RANDOM_STATE, ensure_dir, get_logger, set_global_seed, train_test_split_fixed, timer


logger = get_logger(__name__)


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Survived" not in df.columns:
        raise ValueError("El CSV debe contener la columna 'Survived' para entrenamiento.")
    return df


def build_search_rf() -> Tuple[RandomizedSearchCV, str]:
    rf = RandomForestClassifier(
        random_state=RANDOM_STATE,
        class_weight="balanced",
        n_jobs=-1,
    )
    pipe = build_pipeline(rf, kind="tree")
    param_distributions = {
        "clf__n_estimators": [100, 200, 300, 500],
        "clf__max_depth": [None, 5, 10, 15, 20, 30],
        "clf__min_samples_split": [2, 5, 10, 20],
        "clf__min_samples_leaf": [1, 2, 4, 8],
        "clf__max_features": [None, "sqrt", "log2"],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search = RandomizedSearchCV(
        estimator=pipe,
        param_distributions=param_distributions,
        n_iter=20,
        scoring="f1_macro",
        cv=cv,
        n_jobs=-1,
        refit=True,
        random_state=RANDOM_STATE,
        verbose=1,
    )
    return search, "rf"


def build_search_mlp() -> Tuple[GridSearchCV, str]:
    mlp = MLPClassifier(
        random_state=RANDOM_STATE,
        early_stopping=True,
        max_iter=1000,
    )
    pipe = build_pipeline(mlp, kind="scaled")
    param_grid = {
        "clf__hidden_layer_sizes": [(64,), (128,), (64, 32)],
        "clf__alpha": [1e-5, 1e-4, 1e-3],
        "clf__learning_rate_init": [1e-3, 5e-4],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(
        estimator=pipe,
        param_grid=param_grid,
        scoring="f1_macro",
        cv=cv,
        n_jobs=-1,
        refit=True,
        verbose=1,
    )
    return search, "mlp"


def build_search_hgb() -> Tuple[RandomizedSearchCV, str]:
    hgb = HistGradientBoostingClassifier(
        learning_rate=0.1,
        random_state=RANDOM_STATE,
    )
    pipe = build_pipeline(hgb, kind="tree")
    param_distributions = {
        "clf__learning_rate": [0.05, 0.1, 0.2],
        "clf__max_depth": [None, 3, 5, 7, 10],
        "clf__max_leaf_nodes": [15, 31, 63],
        "clf__min_samples_leaf": [10, 20, 30],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search = RandomizedSearchCV(
        estimator=pipe,
        param_distributions=param_distributions,
        n_iter=15,
        scoring="f1_macro",
        cv=cv,
        n_jobs=-1,
        refit=True,
        random_state=RANDOM_STATE,
        verbose=1,
    )
    return search, "hgb"


def build_search_xgb():
    try:
        from xgboost import XGBClassifier  # type: ignore
    except Exception:  # pragma: no cover
        return None, None

    xgb = XGBClassifier(
        objective="binary:logistic",
        n_estimators=300,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        tree_method="hist",
    )
    pipe = build_pipeline(xgb, kind="tree")
    param_grid = {
        "clf__max_depth": [3, 5, 7],
        "clf__min_child_weight": [1, 3, 5],
        "clf__gamma": [0, 0.1],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(
        estimator=pipe,
        param_grid=param_grid,
        scoring="f1_macro",
        cv=cv,
        n_jobs=-1,
        refit=True,
        verbose=1,
    )
    return search, "xgb"


def fit_and_save(
    search, name: str,
    X_train: pd.DataFrame, y_train: pd.Series,
    out_models_dir: str, out_reports_dir: str,
) -> Dict[str, str]:
    logger.info(f"Entrenando modelo {name}...")
    with timer(f"fit_{name}"):
        search.fit(X_train, y_train)
    best = search.best_estimator_

    ensure_dir(out_models_dir)
    model_path = os.path.join(out_models_dir, f"{name}.pkl")
    joblib.dump(best, model_path)
    logger.info(f"Modelo guardado en {model_path}")

    # guardar cv_results
    ensure_dir(os.path.join(out_reports_dir, "metrics"))
    cv_df = pd.DataFrame(search.cv_results_)
    cv_path = os.path.join(out_reports_dir, "metrics", f"cv_results_{name}.csv")
    cv_df.to_csv(cv_path, index=False)

    # best params
    best_params_path = os.path.join(out_reports_dir, "metrics", f"best_params_{name}.json")
    with open(best_params_path, "w", encoding="utf-8") as f:
        json.dump(search.best_params_, f, indent=2)

    return {"model_path": model_path, "cv_results_path": cv_path, "best_params_path": best_params_path}


def main():
    parser = argparse.ArgumentParser(description="Entrena modelos (RF/MLP/HGB/XGB opcional) para Titanic.")
    parser.add_argument("--data", required=True, help="Ruta al CSV con 'Survived'.")
    parser.add_argument("--models", nargs="+", default=["rf", "mlp", "hgb"],
                        choices=["rf", "mlp", "hgb", "xgb"], help="Modelos a entrenar.")
    parser.add_argument("--save_dir", default="models", help="Directorio para guardar modelos.")
    parser.add_argument("--reports_dir", default="reports", help="Directorio de reportes (cv_results, params).")
    args = parser.parse_args()

    set_global_seed(RANDOM_STATE)

    df = load_data(args.data)
    X_train, X_test, y_train, y_test = train_test_split_fixed(df, target_col="Survived", test_size=0.2)
    logger.info(f"Split: train={X_train.shape}, test={X_test.shape}")

    model_builders = {
        "rf": build_search_rf,
        "mlp": build_search_mlp,
        "hgb": build_search_hgb,
        "xgb": build_search_xgb,
    }

    results: Dict[str, Dict[str, str]] = {}

    for m in args.models:
        builder = model_builders[m]
        search, name = builder()
        if search is None:  # xgb no disponible
            logger.warning("xgboost no disponible; omitiendo XGBClassifier.")
            continue
        paths = fit_and_save(
            search, name,
            X_train, y_train,
            out_models_dir=args.save_dir,
            out_reports_dir=args.reports_dir,
        )
        results[name] = paths

    # guardar resumen simple
    ensure_dir(os.path.join(args.reports_dir, "metrics"))
    summary_path = os.path.join(args.reports_dir, "metrics", "training_outputs.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Resumen guardado en {summary_path}")


if __name__ == "__main__":
    main()
