import streamlit as st
import config
import math

from utils.geolocation import resolve_location, search_restaurants
from utils.llm_processing import analyze_query, generate_explanations
from utils.logger import get_logger
from utils.ranking import rank_restaurants

logger = get_logger(__name__)

st.set_page_config(page_title="Asistente LLM - Restaurantes Yelp", layout="centered")

st.title("Asistente LLM: Recomendador de restaurantes (Yelp Dataset)")


@st.cache_data(show_spinner=False, ttl=config.SEARCH_CACHE_TTL)
def cached_restaurant_search(location_key, cuisine, radius):
    return search_restaurants(location_key, cuisine=cuisine, radius=radius)

with st.form("query_form"):
    user_query = st.text_input("¿Qué buscas?", placeholder="Ej: Quiero una pizza económica en Philadelphia")
    manual_location = st.text_input("Ubicación (opcional, si no se detecta automáticamente):", placeholder="Ej: Philadelphia, PA")
    radius = st.number_input(
        "Radio de búsqueda (metros)",
        value=int(config.DEFAULT_SEARCH_RADIUS),
        min_value=int(config.MIN_SEARCH_RADIUS),
        max_value=int(config.MAX_SEARCH_RADIUS),
        step=100,
    )
    top_k = st.number_input(
        "Máximo resultados",
        value=int(config.DEFAULT_TOP_K),
        min_value=1,
        max_value=int(config.MAX_TOP_K),
    )
    submitted = st.form_submit_button("Buscar")

if submitted and user_query.strip():
    # Validate query length
    if len(user_query) < int(config.MIN_QUERY_LENGTH):
        st.error("❌ La consulta es demasiado corta. Por favor, proporciona más detalles.")
        st.stop()
    
    if len(user_query) > int(config.MAX_QUERY_LENGTH):
        st.warning("⚠️ La consulta es muy larga. Se procesará solo los primeros 500 caracteres.")
        user_query = user_query[: int(config.MAX_QUERY_LENGTH)]
    
    logger.info(f"Processing query: {user_query[:100]}...")
    st.info("Procesando consulta...")
    
    try:
        prefs = analyze_query(user_query)
        st.write("Preferencias detectadas:", prefs)
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        st.error("❌ Error al analizar la consulta. Por favor, intenta de nuevo.")
        st.stop()

    # Determine location: use detected location or manual input
    loc_text = prefs.get("location") or manual_location.strip()
    
    coords = None
    if not loc_text:
        st.warning("⚠️ No se detectó ubicación en la consulta ni se proporcionó manualmente. Por favor, especifica una ubicación.")
        logger.warning("No location provided")
    else:
        try:
            coords = resolve_location(loc_text)
            if coords is None:
                st.error(f"❌ No pude geocodificar la ubicación: {loc_text}")
                logger.warning(f"Failed to geocode: {loc_text}")
            else:
                st.success(f"✅ Ubicación resuelta: {loc_text} → ({coords[0]:.4f}, {coords[1]:.4f})")
                logger.info(f"Location resolved: {loc_text} -> {coords}")
        except Exception as e:
            logger.error(f"Error resolving location: {e}")
            st.error("❌ Error al procesar la ubicación. Por favor, verifica e intenta de nuevo.")

    if coords is not None:
        try:
            # Call cached search (handles remote API + dataset fallback)
            logger.info(f"Searching restaurants (radius={radius}m, cuisine={prefs.get('cuisine')})")
            df = cached_restaurant_search((coords[0], coords[1]), cuisine=prefs.get("cuisine"), radius=radius)
            
            if df.empty:
                st.warning("No se encontraron restaurantes en la zona con esos criterios.")
                logger.info("No restaurants found")
            else:
                logger.info(f"Found {len(df)} restaurants")
                
                # Rank using user coordinates
                try:
                    df_ranked = rank_restaurants(df, prefs, user_coords=coords)
                    top = df_ranked.head(int(top_k)).copy()
                    logger.info(f"Ranked and selected top {len(top)} restaurants")
                except Exception as e:
                    logger.error(f"Error ranking restaurants: {e}")
                    st.error("❌ Error al ordenar los restaurantes.")
                    st.stop()

                # Optional: generate explanations with LLM (can be slow on CPU)
                explain = st.checkbox("Generar explicaciones con LLM (lento en CPU)", value=False)
                if explain:
                    try:
                        explanations = generate_explanations(user_query, top.to_dict(orient="records"))
                        top["explanation"] = explanations
                    except Exception as e:
                        logger.error(f"Error generating explanations: {e}")
                        top["explanation"] = ["Información no disponible"] * len(top)
                else:
                    top["explanation"] = [""] * len(top)

                st.subheader(f"Top {len(top)} resultados")
                for idx, row in top.iterrows():
                    name = row.get("name") or "(sin nombre)"
                    address = row.get("address") or "Dirección no disponible"
                    # distance may be NaN; convert safely
                    _d = row.get("distance_m")
                    try:
                        _dv = float(_d) if _d is not None else 0.0
                        dist = 0 if math.isnan(_dv) else int(_dv)
                    except Exception:
                        dist = 0
                    price_range = row.get("price_range") or row.get("price") or "precio no disponible"
                    opening = row.get("opening_hours") or "Horario no informado"
                    source = row.get("source") or "fuente desconocida"
                    explanation = row.get("explanation") or ""
                    with st.expander(f"{name} — {dist} m"):
                        st.markdown(f"**{name}**")
                        st.write(address)
                        st.write(f"Distancia: {dist} m")
                        st.write(f"Precio estimado: {price_range}")
                        st.write(f"Horario: {opening}")
                        st.write(explanation)
                        st.caption(f"Fuente de datos: {source}")

                st.success(f"Mostrando {len(top)} resultados.")
        
        except Exception as e:
            logger.error(f"Error during restaurant search: {e}")
            st.error("❌ Error al buscar restaurantes. Por favor, intenta de nuevo.")
            st.stop()

else:
    st.write("Introduce una consulta en lenguaje natural arriba y presiona 'Buscar'.")
    
    st.markdown("---")
    st.markdown("### 📊 Información del Dataset")
    st.markdown("""
    - **Fuente:** Yelp Dataset (Hugging Face)
    - **Ciudad:** Philadelphia, PA
    - **Restaurantes:** 318 establecimientos abiertos
    - **Tipos de cocina:** 103 diferentes
    - **Rating promedio:** 3.58/5.0
    
    **Ejemplos de búsqueda:**
    - "Quiero una pizza barata"
    - "Busco un café cerca de la estación"
    - "Restaurante chino con buen rating"
    - "Sushi bar recomendado"
    """)
