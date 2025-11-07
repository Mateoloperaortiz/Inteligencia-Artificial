# 🍕 Asistente LLM para Recomendación de Restaurantes

**Proyecto Académico de Inteligencia Artificial**  
*Por: Mateo Lopera & Camilo Arbelaez*

---

## ¿Qué es esto?

Un asistente inteligente que entiende tus antojos en lenguaje natural y te recomienda restaurantes reales. Le dices algo como *"Quiero pizza económica en Filadelfia"* y te muestra opciones cercanas con explicaciones personalizadas.

**¿Cómo lo hace?**
- 🧠 **LLM Local (Phi-4):** Entiende tu consulta y genera explicaciones naturales
- 🗺️ **Datos Reales:** 318 restaurantes de Yelp en Philadelphia + OpenStreetMap
- 📍 **Geolocalización:** Busca lo más cerca posible de donde estés
- ⭐ **Ranking Inteligente:** Considera distancia, precio, rating y tipo de cocina

## 📋 Requisitos

- Python **3.10+** (Windows / Linux / macOS)
- Conexión a internet (para geocodificación y Overpass API)
- ~8 GB de espacio para el modelo Phi-4 (opcional)
- 8 GB de RAM mínimo (16 GB recomendado para el LLM)

## 🚀 Instalación Rápida
```powershell
git clone <url-del-repo>
cd llm_restaurant_recommender
uv venv
.\.venv\Scripts\Activate.ps1   # en Linux/Mac: source .venv/bin/activate
uv pip install "streamlit>=1.20,<2.0" "pandas>=2.0.0,<3.0" "requests>=2.31.0,<3.0" "geopy>=2.3.0,<3.0"
```

**Nota:** Este proyecto usa `uv` como gestor de paquetes para instalación más rápida.

## 🤖 Configurar el LLM (Phi-4)

Este proyecto usa **Phi-4 Mini** de Microsoft a través de Hugging Face Transformers.

1. Instala las dependencias (incluidas en requirements.txt):
   ```powershell
   uv pip install -r requirements.txt
   ```

2. Inicia sesión con tu token de Hugging Face:
   ```powershell
   hf login --token <tu-token-hf>
   ```
   *Obtén tu token en: https://huggingface.co/settings/tokens*

3. Descarga el modelo Phi-4:
   ```powershell
   hf download microsoft/Phi-4-mini-instruct
   ```
   *El modelo se descargará en la caché de HF (~7.7 GB, ~10-15 min)*

4. Configura la variable de entorno:
   ```powershell
   setx HF_MODEL "microsoft/Phi-4-mini-instruct"
   ```
   *O para la sesión actual: `$env:HF_MODEL = "microsoft/Phi-4-mini-instruct"`*

### Sin configurar el modelo
Si no configuras `HF_MODEL` o no instalas transformers, el sistema genera explicaciones usando plantillas simples. La app sigue funcionando sin el LLM.

## 📊 Datos

### Dataset Principal: Yelp (Hugging Face)
- **Fuente:** `hf://datasets/jaimik69/Yelp-Restaurant-Dataset/restaurants.csv`
- **Archivo local:** `data/restaurants_yelp.csv` (318 restaurantes de Philadelphia)
- **Columnas:** name, lat, lon, cuisine, rating, price_range, tags, city, address
- **Características:** 
  - ✅ Coordenadas GPS reales
  - ✅ Ratings de usuarios (1-5 estrellas)
  - ✅ 103 tipos de cocina diferentes
  - ✅ Atributos (delivery, parking, outdoor seating)

### Cómo Generar Nuevo Dataset
Para usar otra ciudad o más restaurantes:
```powershell
# Edita convert_yelp_dataset.py y cambia los parámetros:
# city_filter='Tampa'  # o 'Indianapolis', 'Nashville', etc.
# limit=1000           # cantidad de restaurantes

uv run python convert_yelp_dataset.py
```

### Otros Archivos
- `data/restaurants_sample.csv`: dataset antiguo (Medellín, ejemplo pequeño)
- `data/generated_reviews.csv`: espacio para reseñas simuladas (opcional, vacío)
- `utils/geolocation.py` combina resultados de Overpass API y el dataset local

