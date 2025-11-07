# Asistente LLM para Recomendación de Restaurantes

Prototipo académico que permite hacer consultas en lenguaje natural (p. ej. *“Quiero un italiano barato en El Poblado”*) y devolver restaurantes reales/simulados basados en:
- tipo de cocina (extraído de etiquetas de OpenStreetMap y dataset local),
- rango de precio (heurísticas + datos locales),
- proximidad geográfica (distancia Haversine),
- explicaciones generadas por un LLM local o fallback.

## Requisitos
- Windows / Linux / macOS con Python **3.10+**.
- Conexión a internet para geocodificación y Overpass (opcional si usas solo dataset local).
- Modelo LLM local (opcional, ver abajo). Sin LLM la app usa textos plantilla.

## Instalación Rápida
```powershell
git clone <url-del-repo>
cd llm_restaurant_recommender
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # en Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Configurar el LLM (opciones)

### Opción A: Hugging Face (Phi-3 Mini recomendado)
1. Instala el CLI si no lo tienes: `python -m pip install "huggingface_hub[cli]"`.
2. Inicia sesión con tu token:
   ```powershell
   huggingface-cli login --token <tu-token-hf>
   ```
3. Descarga el modelo:
   ```powershell
   huggingface-cli download microsoft/Phi-3-mini-4k-instruct --local-dir models/phi-3-mini
   ```
4. Indica la ruta a la app (persistente):
   ```powershell
   setx HF_MODEL "llm_restaurant_recommender\models\phi-3-mini"
   ```
   *(Si prefieres usar la caché global de HF, puedes omitir el paso 3 y usar `setx HF_MODEL "microsoft/Phi-3-mini-4k-instruct"`; el modelo se descargará en la primera ejecución.)*

### Opción B: GPT4All
1. `pip install gpt4all`.
2. Descarga un modelo `.bin` desde <https://gpt4all.io/models/>.
3. Define `GPT4ALL_MODEL_PATH` con la ruta al archivo o ajusta `models/local_model_integration.py`.

### Sin LLM
Si no hay modelo disponible, el sistema genera explicaciones cortas usando una plantilla: la app sigue funcionando (no se detiene).

## Datos
- `data/restaurants_sample.csv`: muestra de restaurantes con coordenadas y etiquetas (puedes regenerar con `python data/generate_dataset.py`).
- `data/generated_reviews.csv`: espacio para reseñas simuladas (opcional, actualmente vacío).
- `utils/geolocation.py` combina resultados de Overpass y el CSV local; si hay datos locales, se fusionan y se eliminan duplicados.

**Importante:** Los pesos de los modelos (varios GB) están ignorados (`models/phi-3-mini/`). Cada desarrollador debe descargarlos localmente siguiendo los pasos anteriores.

## Ejecución
```powershell
streamlit run app.py
```

### Flujo Interno
1. `app.py` recibe la consulta y parámetros (radio, top-k).
2. `utils.llm_processing.analyze_query` detecta cocina, rango de precio y ubicación.
3. `utils.geolocation.search_restaurants` geocodifica y consulta Overpass + dataset local (con cache en Streamlit).
4. `utils.ranking.rank_restaurants` puntúa por distancia, coincidencia de cocina, afinidad de precio y rating.
5. `utils.llm_processing.generate_explanations` produce explicaciones (LLM o plantilla) y la UI las muestra.

## Desarrollo y Pruebas
- Recomendado crear un entorno virtual y activar formateo/linters.
- Puedes extender el dataset local con campos `rating`, `price_range`, etc.
- Pendiente: añadir pruebas unitarias (`pytest`) para `analyze_query`, `rank_restaurants` y `resolve_location` (mockeando APIs).
- Para evitar límites de Overpass, ajusta el radio o usa el dataset local como fallback.

## Próximos pasos sugeridos
- Agregar visualización en mapa (folium/streamlit-folium).
- Enriquecer `generated_reviews.csv` y mostrar reseñas/resúmenes con el LLM.
- Documentar benchmarks y requisitos de hardware del modelo elegido.
- Automatizar la descarga del modelo vía script cuando sea viable.

## Créditos y Licencia
- Datos: OpenStreetMap (Overpass API) y datasets generados por los autores.
- Modelo recomendado: Microsoft Phi-3 Mini 4K Instruct (licencia MIT, ver repositorio de Hugging Face).
- Licencia sugerida para este proyecto: MIT (ajusta según necesidades académicas).

Para dudas adicionales o contribuciones, abre un issue o contacta al equipo del curso.
