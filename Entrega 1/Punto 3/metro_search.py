from collections import deque
import time
import tracemalloc
from typing import List, Dict, Set, Tuple, Optional, Any


class Nodo:
    def __init__(self, estado: str, padre: Optional['Nodo'] = None, accion: Optional[str] = None, profundidad: int = 0):
        self.estado = estado
        self.padre = padre
        self.accion = accion
        self.profundidad = profundidad
    
    def obtener_camino(self) -> List[str]:
        camino = []
        nodo = self
        while nodo:
            camino.append(nodo.estado)
            nodo = nodo.padre
        return list(reversed(camino))
    
    def __repr__(self):
        return f"Nodo({self.estado}, profundidad={self.profundidad})"


class ProblemaMetro:
    def __init__(self):
        self.grafo = {
            'A': ['B', 'C'],
            'B': ['A', 'D', 'E'],
            'C': ['A', 'F'],
            'D': ['B', 'G'],
            'E': ['B', 'H', 'I'],
            'F': ['C', 'J'],
            'G': ['D'],
            'H': ['E'],
            'I': ['E', 'J'],
            'J': ['F', 'I']
        }
    
    def estado_inicial(self) -> str:
        return 'A'
    
    def es_objetivo(self, estado: str) -> bool:
        return estado == 'J'
    
    def acciones(self, estado: str) -> List[str]:
        return self.grafo.get(estado, [])
    
    def resultado(self, estado: str, accion: str) -> str:
        if accion in self.grafo.get(estado, []):
            return accion
        return estado
    
    def costo_camino(self, camino: List[str]) -> int:
        return len(camino) - 1


def busqueda_en_anchura(problema: ProblemaMetro, inicio: str = 'A', objetivo: str = 'J') -> Tuple[Optional[Nodo], Dict[str, Any]]:
    tiempo_inicio = time.time()
    tracemalloc.start()
    
    nodo_inicial = Nodo(inicio)
    
    if nodo_inicial.estado == objetivo:
        tiempo_fin = time.time()
        memoria_actual, memoria_pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return nodo_inicial, {
            'tiempo': tiempo_fin - tiempo_inicio,
            'memoria_actual': memoria_actual,
            'memoria_pico': memoria_pico,
            'nodos_explorados': 1
        }
    
    frontera = deque([nodo_inicial])
    estados_frontera: Set[str] = {nodo_inicial.estado}
    explorados = set()
    nodos_explorados = 0
    
    while frontera:
        nodo = frontera.popleft()
        estados_frontera.discard(nodo.estado)
        explorados.add(nodo.estado)
        nodos_explorados += 1
        
        for accion in problema.acciones(nodo.estado):
            estado_hijo = problema.resultado(nodo.estado, accion)
            
            if estado_hijo not in explorados and estado_hijo not in estados_frontera:
                nodo_hijo = Nodo(estado_hijo, padre=nodo, accion=accion, profundidad=nodo.profundidad + 1)
                
                if nodo_hijo.estado == objetivo:
                    tiempo_fin = time.time()
                    memoria_actual, memoria_pico = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    return nodo_hijo, {
                        'tiempo': tiempo_fin - tiempo_inicio,
                        'memoria_actual': memoria_actual,
                        'memoria_pico': memoria_pico,
                        'nodos_explorados': nodos_explorados
                    }
                
                frontera.append(nodo_hijo)
                estados_frontera.add(estado_hijo)
    
    tiempo_fin = time.time()
    memoria_actual, memoria_pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return None, {
        'tiempo': tiempo_fin - tiempo_inicio,
        'memoria_actual': memoria_actual,
        'memoria_pico': memoria_pico,
        'nodos_explorados': nodos_explorados
    }


