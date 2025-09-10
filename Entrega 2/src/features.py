"""Preprocesamiento e ingeniería de variables para Titanic.

Provee:
- TitanicFeatureEngineer: transforma el DataFrame con nuevas columnas
- build_preprocessor(kind): 'tree' o 'scaled' para crear ColumnTransformer
- build_pipeline(model, kind): Pipeline completa (feat_eng + preproc + modelo)
- get_output_feature_names(preproc, input_columns): nombres de features tras one-hot
"""
from __future__ import annotations

import re
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


BASE_NUMERIC = ["Pclass", "Age", "SibSp", "Parch", "Fare"]
BASE_CATEGORICAL = ["Sex", "Embarked"]
TEXT_COLS = ["Name", "Ticket", "Cabin"]

ENGINEERED_NUMERIC = ["FamilySize", "IsAlone"]
ENGINEERED_CATEGORICAL = ["Title", "Deck", "TicketPrefix"]


class TitanicFeatureEngineer(BaseEstimator, TransformerMixin):
    """Crea variables derivadas del dataset Titanic.

    - FamilySize = SibSp + Parch + 1
    - IsAlone = 1 si FamilySize == 1, else 0
    - Title desde Name (Mr, Mrs, Miss, Master, Rare)
    - Deck desde Cabin (primera letra; NaN -> 'U')
    - TicketPrefix desde Ticket (prefijo alfanumérico; si no -> 'NONE')
    """

    def __init__(self, drop_original_text: bool = True):
        self.drop_original_text = drop_original_text
        self.columns_: Optional[List[str]] = None

    def fit(self, X: pd.DataFrame, y=None):  # noqa: N803 (sklearn signature)
        return self

    @staticmethod
    def _extract_title(name: str) -> str:
        if not isinstance(name, str):
            return "Rare"
        match = re.search(r",\s*([^.]*)\.", name)
        title = match.group(1).strip() if match else "Rare"
        mapping = {
            "Mlle": "Miss",
            "Ms": "Miss",
            "Mme": "Mrs",
            "Lady": "Rare",
            "Countess": "Rare",
            "Capt": "Rare",
            "Col": "Rare",
            "Don": "Rare",
            "Dr": "Rare",
            "Major": "Rare",
            "Rev": "Rare",
            "Sir": "Rare",
            "Jonkheer": "Rare",
            "Dona": "Rare",
        }
        title = mapping.get(title, title)
        if title not in {"Mr", "Mrs", "Miss", "Master"}:
            title = "Rare"
        return title

    @staticmethod
    def _extract_deck(cabin: str) -> str:
        if isinstance(cabin, str) and len(cabin) > 0:
            return cabin[0].upper()
        return "U"

    @staticmethod
    def _extract_ticket_prefix(ticket: str) -> str:
        if not isinstance(ticket, str):
            return "NONE"
        # quitar dígitos, puntos, barras duplicadas y espacios
        cleaned = ticket.replace(".", " ").replace("/", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # prefijo alfanumérico antes del último bloque numérico
        parts = cleaned.split(" ")
        alnum = [p for p in parts if not p.isdigit()]
        if len(alnum) == 0:
            return "NONE"
        return alnum[0].upper()

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:  # noqa: N803 (sklearn)
        X = X.copy()

        # FamilySize e IsAlone
        X["FamilySize"] = X.get("SibSp", 0).fillna(0) + X.get("Parch", 0).fillna(0) + 1
        X["IsAlone"] = (X["FamilySize"] == 1).astype(int)

        # Title
        X["Title"] = X["Name"].apply(self._extract_title) if "Name" in X else "Rare"

        # Deck
        X["Deck"] = X["Cabin"].apply(self._extract_deck) if "Cabin" in X else "U"

        # TicketPrefix
        X["TicketPrefix"] = (
            X["Ticket"].apply(self._extract_ticket_prefix) if "Ticket" in X else "NONE"
        )

        # ordenar columnas clave primero
        cols = (
            BASE_NUMERIC
            + BASE_CATEGORICAL
            + ENGINEERED_NUMERIC
            + ENGINEERED_CATEGORICAL
        )
        # algunos datasets pueden no tener todas las columnas base
        existing_cols = [c for c in cols if c in X.columns]
        X_out = X[existing_cols].copy()

        if not self.drop_original_text:
            for c in TEXT_COLS:
                if c in X.columns and c not in X_out.columns:
                    X_out[c] = X[c]

        self.columns_ = list(X_out.columns)
        return X_out


def build_preprocessor(kind: str = "tree") -> ColumnTransformer:
    """Crea un ColumnTransformer para 'tree' (sin escalar) o 'scaled' (con StandardScaler)."""
    numeric_features = BASE_NUMERIC + ENGINEERED_NUMERIC
    categorical_features = BASE_CATEGORICAL + ENGINEERED_CATEGORICAL

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            *([("scaler", StandardScaler())] if kind == "scaled" else []),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )
    return preprocessor


def build_pipeline(model, kind: str = "tree") -> Pipeline:
    """Construye una Pipeline completa: FeatureEngineering + Preprocesador + Modelo."""
    return Pipeline(
        steps=[
            ("feat_eng", TitanicFeatureEngineer()),
            ("preprocessor", build_preprocessor(kind=kind)),
            ("clf", model),
        ]
    )


def get_output_feature_names(preproc: ColumnTransformer, input_columns: List[str]) -> List[str]:
    """Obtiene los nombres de salida tras ColumnTransformer (incluye OneHot)."""
    try:
        names = preproc.get_feature_names_out(input_features=input_columns)
        return list(names)
    except Exception:
        # fallback genérico
        return [f"f{i}" for i in range(preproc.transform(pd.DataFrame(columns=input_columns, index=[0])).shape[1])]
