from collections import deque
import time
import tracemalloc
from typing import List, Dict, Set, Tuple, Optional


class Node:
    def __init__(self, state: str, parent: Optional['Node'] = None, action: Optional[str] = None, depth: int = 0):
        self.state = state
        self.parent = parent
        self.action = action
        self.depth = depth
    
    def get_path(self) -> List[str]:
        path = []
        node = self
        while node:
            path.append(node.state)
            node = node.parent
        return list(reversed(path))
    
    def __repr__(self):
        return f"Node({self.state}, depth={self.depth})"


class MetroProblem:
    def __init__(self):
        self.graph = {
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
    
    def initial_state(self) -> str:
        return 'A'
    
    def goal_test(self, state: str) -> bool:
        return state == 'J'
    
    def actions(self, state: str) -> List[str]:
        return self.graph.get(state, [])
    
    def result(self, state: str, action: str) -> str:
        if action in self.graph.get(state, []):
            return action
        return state
    
    def path_cost(self, path: List[str]) -> int:
        return len(path) - 1


def breadth_first_search(problem: MetroProblem, start: str = 'A', goal: str = 'J') -> Tuple[Optional[Node], Dict[str, any]]:
    start_time = time.time()
    tracemalloc.start()
    
    initial_node = Node(start)
    
    if problem.goal_test(initial_node.state):
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return initial_node, {
            'time': end_time - start_time,
            'memory_current': current,
            'memory_peak': peak,
            'nodes_explored': 1
        }
    
    frontier = deque([initial_node])
    explored = set()
    nodes_explored = 0
    
    while frontier:
        node = frontier.popleft()
        explored.add(node.state)
        nodes_explored += 1
        
        for action in problem.actions(node.state):
            child_state = problem.result(node.state, action)
            
            if child_state not in explored and not any(n.state == child_state for n in frontier):
                child_node = Node(child_state, parent=node, action=action, depth=node.depth + 1)
                
                if problem.goal_test(child_node.state):
                    end_time = time.time()
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    return child_node, {
                        'time': end_time - start_time,
                        'memory_current': current,
                        'memory_peak': peak,
                        'nodes_explored': nodes_explored
                    }
                
                frontier.append(child_node)
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return None, {
        'time': end_time - start_time,
        'memory_current': current,
        'memory_peak': peak,
        'nodes_explored': nodes_explored
    }


def depth_limited_search(problem: MetroProblem, start: str, goal: str, limit: int) -> Tuple[Optional[Node], bool, int]:
    def recursive_dls(node: Node, limit: int, explored: Set[str]) -> Tuple[Optional[Node], bool, int]:
        nodes_explored = 1
        
        if problem.goal_test(node.state):
            return node, False, nodes_explored
        
        if limit == 0:
            return None, True, nodes_explored
        
        cutoff_occurred = False
        explored.add(node.state)
        
        for action in problem.actions(node.state):
            child_state = problem.result(node.state, action)
            
            if child_state not in explored:
                child_node = Node(child_state, parent=node, action=action, depth=node.depth + 1)
                result, cutoff, child_nodes = recursive_dls(child_node, limit - 1, explored.copy())
                nodes_explored += child_nodes
                
                if result is not None:
                    return result, False, nodes_explored
                if cutoff:
                    cutoff_occurred = True
        
        return None, cutoff_occurred, nodes_explored
    
    initial_node = Node(start)
    return recursive_dls(initial_node, limit, set())


def iterative_deepening_search(problem: MetroProblem, start: str = 'A', goal: str = 'J') -> Tuple[Optional[Node], Dict[str, any]]:
    start_time = time.time()
    tracemalloc.start()
    
    total_nodes_explored = 0
    
    for depth in range(100):
        result, cutoff, nodes_explored = depth_limited_search(problem, start, goal, depth)
        total_nodes_explored += nodes_explored
        
        if result is not None:
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return result, {
                'time': end_time - start_time,
                'memory_current': current,
                'memory_peak': peak,
                'nodes_explored': total_nodes_explored,
                'max_depth': depth
            }
        
        if not cutoff:
            break
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return None, {
        'time': end_time - start_time,
        'memory_current': current,
        'memory_peak': peak,
        'nodes_explored': total_nodes_explored
    }


def print_results(algorithm_name: str, result: Optional[Node], stats: Dict[str, any]):
    print(f"\n{algorithm_name} Results:")
    print("-" * 50)
    
    if result:
        path = result.get_path()
        print(f"Path found: {' -> '.join(path)}")
        print(f"Path length: {len(path) - 1} stations")
    else:
        print("No path found!")
    
    print(f"Time elapsed: {stats['time']:.6f} seconds")
    print(f"Memory used (current): {stats['memory_current'] / 1024:.2f} KB")
    print(f"Memory used (peak): {stats['memory_peak'] / 1024:.2f} KB")
    print(f"Nodes explored: {stats['nodes_explored']}")
    
    if 'max_depth' in stats:
        print(f"Maximum depth reached: {stats['max_depth']}")


def main():
    problem = MetroProblem()
    
    print("Metro Network Navigation - Finding path from A to J")
    print("=" * 50)
    
    bfs_result, bfs_stats = breadth_first_search(problem, 'A', 'J')
    print_results("Breadth-First Search (BFS)", bfs_result, bfs_stats)
    
    ids_result, ids_stats = iterative_deepening_search(problem, 'A', 'J')
    print_results("Iterative Deepening Search (IDS)", ids_result, ids_stats)
    
    print("\n\nComparison Analysis:")
    print("=" * 50)
    print(f"Time difference: {abs(bfs_stats['time'] - ids_stats['time']):.6f} seconds")
    print(f"Memory difference (peak): {abs(bfs_stats['memory_peak'] - ids_stats['memory_peak']) / 1024:.2f} KB")
    print(f"Nodes explored difference: {abs(bfs_stats['nodes_explored'] - ids_stats['nodes_explored'])}")
    
    print("\nAlgorithm Characteristics:")
    print("-" * 50)
    print("BFS:")
    print("- Guarantees shortest path in unweighted graphs")
    print("- Explores level by level")
    print("- Higher memory usage (stores entire frontier)")
    print("- Generally faster for shallow solutions")
    
    print("\nIDS:")
    print("- Combines benefits of DFS memory efficiency with BFS completeness")
    print("- Revisits nodes multiple times")
    print("- Lower memory footprint")
    print("- Can be slower due to repeated exploration")


if __name__ == "__main__":
    main()