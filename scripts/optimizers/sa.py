"""
SA (Simulated Annealing) optimizer for bus route planning.
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from scripts.city_map import CityMap
from scripts.astar import astar, path_cost, waypoint_route


def optimize(city_map: CityMap, alpha: float = 1.0, beta: float = 1.0,
             gamma: float = 1.0, max_iter: int = 5000,
             t_start: float = 100.0, t_end: float = 0.1,
             seed: Optional[int] = None) -> Dict:
    """SA optimizer with Metropolis acceptance criterion."""
    rng = np.random.RandomState(seed)
    N = city_map.grid_size

    # Initial solution from baseline
    current = _initial_solution(city_map, rng)
    current_cost = _evaluate(city_map, current, alpha, beta, gamma)

    best = current.copy()
    best_cost = current_cost
    convergence = []

    cooling_rate = (t_end / t_start) ** (1.0 / max_iter) if max_iter > 0 else 1.0
    temperature = t_start

    for i in range(max_iter):
        # Generate neighbor
        neighbor = _neighbor(current, city_map, rng)
        neighbor_cost = _evaluate(city_map, neighbor, alpha, beta, gamma)

        # Metropolis criterion
        delta = neighbor_cost - current_cost
        if delta < 0 or rng.random() < math.exp(-delta / max(temperature, 1e-10)):
            current = neighbor
            current_cost = neighbor_cost

        if current_cost < best_cost:
            best = current.copy()
            best_cost = current_cost

        temperature *= cooling_rate
        if i % 50 == 0:
            convergence.append(best_cost)

    # Decode best solution
    result = _decode(city_map, best, alpha, beta, gamma)
    if result:
        result["convergence"] = convergence
    return result or {"error": "SA failed"}


def _initial_solution(city_map: CityMap, rng: np.random.RandomState) -> dict:
    """Start from baseline-like solution."""
    route = astar(city_map, city_map.start, city_map.end)
    if route is None:
        return {"waypoints": [], "stop_fracs": [0.5]}

    n_stops = min(city_map.max_stops, max(1, len(route) // 10))
    stop_fracs = [i / (n_stops + 1) for i in range(1, n_stops + 1)]
    return {"waypoints": [], "stop_fracs": stop_fracs}


def _evaluate(city_map: CityMap, sol: dict, alpha: float, beta: float,
              gamma: float) -> float:
    result = _decode(city_map, sol, alpha, beta, gamma)
    if result and "total_cost" in result:
        return result["total_cost"]
    return float('inf')


def _decode(city_map: CityMap, sol: dict, alpha: float, beta: float,
            gamma: float) -> Optional[Dict]:
    wp_list = [city_map.start] + sol.get("waypoints", []) + [city_map.end]
    route = waypoint_route(city_map, wp_list)
    if route is None or len(route) < 2:
        return None

    stops = []
    for frac in sol.get("stop_fracs", []):
        idx = int(frac * (len(route) - 1))
        idx = min(idx, len(route) - 1)
        pos = route[idx]
        if pos not in stops:
            stops.append(pos)

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
        "method": "sa",
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


def _neighbor(sol: dict, city_map: CityMap, rng: np.random.RandomState) -> dict:
    """Generate a neighboring solution."""
    new_sol = {"waypoints": sol.get("waypoints", [])[:],
               "stop_fracs": sol.get("stop_fracs", [])[:]}
    N = city_map.grid_size

    action = rng.randint(0, 5)

    if action == 0 and new_sol["waypoints"]:
        # Move a waypoint
        idx = rng.randint(0, len(new_sol["waypoints"]))
        wx, wy = new_sol["waypoints"][idx]
        dx, dy = rng.randint(-5, 6), rng.randint(-5, 6)
        nx, ny = max(0, min(N-1, wx+dx)), max(0, min(N-1, wy+dy))
        if city_map.is_passable(nx, ny):
            new_sol["waypoints"][idx] = (nx, ny)
    elif action == 1:
        # Add waypoint
        if len(new_sol["waypoints"]) < 5:
            x, y = rng.randint(0, N), rng.randint(0, N)
            if city_map.is_passable(x, y):
                new_sol["waypoints"].append((x, y))
    elif action == 2 and new_sol["waypoints"]:
        # Remove waypoint
        idx = rng.randint(0, len(new_sol["waypoints"]))
        new_sol["waypoints"].pop(idx)
    elif action == 3 and new_sol["stop_fracs"]:
        # Move a stop
        idx = rng.randint(0, len(new_sol["stop_fracs"]))
        new_sol["stop_fracs"][idx] = float(np.clip(
            new_sol["stop_fracs"][idx] + rng.normal(0, 0.1), 0.01, 0.99
        ))
        new_sol["stop_fracs"].sort()
    elif action == 4:
        # Add/remove a stop
        if rng.random() < 0.5 and len(new_sol["stop_fracs"]) < city_map.max_stops:
            new_sol["stop_fracs"].append(float(rng.random()))
            new_sol["stop_fracs"].sort()
        elif len(new_sol["stop_fracs"]) > 1:
            idx = rng.randint(0, len(new_sol["stop_fracs"]))
            new_sol["stop_fracs"].pop(idx)

    return new_sol


def optimize_multi(city_map: CityMap, n_runs: int = 10, **kwargs) -> List[Dict]:
    """Run SA multiple times."""
    results = []
    for i in range(n_runs):
        seed = kwargs.get("seed", 0) + i if kwargs.get("seed") is not None else i
        result = optimize(city_map, seed=seed, **{k: v for k, v in kwargs.items() if k != "seed"})
        results.append(result)
    return results
