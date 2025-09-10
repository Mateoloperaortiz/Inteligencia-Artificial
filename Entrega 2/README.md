# Actividad 2 — Machine Learning Supervisado (Titanic)

Este repositorio contiene la solución completa para la Actividad 2.
Se sigue la estructura, criterios y lineamientos definidos en el taller (`taller2.md`) y en las reglas del proyecto.

## Integrantes y aportes
- Mateo Lopera
- Camilo Arbelaez

## 1) Descripción del dataset
- Fuente: Titanic (Kaggle)
- Archivo: `data/tested.csv` (contiene la etiqueta `Survived`)
- Objetivo: predecir `Survived` (0 = no sobrevivió, 1 = sobrevivió)
- Número de registros: 419
- Variables (12 columnas):
  - PassengerId (int)
  - Survived (int)
  - Pclass (int)
  - Name (str)
  - Sex (str)
  - Age (float)
  - SibSp (int)
  - Parch (int)
  - Ticket (str)
  - Fare (float)
  - Cabin (str)
  - Embarked (str)

## 2) Preprocesamiento realizado
- Limpieza e imputación de faltantes:
  - Numéricas: mediana
  - Categóricas: moda (más frecuente)
- Codificación de variables categóricas: One-Hot Encoding (handle_unknown="ignore")
- Escalado: StandardScaler para modelos que lo requieren (MLP)
- División Train/Test: 80/20 estratificada con `random_state=42`
- Ingeniería de variables Titanic:
  - `FamilySize = SibSp + Parch + 1`
  - `IsAlone = 1 si FamilySize == 1, si no 0`
  - `Title` extraído de `Name` (Mr, Mrs, Miss, Master, Rare)
  - `Deck` = primera letra de `Cabin` (NaN -> "U")
  - `TicketPrefix` = prefijo alfanumérico de `Ticket` (si no -> "NONE")

## 3) Modelos entrenados
- Clásico: RandomForestClassifier (`class_weight="balanced"`), selección por RandomizedSearchCV
- Red Neuronal: MLPClassifier (preprocesamiento escalado, GridSearchCV, `early_stopping=True`)
- Adicional: HistGradientBoostingClassifier (búsqueda pequeña). Si `xgboost` está disponible, también se entrena `XGBClassifier`.

## 4) Evaluación de resultados
- Métricas: Accuracy, Precision, Recall, F1 (macro, weighted), ROC-AUC
- Curvas/Visualizaciones: Matriz de confusión, ROC, PR
- Validación cruzada: se guardan `cv_results_*.csv`
- Importancia de variables: para modelos de árboles (RF / HGB)
- Reportes en `reports/figures/` y `reports/metrics/`

## 5) Análisis comparativo
Se genera una tabla consolidada en `reports/metrics/metrics_summary.json` y visualizaciones en `reports/figures/`. El notebook `02_modeling.ipynb` resume y comenta los hallazgos.

Tabla de métricas (test) a partir de `reports/metrics/metrics_summary.json`:

| Modelo | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | ROC-AUC | AP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RF | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| HGB | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| MLP | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## 6) Conclusiones
Se discuten las técnicas más adecuadas, ventajas/desventajas y trabajo futuro en el README final y el notebook de modelado.

## Requisitos / Instalación
```
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

## Comandos de ejemplo
- Entrenar los 3 modelos:
```
python -m src.train --data data/tested.csv --models rf mlp hgb --save_dir models
```
- Evaluar y generar reportes:
```
python -m src.evaluate --data data/tested.csv --models_dir models --out_dir reports
```
- Predecir:
```
python -m src.predict --model models/rf.pkl --input data/tested.csv --output predictions.csv
```

## Estructura del repositorio
```
data/
  tested.csv
notebooks/
  01_eda.ipynb
  02_modeling.ipynb
src/
  features.py
  train.py
  evaluate.py
  predict.py
  utils.py
models/
reports/
  figures/
  metrics/
```