def busqueda_limitada_en_profundidad(problema: ProblemaMetro, inicio: str, objetivo: str, limite: int) -> Tuple[Optional[Nodo], bool, int]:
    def recursiva_blp(nodo: Nodo, limite: int, conjunto_camino: Set[str]) -> Tuple[Optional[Nodo], bool, int]:
        nodos_explorados = 1
        
        if nodo.estado == objetivo:
            return nodo, False, nodos_explorados
        
        if limite == 0:
            return None, True, nodos_explorados
        
        hubo_corte = False
        
        for accion in problema.acciones(nodo.estado):
            estado_hijo = problema.resultado(nodo.estado, accion)
            
            if estado_hijo in conjunto_camino:
                continue
            
            nodo_hijo = Nodo(estado_hijo, padre=nodo, accion=accion, profundidad=nodo.profundidad + 1)
            conjunto_camino.add(estado_hijo)
            resultado, hubo_corte_hijo, nodos_hijo = recursiva_blp(nodo_hijo, limite - 1, conjunto_camino)
            nodos_explorados += nodos_hijo
            conjunto_camino.remove(estado_hijo)
            
            if resultado is not None:
                return resultado, False, nodos_explorados
            if hubo_corte_hijo:
                hubo_corte = True
        
        return None, hubo_corte, nodos_explorados
    
    nodo_inicial = Nodo(inicio)
    return recursiva_blp(nodo_inicial, limite, {inicio})


def busqueda_de_profundizacion_iterativa(problema: ProblemaMetro, inicio: str = 'A', objetivo: str = 'J') -> Tuple[Optional[Nodo], Dict[str, Any]]:
    tiempo_inicio = time.time()
    tracemalloc.start()
    
    total_nodos_explorados = 0
    
    for profundidad in range(100):
        resultado, hubo_corte, nodos_explorados = busqueda_limitada_en_profundidad(problema, inicio, objetivo, profundidad)
        total_nodos_explorados += nodos_explorados
        
        if resultado is not None:
            tiempo_fin = time.time()
            memoria_actual, memoria_pico = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return resultado, {
                'tiempo': tiempo_fin - tiempo_inicio,
                'memoria_actual': memoria_actual,
                'memoria_pico': memoria_pico,
                'nodos_explorados': total_nodos_explorados,
                'profundidad_maxima': profundidad
            }
        
        if not hubo_corte:
            break
    
    tiempo_fin = time.time()
    memoria_actual, memoria_pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return None, {
        'tiempo': tiempo_fin - tiempo_inicio,
        'memoria_actual': memoria_actual,
        'memoria_pico': memoria_pico,
        'nodos_explorados': total_nodos_explorados
    }


def imprimir_resultados(nombre_algoritmo: str, resultado: Optional[Nodo], estadisticas: Dict[str, Any]):
    print(f"\nResultados de {nombre_algoritmo}:")
    print("-" * 50)
    
    if resultado:
        camino = resultado.obtener_camino()
        print(f"Camino encontrado: {' -> '.join(camino)}")
        print(f"Longitud del camino: {len(camino) - 1} estaciones")
    else:
        print("¡No se encontró camino!")
    
    print(f"Tiempo transcurrido: {estadisticas['tiempo']:.6f} segundos")
    print(f"Memoria usada (actual): {estadisticas['memoria_actual'] / 1024:.2f} KB")
    print(f"Memoria usada (pico): {estadisticas['memoria_pico'] / 1024:.2f} KB")
    print(f"Nodos explorados: {estadisticas['nodos_explorados']}")
    
    if 'profundidad_maxima' in estadisticas:
        print(f"Profundidad máxima alcanzada: {estadisticas['profundidad_maxima']}")


def principal():
    problema = ProblemaMetro()
    
    print("Navegación en la Red de Metro - Buscando ruta de A a J")
    print("=" * 50)
    
    resultado_bfs, estadisticas_bfs = busqueda_en_anchura(problema, 'A', 'J')
    imprimir_resultados("Búsqueda en Anchura (BFS)", resultado_bfs, estadisticas_bfs)
    
    resultado_ids, estadisticas_ids = busqueda_de_profundizacion_iterativa(problema, 'A', 'J')
    imprimir_resultados("Búsqueda de Profundización Iterativa (IDS)", resultado_ids, estadisticas_ids)
    
    print("\n\nAnálisis de Comparación:")
    print("=" * 50)
    print(f"Diferencia de tiempo: {abs(estadisticas_bfs['tiempo'] - estadisticas_ids['tiempo']):.6f} segundos")
    print(f"Diferencia de memoria (pico): {abs(estadisticas_bfs['memoria_pico'] - estadisticas_ids['memoria_pico']) / 1024:.2f} KB")
    print(f"Diferencia de nodos explorados: {abs(estadisticas_bfs['nodos_explorados'] - estadisticas_ids['nodos_explorados'])}")

if __name__ == "__main__":
    principal()