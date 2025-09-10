"""Utilidades comunes para el proyecto Titanic ML Supervisado.

Funciones incluidas:
- set_global_seed: fija las semillas para reproducibilidad
- get_logger: crea un logger simple
- ensure_dir: crea directorios si no existen
- train_test_split_fixed: envoltorio consistente para división estratificada
- timer context manager: para medir tiempos
"""
from __future__ import annotations

import os
import random
import time
import contextlib
from typing import Iterator, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42


def set_global_seed(seed: int = RANDOM_STATE) -> None:
    """Fija semillas en random y numpy para reproducibilidad."""
    random.seed(seed)
    np.random.seed(seed)


def get_logger(name: str):
    """Crea un logger simple a stdout con nivel INFO."""
    import logging

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
                                 datefmt="%H:%M:%S")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


@contextlib.contextmanager
def timer(section: str) -> Iterator[None]:
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    print(f"[TIMER] {section}: {end - start:.2f}s")


def train_test_split_fixed(
    df: pd.DataFrame,
    target_col: str = "Survived",
    test_size: float = 0.2,
    random_state: int = RANDOM_STATE,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Realiza una división estratificada train/test con parámetros fijos."""
    X = df.drop(columns=[target_col])
    y = df[target_col].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    return X_train, X_test, y_train, y_test
