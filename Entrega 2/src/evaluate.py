"""Evaluación de modelos entrenados para Titanic.

Uso:
    python -m src.evaluate --data data/tested.csv --models_dir models --out_dir reports

Genera:
- reports/metrics/metrics_summary.json
- reports/figures/confusion_matrix_*.png
- reports/figures/roc_curve_*.png (si hay probas/decision)
- reports/figures/pr_curve_*.png (si hay probas/decision)
- reports/metrics/feature_importances_*.csv (para modelos con importancias)
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Optional, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    average_precision_score,
)

from .features import TitanicFeatureEngineer, build_preprocessor, get_output_feature_names
from .utils import RANDOM_STATE, ensure_dir, get_logger, set_global_seed, train_test_split_fixed, timer


logger = get_logger(__name__)


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Survived" not in df.columns:
        raise ValueError("El CSV debe contener la columna 'Survived' para evaluación.")
    return df


def list_model_paths(models_dir: str) -> List[str]:
    return [
        os.path.join(models_dir, f)
        for f in os.listdir(models_dir)
        if f.endswith(".pkl")
    ]


def predict_scores(model, X_test: pd.DataFrame) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """Devuelve (y_pred, y_score) siendo y_score probabilidades o decision_function si existe."""
    y_pred = model.predict(X_test)
    y_score: Optional[np.ndarray] = None
    if hasattr(model, "predict_proba"):
        try:
            y_score = model.predict_proba(X_test)[:, 1]
        except Exception:
            y_score = None
    if y_score is None and hasattr(model, "decision_function"):
        try:
            y_score = model.decision_function(X_test)
        except Exception:
            y_score = None
    return y_pred, y_score


def save_confusion_matrix(y_true, y_pred, out_path: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    disp = ConfusionMatrixDisplay.from_predictions(y_true, y_pred, cmap="Blues", ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def save_roc_curve(y_true, y_score, out_path: str, title: str) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    auc = roc_auc_score(y_true, y_score)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(fpr, tpr, label=f"ROC AUC = {auc:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(title)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return float(auc)


def save_pr_curve(y_true, y_score, out_path: str, title: str) -> float:
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    ap = average_precision_score(y_true, y_score)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(recall, precision, label=f"AP = {ap:.3f}")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(title)
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return float(ap)


def try_save_feature_importances(model, X_test: pd.DataFrame, out_csv: str) -> Optional[str]:
    """Extrae importancias si el estimador final las dispone y guarda CSV.

    Retorna la ruta si se guardó o None si no aplica.
    """
    try:
        if not hasattr(model, "named_steps"):
            return None
        est = model.named_steps.get("clf")
        preproc = model.named_steps.get("preprocessor")
        feat_eng = model.named_steps.get("feat_eng")
        if est is None or preproc is None or feat_eng is None:
            return None
        if not hasattr(est, "feature_importances_"):
            return None
        # obtener columnas tras ingeniería
        X_eng = feat_eng.transform(X_test.copy())
        input_cols = list(X_eng.columns)
        feat_names = get_output_feature_names(preproc, input_cols)
        importances = est.feature_importances_
        if len(importances) != len(feat_names):
            feat_names = [f"f{i}" for i in range(len(importances))]
        imp_df = pd.DataFrame({"feature": feat_names, "importance": importances}).sort_values(
            "importance", ascending=False
        )
        imp_df.to_csv(out_csv, index=False)
        return out_csv
    except Exception as e:  # pragma: no cover
        logger.warning(f"No se pudieron guardar importancias: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Evalúa modelos entrenados para Titanic.")
    parser.add_argument("--data", required=True, help="Ruta al CSV con 'Survived'.")
    parser.add_argument("--models_dir", default="models", help="Directorio con archivos .pkl")
    parser.add_argument("--out_dir", default="reports", help="Directorio de salida para reportes")
    args = parser.parse_args()

    set_global_seed(RANDOM_STATE)

    ensure_dir(args.out_dir)
    ensure_dir(os.path.join(args.out_dir, "figures"))
    ensure_dir(os.path.join(args.out_dir, "metrics"))

    df = load_data(args.data)
    X_train, X_test, y_train, y_test = train_test_split_fixed(df, target_col="Survived", test_size=0.2)

    model_paths = list_model_paths(args.models_dir)
    if not model_paths:
        raise FileNotFoundError(f"No se encontraron modelos .pkl en {args.models_dir}")

    summary: Dict[str, Dict[str, float]] = {}

    for path in model_paths:
        name = os.path.splitext(os.path.basename(path))[0]
        logger.info(f"Evaluando modelo {name}...")
        with timer(f"eval_{name}"):
            model = joblib.load(path)
            y_pred, y_score = predict_scores(model, X_test)

        acc = accuracy_score(y_test, y_pred)
        p_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
        r_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
        f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
        p_weighted = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        r_weighted = recall_score(y_test, y_pred, average="weighted", zero_division=0)
        f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)
        roc_auc = None
        ap_score = None

        # figuras
        cm_path = os.path.join(args.out_dir, "figures", f"confusion_matrix_{name}.png")
        save_confusion_matrix(y_test, y_pred, cm_path, f"Matriz de Confusión - {name}")

        if y_score is not None:
            roc_path = os.path.join(args.out_dir, "figures", f"roc_curve_{name}.png")
            pr_path = os.path.join(args.out_dir, "figures", f"pr_curve_{name}.png")
            roc_auc = save_roc_curve(y_test, y_score, roc_path, f"ROC - {name}")
            ap_score = save_pr_curve(y_test, y_score, pr_path, f"Precision-Recall - {name}")

        # importancias
        imp_csv = os.path.join(args.out_dir, "metrics", f"feature_importances_{name}.csv")
        imp_saved = try_save_feature_importances(model, X_test, imp_csv)

        summary[name] = {
            "accuracy": float(acc),
            "precision_macro": float(p_macro),
            "recall_macro": float(r_macro),
            "f1_macro": float(f1_macro),
            "precision_weighted": float(p_weighted),
            "recall_weighted": float(r_weighted),
            "f1_weighted": float(f1_weighted),
            "roc_auc": float(roc_auc) if roc_auc is not None else None,
            "average_precision": float(ap_score) if ap_score is not None else None,
            "confusion_matrix_path": cm_path,
            "feature_importances_csv": imp_saved,
        }

    # guardar resumen
    summary_path = os.path.join(args.out_dir, "metrics", "metrics_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Resumen de métricas guardado en {summary_path}")


if __name__ == "__main__":
    main()