**Importante:** Los pesos de los modelos (varios GB) están ignorados en git. Los modelos se almacenan automáticamente en la caché de Hugging Face (`~/.cache/huggingface/` en Linux/Mac, `C:\Users\<user>\.cache\huggingface\` en Windows). Cada desarrollador debe descargarlos siguiendo los pasos anteriores.

## ▶️ Ejecución
```powershell
# Configurar el modelo (si no usaste setx)
$env:HF_MODEL = "microsoft/Phi-4-mini-instruct"

# Ejecutar la app
uv run streamlit run app.py
```

**Alternativa sin activar entorno:**
```powershell
uv run streamlit run app.py
```

### 🔄 Cómo funciona por dentro

1. **Entrada:** Recibes la consulta en lenguaje natural (ej: "pizza barata")
2. **Análisis:** El LLM extrae cocina, precio y ubicación de tu texto
3. **Búsqueda:** Geocodifica la ubicación y busca restaurantes en Yelp + OpenStreetMap
4. **Ranking:** Puntúa cada restaurante por distancia, cocina, precio y rating
5. **Respuesta:** Genera explicaciones personalizadas para cada recomendación

## 🧪 Tests y Validación

Implementamos **19 tests unitarios** con **36% de cobertura** (y subiendo):

```powershell
# Ejecutar todos los tests
uv run pytest -v

# Con reporte de cobertura
uv run pytest --cov=utils --cov=models --cov-report=term-missing

# Generar reporte HTML
uv run pytest --cov=utils --cov=models --cov-report=html
# Luego abre: htmlcov/index.html
```

**Tests implementados:**
- ✅ `test_common.py` - Parsing de tags y utilidades (100% coverage)
- ✅ `test_ranking.py` - Cálculo de distancias y ranking (58% coverage)  
- ✅ `test_llm_processing.py` - Análisis de queries y generación (58% coverage)

### 📝 Ver logs en tiempo real

```powershell
# Ver el archivo de logs
cat logs/app.log

# Últimas 20 líneas
tail -20 logs/app.log
```

## ✨ Mejoras Implementadas

### 🔴 Críticas (completadas)
- ✅ **Flujo de ubicación arreglado** - La app ya no se rompe con ubicaciones
- ✅ **Caché del modelo** - Carga una sola vez (30s → <1s por consulta)
- ✅ **Dependencies completas** - `requirements.txt` y `pyproject.toml` actualizados
- ✅ **Bugs eliminados** - Código redundante limpiado

### 🟡 Importantes (completadas)
- ✅ **Sistema de logging profesional** - Logs a consola + archivo
- ✅ **Rate limiting** - Respeta límites de Nominatim (1/s) y Overpass (2/s)
- ✅ **Código sin duplicados** - Funciones comunes centralizadas
- ✅ **Dataset expandido** - 318 restaurantes reales de Yelp
- ✅ **Tests unitarios** - 19 tests, 36% coverage
- ✅ **Validación completa** - Inputs validados con try-catch

### 🚀 Bonus (completadas)
- ✅ **Configuración centralizada** - Archivo `config.py`
- ✅ **`.gitignore` mejorado** - Archivos grandes ignorados
- ✅ **Integración con UV** - Gestor de paquetes moderno
- ✅ **Actualización a Phi-4** - Modelo más potente

**Ver detalles completos en:** `IMPROVEMENTS.md`

## 🎯 Próximos Pasos (To-Do)

- [ ] Mapa interactivo con Folium
- [ ] Tests de integración con mocking de APIs
- [ ] Caché persistente de Overpass
- [ ] Métricas de performance
- [ ] Soporte multi-idioma (inglés/español)
- [ ] API REST (además de la UI Streamlit)
- [ ] CI/CD con GitHub Actions
- [ ] Docker containerization

## 📈 Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Restaurantes** | 318 (Philadelphia) |
| **Tests** | 19 pasando ✅ |
| **Cobertura** | 36% (subiendo) |
| **Performance LLM** | <1s/consulta (con caché) |
| **Rate Limiting** | ✅ Implementado |
| **Logging** | ✅ Sistema profesional |

## 👥 Autores

**Mateo Lopera** & **Camilo Arbelaez**  
Proyecto Académico - Inteligencia Artificial  
Noviembre 2025

## 🙏 Créditos

- **Datos:** OpenStreetMap (Overpass API) + Yelp Dataset (Hugging Face)
- **Modelo LLM:** Microsoft Phi-4 Mini Instruct (MIT License)
- **Gestor de paquetes:** UV (ultra-rápido)
- **Framework:** Streamlit para la UI

## 📜 Licencia

MIT License - Libre para uso académico y comercial

---

💡 **¿Dudas o sugerencias?** Abre un issue o contáctanos.
