import streamlit as st
import pandas as pd

from utils.geolocation import resolve_location, search_restaurants
from utils.llm_processing import analyze_query, generate_explanations
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
    prefs = analyze_query(user_query)
    st.write("Preferencias detectadas:", prefs)

    # Determine location (ask user if not detected)
    loc_text = prefs.get("location") or ""
    if not loc_text:
        loc_text = st.text_input("No detecté ubicación — escribe una ubicación o barrio:")

    coords = None
    if loc_text:
        coords = resolve_location(loc_text)
        if coords is None:
            st.error(f"No pude geocodificar la ubicación: {loc_text}")
        else:
            st.write(f"Ubicación resuelta: {loc_text} → {coords}")

    if coords is not None:
        # Call search_restaurants with either coords or text; our function accepts both
        df = search_restaurants(coords, cuisine=prefs.get("cuisine"), radius=radius)
        if df.empty:
            st.warning("No se encontraron restaurantes en la zona con esos criterios.")
        else:
            # Rank using user coordinates
            df_ranked = rank_restaurants(df, prefs, user_coords=coords)
            top = df_ranked.head(int(top_k)).copy()

            # Generate explanations (LLM or fallback)
            explanations = generate_explanations(user_query, top.to_dict(orient="records"))
            top["explanation"] = explanations

            st.subheader(f"Top {len(top)} resultados")
            for idx, row in top.iterrows():
                name = row.get("name") or "(sin nombre)"
                address = row.get("address") or "Dirección no disponible"
                dist = int(row.get("distance_m") or 0)
                explanation = row.get("explanation") or ""
                with st.expander(f"{name} — {dist} m"):
                    st.markdown(f"**{name}**")
                    st.write(address)
                    st.write(f"Distancia: {dist} m")
                    st.write(explanation)

            st.success(f"Mostrando {len(top)} resultados.")

else:
    st.write("Introduce una consulta en lenguaje natural arriba y presiona 'Buscar'.")
