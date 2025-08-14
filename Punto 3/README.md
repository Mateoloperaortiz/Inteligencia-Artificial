## Ejercicio 3 – Navegación en la Red de Metro

### Objetivo

En este ejercicio implementé dos estrategias de búsqueda, BFS (búsqueda en anchura) e IDS (búsqueda de profundización iterativa), para hallar la ruta con menos estaciones (menor número de acciones) entre dos estaciones del metro. Además, comparé tiempo de ejecución y memoria utilizada.

La red tiene 10 estaciones (A–J) y las conexiones dadas en `problema.md`. Se asume costo uniforme entre estaciones (grafo no ponderado).

### Modelado del problema

- Representación: lista de adyacencia en `ProblemaMetro.grafo`.
- Costo: cada movimiento entre estaciones cuesta 1.
- Estado inicial y objetivo: se parametrizan en las funciones de búsqueda (por defecto A → J).

### Implementación (archivo `Punto 3/metro_search.py`)

- `Nodo`: modela un estado con `estado`, `padre`, `accion` y `profundidad`. Permite reconstruir la ruta con `obtener_camino()`.
- `ProblemaMetro`: expone `acciones(estado)` y `resultado(estado, accion)` sobre el grafo.
- `busqueda_en_anchura` (BFS): explora nivel por nivel y garantiza el camino más corto en grafos no ponderados. Optimicé la verificación de pertenencia a la cola con `estados_frontera` (set) para O(1).
- `busqueda_limitada_en_profundidad` (DLS): DFS con límite de profundidad. Evita ciclos por rama usando `conjunto_camino` (sin conjunto global de explorados).
- `busqueda_de_profundizacion_iterativa` (IDS): corre DLS con límites crecientes (0, 1, 2, …) y acumula `nodos_explorados`.
- Métricas: tiempo con `time` y memoria con `tracemalloc` (`memoria_actual` y `memoria_pico`).

### Cómo ejecutar

Requisitos: Python 3.

```bash
python3 "Punto 3/metro_search.py"
```

### Resultados de ejemplo (A → J)

Pueden variar ligeramente por equipo, pero el camino mínimo debe coincidir.

- BFS: camino `A -> C -> F -> J` (longitud 3), nodos explorados: ~6.
- IDS: camino `A -> C -> F -> J` (longitud 3), nodos explorados: ~20, profundidad máxima: 3.

### Comparación y conclusiones

- BFS: garantiza el camino mínimo en grafos no ponderados; suele ser más rápido cuando la solución está poco profunda; usa más memoria por la frontera.
- IDS: memoria más contenida (similar a DFS) y completo; puede ser más lento por reexploración.

En esta red ambos métodos encuentran la misma ruta óptima `A → C → F → J` con 3 movimientos. En mis pruebas, BFS exploró menos nodos y fue un poco más rápido, mientras que IDS tuvo menor huella de memoria pico.
