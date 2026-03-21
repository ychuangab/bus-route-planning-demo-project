"""
Greedy optimizer: A* shortest path + greedy stop placement (max walk cost reduction).
"""

from typing import Dict, List, Tuple
from scripts.city_map import CityMap
from scripts.astar import astar, path_cost


def optimize(city_map: CityMap, alpha: float = 1.0, beta: float = 1.0,
             gamma: float = 1.0) -> Dict:
    """
    Greedy: A* shortest path, then iteratively place stops at positions
    along the route that maximally reduce total passenger walk cost.
    """
    route = astar(city_map, city_map.start, city_map.end)
    if route is None:
        return {"error": "No path found"}

    n_stops = city_map.max_stops
    stops = []
    route_set = list(set(route))  # candidate positions (on the route)

    for _ in range(n_stops):
        best_pos = None
        best_reduction = -float('inf')

        for candidate in route_set:
            if candidate in stops:
                continue
            # Calculate walk cost reduction if we add this stop
            reduction = 0.0
            for px, py in city_map.passengers:
                # Current min distance to existing stops
                if stops:
                    current_min = min(abs(px - sx) + abs(py - sy) for sx, sy in stops)
                else:
                    current_min = float('inf')
                # Distance to candidate
                new_dist = abs(px - candidate[0]) + abs(py - candidate[1])
                if new_dist < current_min:
                    reduction += (current_min - new_dist)

            # Factor in stop cost penalty
            net_benefit = beta * reduction - gamma * city_map.stop_cost(candidate[0], candidate[1])

            if net_benefit > best_reduction:
                best_reduction = net_benefit
                best_pos = candidate

        if best_pos is None or best_reduction <= 0:
            break
        stops.append(best_pos)

    return _build_result(city_map, route, stops, alpha, beta, gamma)


def _build_result(city_map: CityMap, route: List[Tuple[int, int]],
                  stops: List[Tuple[int, int]],
                  alpha: float, beta: float, gamma: float) -> Dict:
    raw_route_cost = path_cost(city_map, route)

    raw_walk_cost = 0.0
    for px, py in city_map.passengers:
        if stops:
            min_dist = min(abs(px - sx) + abs(py - sy) for sx, sy in stops)
        else:
            min_dist = float('inf')
        raw_walk_cost += min_dist

    raw_stop_cost = sum(city_map.stop_cost(sx, sy) for sx, sy in stops)

    total = alpha * raw_route_cost + beta * raw_walk_cost + gamma * raw_stop_cost

    return {
        "method": "greedy",
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
