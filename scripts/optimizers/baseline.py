"""
Baseline optimizer: A* shortest path + equidistant stops.
"""

from typing import Dict, List, Tuple
from scripts.city_map import CityMap
from scripts.astar import astar, path_cost


def optimize(city_map: CityMap, alpha: float = 1.0, beta: float = 1.0,
             gamma: float = 1.0) -> Dict:
    """
    Baseline: find A* shortest path, place stops at equal intervals.
    Returns solution dict with route, stops, and cost breakdown.
    """
    route = astar(city_map, city_map.start, city_map.end)
    if route is None:
        return {"error": "No path found"}

    # Place stops at equal intervals along the route
    n_stops = min(city_map.max_stops, len(route) - 1)
    if n_stops <= 0:
        stops = []
    else:
        interval = len(route) / (n_stops + 1)
        stops = []
        for i in range(1, n_stops + 1):
            idx = int(i * interval)
            idx = min(idx, len(route) - 1)
            stops.append(route[idx])

    return _build_result(city_map, route, stops, alpha, beta, gamma)


def _build_result(city_map: CityMap, route: List[Tuple[int, int]],
                  stops: List[Tuple[int, int]],
                  alpha: float, beta: float, gamma: float) -> Dict:
    """Build standardized result dict."""
    raw_route_cost = path_cost(city_map, route)

    # Walk cost: sum of Manhattan distances from each passenger to nearest stop
    raw_walk_cost = 0.0
    passenger_assignments = []
    for px, py in city_map.passengers:
        if not stops:
            min_dist = float('inf')
            nearest = None
        else:
            min_dist = float('inf')
            nearest = stops[0]
            for sx, sy in stops:
                d = abs(px - sx) + abs(py - sy)
                if d < min_dist:
                    min_dist = d
                    nearest = (sx, sy)
        raw_walk_cost += min_dist
        passenger_assignments.append({"passenger": (px, py), "stop": nearest, "distance": min_dist})

    # Stop cost: sum of (fixed_cost + terrain_bonus) for each stop
    raw_stop_cost = 0.0
    for sx, sy in stops:
        raw_stop_cost += city_map.stop_cost(sx, sy)

    total = alpha * raw_route_cost + beta * raw_walk_cost + gamma * raw_stop_cost

    return {
        "method": "baseline",
        "route": route,
        "stops": stops,
        "route_cost": alpha * raw_route_cost,
        "walk_cost": beta * raw_walk_cost,
        "stop_cost": gamma * raw_stop_cost,
        "total_cost": total,
        "raw_route_cost": raw_route_cost,
        "raw_walk_cost": raw_walk_cost,
        "raw_stop_cost": raw_stop_cost,
        "n_stops": len(stops),
    }
