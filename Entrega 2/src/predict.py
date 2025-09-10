"""Predicción con modelos entrenados para Titanic.

Uso:
    python -m src.predict --model models/rf.pkl --input data/tested.csv --output predictions.csv [--compare]

Notas:
- Si el CSV de entrada contiene la columna 'Survived', por defecto NO se generan predicciones
  (para no usar un dataset con etiqueta en fase de inferencia). Use --compare para evaluar
  el desempeño del modelo sobre ese conjunto (se reportan métricas por consola) y no se
  escriben predicciones.
- Para inferir sobre datos nuevos SIN 'Survived', se generará un CSV con las predicciones.
"""
from __future__ import annotations

import argparse
import os
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from .utils import get_logger, set_global_seed, RANDOM_STATE


logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Predice con un modelo entrenado del Titanic.")
    parser.add_argument("--model", required=True, help="Ruta al archivo .pkl del modelo.")
    parser.add_argument("--input", required=True, help="Ruta al CSV de entrada.")
    parser.add_argument("--output", required=True, help="Ruta al CSV de salida de predicciones.")
    parser.add_argument("--compare", action="store_true", help="Si el CSV tiene 'Survived', evalúa en lugar de predecir.")
    args = parser.parse_args()

    set_global_seed(RANDOM_STATE)

    if not os.path.exists(args.model):
        raise FileNotFoundError(f"No se encontró el modelo: {args.model}")
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"No se encontró el CSV de entrada: {args.input}")

    logger.info(f"Cargando modelo desde {args.model}")
    model = joblib.load(args.model)

    df = pd.read_csv(args.input)

    if "Survived" in df.columns:
        if not args.compare:
            raise SystemExit(
                "El CSV de entrada contiene 'Survived'. Por política, no se generan predicciones. "
                "Ejecute con --compare para evaluar el modelo sobre este conjunto."
            )
        # Evaluación simple
        y_true = df["Survived"].astype(int)
        X = df.drop(columns=["Survived"])  # el pipeline interno hará el resto
        logger.info("Evaluando sobre el CSV etiquetado...")
        y_pred = model.predict(X)
        acc = (y_pred == y_true).mean()
        from sklearn.metrics import classification_report

        try:
            y_score = None
            if hasattr(model, "predict_proba"):
                y_score = model.predict_proba(X)[:, 1]
            elif hasattr(model, "decision_function"):
                y_score = model.decision_function(X)
        except Exception:
            y_score = None

        print("\n== Resultados de Evaluación (compare) ==")
        print(f"Accuracy: {acc:.4f}")
        print(classification_report(y_true, y_pred, digits=4, zero_division=0))
        if y_score is not None:
            try:
                from sklearn.metrics import roc_auc_score, average_precision_score

                roc_auc = roc_auc_score(y_true, y_score)
                ap = average_precision_score(y_true, y_score)
                print(f"ROC-AUC: {roc_auc:.4f}")
                print(f"Average Precision: {ap:.4f}")
            except Exception:
                pass
        return

    # Predicción sobre datos sin etiqueta
    logger.info("Generando predicciones...")
    X_new = df.copy()
    preds = model.predict(X_new)
    out_df = df.copy()
    out_df["Prediction"] = preds
    out_df.to_csv(args.output, index=False)
    logger.info(f"Predicciones guardadas en {args.output}")


if __name__ == "__main__":
    main()
