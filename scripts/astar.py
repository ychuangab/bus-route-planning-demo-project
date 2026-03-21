"""
A* pathfinding on a 2D grid with forbidden zones and terrain costs.
"""

import heapq
from typing import List, Tuple, Optional

from scripts.city_map import CityMap


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(city_map: CityMap, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """
    A* search on grid. Returns list of (x, y) coordinates from start to goal,
    or None if no path exists.
    """
    N = city_map.grid_size
    sx, sy = start
    gx, gy = goal

    if not city_map.is_passable(sx, sy) or not city_map.is_passable(gx, gy):
        return None

    # Priority queue: (f_score, counter, x, y)
    counter = 0
    open_set = [(manhattan_distance(start, goal), counter, sx, sy)]
    came_from = {}
    g_score = {(sx, sy): 0.0}

    DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    while open_set:
        f, _, cx, cy = heapq.heappop(open_set)

        if (cx, cy) == (gx, gy):
            # Reconstruct path
            path = [(gx, gy)]
            node = (gx, gy)
            while node in came_from:
                node = came_from[node]
                path.append(node)
            path.reverse()
            return path

        current_g = g_score.get((cx, cy), float('inf'))
        if f - manhattan_distance((cx, cy), goal) > current_g:
            continue  # stale entry

        for dx, dy in DIRS:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < N and 0 <= ny < N and city_map.is_passable(nx, ny):
                new_g = current_g + city_map.terrain_cost(nx, ny)
                if new_g < g_score.get((nx, ny), float('inf')):
                    g_score[(nx, ny)] = new_g
                    h = manhattan_distance((nx, ny), goal)
                    counter += 1
                    heapq.heappush(open_set, (new_g + h, counter, nx, ny))
                    came_from[(nx, ny)] = (cx, cy)

    return None  # No path found


def path_cost(city_map: CityMap, path: List[Tuple[int, int]]) -> float:
    """Calculate total terrain cost along a path."""
    if not path:
        return 0.0
    # Cost = sum of terrain costs for all cells in path (excluding start)
    return sum(city_map.terrain_cost(x, y) for x, y in path[1:])


def waypoint_route(city_map: CityMap, waypoints: List[Tuple[int, int]]) -> Optional[List[Tuple[int, int]]]:
    """
    Route through waypoints: A → W1 → W2 → ... → B.
    waypoints should include start and end: [start, w1, w2, ..., end].
    Returns the full connected path, or None if any segment fails.
    """
    if len(waypoints) < 2:
        return None

    full_path = []
    for i in range(len(waypoints) - 1):
        segment = astar(city_map, waypoints[i], waypoints[i + 1])
        if segment is None:
            return None
        if i > 0:
            segment = segment[1:]  # avoid duplicating junction points
        full_path.extend(segment)

    return full_path


if __name__ == "__main__":
    from scripts.city_map import generate_all_maps

    maps = generate_all_maps()

    # Test on each map
    for map_id, m in maps.items():
        p = astar(m, m.start, m.end)
        if p:
            cost = path_cost(m, p)
            print(f"Map {map_id}: path length={len(p)}, cost={cost:.1f}")
        else:
            print(f"Map {map_id}: NO PATH FOUND")
