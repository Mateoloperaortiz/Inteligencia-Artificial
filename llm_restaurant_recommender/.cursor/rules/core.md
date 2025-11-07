# Reglas internas de prompting y comportamiento — Asistente LLM Recomendador de Restaurantes

Propósito
-------
Definir reglas claras y reproducibles para cómo el asistente interpreta consultas en lenguaje natural, qué formato debe tener la salida (JSON) y cómo generar explicaciones breves para cada restaurante. Estas reglas son la referencia para construir prompts a LLMs locales o para el comportamiento por defecto (fallback templates).

1) Interpretación de consultas del usuario
-----------------------------------------
Reglas generales:
- El asistente debe extraer tres tipos principales de preferencia cuando sea posible: cocina (ej. "italiano"), ubicación (ej. "El Poblado", "cerca de Laureles"), y preferencia de precio (ej. "barato", "económico", "lujoso").
- Usar heurísticas en este orden: (a) coincidencias por palabra clave para cocina y precio, (b) expresiones preposicionales para ubicación (ej. "cerca de X", "en X"), (c) nombres de barrios/zonas conocidos como fallback.

Detección de cocina:
- Buscar palabras clave comunes en español (ej: italiano, chino, japonés/japones, sushi, mexicano, vegetariano, vegano, pizza, hamburguesa, peruano, francés/frances).
- Si aparecen varias, priorizar la primera mencionada.

Detección de precio:
- Detectar palabras: "barato", "económico", "barata", "económico" → price: "low".
- Detectar palabras: "caro", "costoso", "lujoso" → price: "high".
- Si no hay indicativo, price: "any".

Detección de ubicación:
- Buscar patrones regex como `cerca de (.+)`, `en (.+)`, `por (.+)` (adaptar para variantes).
- Limpiar capturas de palabras clave (eliminar adjetivos de precio o conectores al final).
- Si no se detecta una ubicación explícita, intentar detectar nombres de barrios/zonas preconfiguradas (lista local: Poblado, Centro, Laureles, Envigado, Belén). Si tampoco, dejar location vacío para pedir aclaración.

2) Formato de salida JSON
-------------------------
El asistente debe devolver una lista JSON (array) con objetos para cada restaurante. Cada objeto debe tener las claves exactas que se indican a continuación. Siempre producir JSON válido (no texto libre junto al JSON).

Esquema (cada elemento):
- id: string|int — identificador único del elemento (si proviene de OSM usar el id; si es local, usar un índice único).
- name: string — nombre del restaurante (o cadena vacía si desconocido).
- cuisine: string — tipo de cocina principal detectada (o cadena vacía si desconocido).
- lat: number — latitud (float) si está disponible, null si no.
- lon: number — longitud (float) si está disponible, null si no.
- distance_m: integer — distancia en metros desde la ubicación consultada (si está calculada), null si no.
- score: number — puntuación interna de relevancia (0..+inf, heurística interna).
- tags: object — diccionario con tags/pares clave-valor recogidos de la fuente (puede estar vacío `{}`).
- explanation: string — explicación breve generada por el LLM o fallback (1-2 oraciones en español).

Ejemplo de salida JSON (formato):
```
[
	{
		"id": 123456,
		"name": "Pizzería Da Marco",
		"cuisine": "italiano",
		"lat": 6.2100,
		"lon": -75.5710,
		"distance_m": 450,
		"score": 1.234,
		"tags": {"addr:street":"Cra 35","price":"$"},
		"explanation": "Pizzería Da Marco: excelente pizza napolitana a poca distancia; buena opción para grupos y con precios moderados."
	}
]
```

3) Generación de explicaciones cortas (por restaurante)
-------------------------------------------------------
Reglas estilísticas:
- Longitud: 1–2 oraciones (aprox. 10–30 palabras). En español.
- Contenido mínimo: mencionar la cocina o característica principal y por qué es relevante para la consulta (ej. coincidencia de cocina o cercanía).
- Incluir, si es aplicable, un consejo práctico breve (ej.: "reservar", "pedir mesa en la terraza", "prueba la pizza al horno").
- Si la consulta incluye preferencia de precio, reflejarlo: resaltar si parece una "posible opción económica" o indicar desconocimiento si no hay datos.
- Evitar inventar hechos no presentes en los datos (ej.: horarios, menús extensos, premios). Si algo no está disponible, indicar claramente "información no disponible" o evitar afirmaciones precisas.

Reglas de seguridad y veracidad:
- No inventar información que no provenga de la fuente de datos ni del prompt.
- Si la confianza en la información es baja (p. ej., data missing), prefijar con frases como "Según los datos disponibles," o "Posible opción:".

Plantilla de prompt recomendada para LLMs (usar variables):
```
Eres un asistente conciso en español. Usuario: '<USER_QUERY>'. Restaurante: <NAME>, cocina: <CUISINE>, distancia: <DISTANCE> m, tags: <TAGS>. Genera una explicación corta en español (1-2 oraciones) que:
- Explique por qué el restaurante es relevante para la consulta.
- Incluya un consejo práctico breve.
- No invente horarios ni precios exactos; si falta información, indica "información no disponible".
Respuesta (solo la explicación):
```

4) Prioridad y ordenamiento semántico
-------------------------------------
- El sistema prioriza coincidencia de cocina y cercanía (distancia) en ese orden.
- Si la consulta explícitamente pide precio bajo, aplicar un pequeño sesgo positivo a restaurantes con tags que sugieran menor precio.

5) Errores y respuestas cuando falta información
------------------------------------------------
- Si no se detecta ubicación, el asistente debe pedir al usuario que la aclare en una frase corta (ej.: "¿En qué zona te encuentras o cerca de qué lugar?").
- Si Overpass o la fuente de datos falla, devolver un JSON vacío `[]` y una explicación humana aparte en la UI (no en el JSON) indicando el fallo.

6) Formato final y consumo por la UI
-----------------------------------
- La UI espera recibir el JSON descrito arriba. El campo `explanation` debe estar ya en español y listo para mostrarse sin post-procesado adicional.

7) Ejemplos rápidos (casos de uso)
----------------------------------
- Query: "Quiero un restaurante italiano barato cerca del Poblado"
	- Extracción: cuisine: "italiano", price: "low", location: "Poblado"
	- Salida: lista de restaurantes italianos cercanos, cada uno con `explanation` destacando cocina y posible economía.

8) Notas de mantenimiento
-------------------------
- Mantener actualizada la lista local de barrios/zonas para mejorar la detección de ubicación.
- Si se integra un LLM externo/local distinto, conservar las plantillas y reglas; ajustar el prompt sólo para el formato esperado.

---
Versión: 1.0 — Reglas por defecto para el prototipo local. Mantener claras las equivalencias entre campos del JSON y los tags de OSM.

