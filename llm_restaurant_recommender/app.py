import streamlit as st
import pandas as pd

from utils.geolocation import geocode_location, search_restaurants_overpass
from utils.llm_processing import parse_query, generate_explanations
from utils.ranking import rank_restaurants

st.set_page_config(page_title="Asistente LLM - Recomendador de Restaurantes", layout="centered")

st.title("Asistente LLM: Recomendador de restaurantes (OpenStreetMap)")

with st.form("query_form"):
    user_query = st.text_input("¿Qué buscas?", placeholder="Ej: Quiero un restaurante italiano barato cerca del Poblado")
    radius = st.number_input("Radio de búsqueda (metros)", value=1500, min_value=200, max_value=10000, step=100)
    top_k = st.number_input("Máximo resultados", value=5, min_value=1, max_value=20)
    submitted = st.form_submit_button("Buscar")

if submitted and user_query.strip():
    st.info("Procesando consulta...")
    prefs = parse_query(user_query)
    st.write("Preferencias detectadas:", prefs)

    # Resolve location
    loc_text = prefs.get("location") or ""
    if not loc_text:
        st.warning("No se detectó ubicación en la consulta. Por favor añade una ubicación (ej: 'Poblado').")
    coords = None
    if loc_text:
        coords = geocode_location(loc_text)
        if coords is None:
            st.error(f"No pude geocodificar la ubicación: {loc_text}")
        else:
            st.write(f"Ubicación: {loc_text} → {coords}")

    if coords is not None:
        df = search_restaurants_overpass(coords[0], coords[1], radius, cuisine=prefs.get("cuisine"))
        if df.empty:
            st.warning("No se encontraron restaurantes en la zona con esos criterios.")
        else:
            df_ranked = rank_restaurants(df, prefs)
            top = df_ranked.head(int(top_k)).copy()

            # Generate explanations (LLM or fallback)
            explanations = generate_explanations(user_query, top.to_dict(orient="records"))
            top["explanation"] = explanations

            for idx, row in top.iterrows():
                with st.expander(f"{row.get('name','(sin nombre)')} — {row.get('distance_m', '?')} m"):
                    st.write("Cocina:", row.get("cuisine", "—"))
                    st.write("Dirección / tags:", row.get("tags", {}))
                    st.write(row.get("explanation", ""))

            st.success(f"Mostrando {len(top)} resultados.")

else:
    st.write("Introduce una consulta en lenguaje natural arriba y presiona 'Buscar'.")
