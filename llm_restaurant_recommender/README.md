# Asistente LLM - Recomendador de Restaurantes (local / gratis)

Prototipo en Python que usa OpenStreetMap/Overpass para buscar restaurantes y genera explicaciones cortas con un LLM local o un fallback.

Requisitos
- Python 3.10+
- Paquetes: ver `requirements.txt` (instalación reseñada abajo)
- No se usan APIs de pago por defecto.

Cómo ejecutar
1. Crear y activar un entorno virtual (ejemplo PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Ejecutar la app:

```powershell
streamlit run app.py
```

Modelos LLM
- El módulo `models/local_model_integration.py` intenta usar `gpt4all` si está instalado y si tienes un modelo en local.
- Si no quieres instalar un modelo, el sistema usa un fallback basado en plantillas para generar explicaciones.

Opciones para usar un LLM local (manual):
1. Instalar GPT4All: sigue las instrucciones oficiales (https://gpt4all.io) y luego `pip install gpt4all`.
2. Colocar el modelo en la ruta que espere `gpt4all` o modificar `models/local_model_integration.py` para apuntar al archivo del modelo.

Notas sobre Overpass
- No requiere clave. El endpoint público se usa por defecto (`overpass-api.de`). Respeta los límites de uso.

Estructura
```
llm_restaurant_recommender/
├── app.py
├── utils/
│   ├── geolocation.py
│   ├── llm_processing.py
│   └── ranking.py
├── data/
│   ├── restaurants_sample.csv
│   └── generated_reviews.csv
├── models/
│   └── local_model_integration.py
├── .cursor/
│   └── rules/core.md
└── README.md
```

¿Qué hago por ti ahora?
- Puedo ayudar a configurar un modelo local (darte los comandos para descargar e instalar GPT4All) o adaptar la integración a otro motor gratuito (Hugging Face). Dime si quieres que cree instrucciones concretas para alguno de ellos.
