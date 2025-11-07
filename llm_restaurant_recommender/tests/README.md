# Tests

Este directorio contiene pruebas unitarias para el proyecto.

## Ejecutar Tests

```powershell
# Ejecutar todos los tests
uv run pytest

# Ejecutar tests con verbose
uv run pytest -v

# Ejecutar tests con coverage
uv run pytest --cov=utils --cov=models

# Ejecutar un archivo específico
uv run pytest tests/test_ranking.py

# Ejecutar un test específico
uv run pytest tests/test_ranking.py::TestHaversineMeters::test_same_point
```

## Estructura de Tests

- `test_common.py`: Tests para utilidades comunes (safe_parse_tags)
- `test_ranking.py`: Tests para funciones de ranking y distancia
- `test_llm_processing.py`: Tests para procesamiento LLM y análisis de queries

## Cobertura Actual

Los tests cubren:
- ✅ Funciones de utilidades comunes
- ✅ Cálculo de distancia Haversine
- ✅ Ranking de restaurantes
- ✅ Análisis de queries
- ✅ Generación de explicaciones fallback

## Próximas Pruebas

Pendiente agregar:
- Tests para geolocalización (con mocking de APIs)
- Tests para rate limiter
- Tests de integración end-to-end
- Tests de performance
