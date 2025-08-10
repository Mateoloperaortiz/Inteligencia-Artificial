# Ejercicio 1

A partir del Notebook "2.BestFirstSearch.ipynb" de la semana 2, resolver el problema que soluciona la ruta óptima hasta Bucharest, mediante el algoritmo de A*Search usando la heurística.

El README.md debe explicar:
• El análisis del problema.
• Cómo se aplica A*
• ¿Por qué se considera que la ruta encontrada es óptima?


# Ejercicio 1 – Búsqueda A* para encontrar la ruta óptima a Bucharest

## 📌 Análisis del problema

El objetivo de este ejercicio es encontrar la ruta más corta desde una ciudad inicial (en este caso, **Arad**) hasta la ciudad de **Bucharest**, dentro de un grafo que representa el mapa de Rumania. Este grafo contiene ciudades como nodos y las distancias entre ellas como pesos en los bordes.


**Características del problema:**
- **Estado inicial**: `problem.initial` = `Arad`
- **Estado objetivo**: `problem.goal` = `Bucharest`
- **Acciones**: `Problem.actions(state)` devuelve las ciudades conectadas
- **Costo**: `Problem.path_cost(from_node, to_node)` devuelve la distancia en kilómetros entre ciudades
- **Heurística**: `heuristic[city]` = distancia en línea recta desde cada ciudad hasta Bucharest


---

## 🚀 ¿Cómo se aplica A* en este problema?

El algoritmo A* busca el camino con el menor costo estimado usando la fórmula:

```
f(n) = g(n) + h(n)
```


Donde:
- **g(n)** → `current.path_cost`: costo real acumulado desde el nodo inicial hasta el nodo actual.
- **h(n)** → `heuristic[child.state]`: distancia estimada desde la ciudad actual hasta Bucharest.
- **f(n)** → `total_cost + heuristic[child.state]`: costo total estimado usado como prioridad en la cola.

**Implementación del algoritmo `astar_search`:**
1. **Inicialización** → Crear `Node(problem.initial)` con `path_cost = 0` y agregarlo a la `frontier` con prioridad `heuristic[problem.initial]`.
2. **Frontera** → Cola de prioridad (`heapq`) que selecciona el nodo con menor `f(n)`.
3. **Expansión** → Extraer el nodo con menor `f(n)` y verificar si cumple `problem.goal_test(state)`.
4. **Exploración** → Para cada ciudad vecina (`action`), generar un nuevo `Node` con:
   - `child.state` = ciudad vecina
   - `child.parent` = nodo actual
   - `child.path_cost` = costo acumulado
5. **Evaluación** → Calcular `f_child = child.path_cost + heuristic[child.state]` y añadirlo a la `frontier`.
6. **Terminación** → Devolver el nodo cuando `problem.goal_test(state)` sea verdadero.

**Estructuras de datos utilizadas:**
- **Clase `Problem`** → Define el espacio de estados y las transiciones.
- **Clase `Node`** → Representa cada paso de la búsqueda con referencias a su nodo padre.
- **Cola de prioridad** → Implementada con `heapq` para seleccionar el nodo más prometedor.

---

## ✅ ¿Por qué la ruta encontrada se considera óptima?

La heurística `heuristic` usada (distancia en línea recta a Bucharest) es:
- **Admisible** → Nunca sobreestima el costo real restante.
- **Consistente** → Cumple que `h(n) ≤ c(n, a, n') + h(n')`, evitando retrocesos innecesarios.

**Propiedades de A*:**
- **Completitud** → Encuentra solución si existe.
- **Optimalidad** → Con heurística admisible y consistente, siempre devuelve la ruta de menor `path_cost`.
- **Eficiencia** → Reduce el número de nodos explorados al usar `heuristic` para guiar la búsqueda.

**Resultado obtenido:**
- **Ruta**: `Arad → Sibiu → Rimnicu Vilcea → Pitesti → Bucharest`
- **Costo total (`path_cost`)**: `418 km`




---
