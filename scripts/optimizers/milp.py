"""
MILP (Mixed Integer Linear Programming) optimizer using PuLP.
Exact solution for small-scale problems; may timeout on large ones.
"""

import time
from typing import Dict, List, Tuple, Optional

try:
    import pulp
    HAS_PULP = True
except ImportError:
    HAS_PULP = False

from scripts.city_map import CityMap
from scripts.astar import astar, path_cost


def optimize(city_map: CityMap, alpha: float = 1.0, beta: float = 1.0,
             gamma: float = 1.0, timeout: int = 60,
             candidate_interval: int = 3) -> Dict:
    """
    MILP optimizer.

    Since full route optimization via MILP on a grid is intractable,
    we fix the route (A* shortest path) and optimize stop placement.

    Decision variables: binary y_j for each candidate stop position.
    Objective: minimize α·route_cost + β·Σ_i(min_j walk_ij · y_j) + γ·Σ_j(stop_cost_j · y_j)

    The walk cost is linearized using auxiliary variables.
    """
    if not HAS_PULP:
        return {"error": "PuLP not installed", "method": "milp"}

    route = astar(city_map, city_map.start, city_map.end)
    if route is None:
        return {"error": "No path found", "method": "milp"}

    raw_route_cost = path_cost(city_map, route)

    # Generate candidate stop positions along the route
    candidates = []
    for i in range(0, len(route), candidate_interval):
        if route[i] not in candidates:
            candidates.append(route[i])
    if route[-1] not in candidates:
        candidates.append(route[-1])

    n_candidates = len(candidates)
    n_passengers = len(city_map.passengers)

    # Precompute distances
    dist = {}  # dist[i][j] = Manhattan distance from passenger i to candidate j
    for i, (px, py) in enumerate(city_map.passengers):
        for j, (cx, cy) in enumerate(candidates):
            dist[(i, j)] = abs(px - cx) + abs(py - cy)

    # Build MILP model
    model = pulp.LpProblem("BusStopPlacement", pulp.LpMinimize)

    # Decision variables
    y = {j: pulp.LpVariable(f"y_{j}", cat="Binary") for j in range(n_candidates)}

    # Assignment variables: x[i][j] = 1 if passenger i assigned to stop j
    x = {}
    for i in range(n_passengers):
        for j in range(n_candidates):
            x[(i, j)] = pulp.LpVariable(f"x_{i}_{j}", cat="Binary")

    # Walk cost variable for each passenger
    w = {i: pulp.LpVariable(f"w_{i}", lowBound=0) for i in range(n_passengers)}

    # Objective
    walk_term = pulp.lpSum(w[i] for i in range(n_passengers))
    stop_term = pulp.lpSum(
        city_map.stop_cost(candidates[j][0], candidates[j][1]) * y[j]
        for j in range(n_candidates)
    )
    model += alpha * raw_route_cost + beta * walk_term + gamma * stop_term

    # Constraints
    # Each passenger assigned to exactly one stop
    for i in range(n_passengers):
        model += pulp.lpSum(x[(i, j)] for j in range(n_candidates)) == 1

    # Can only assign to open stops
    for i in range(n_passengers):
        for j in range(n_candidates):
            model += x[(i, j)] <= y[j]

    # Walk distance linking
    for i in range(n_passengers):
        for j in range(n_candidates):
            model += w[i] >= dist[(i, j)] * x[(i, j)]

    # Max stops constraint
    model += pulp.lpSum(y[j] for j in range(n_candidates)) <= city_map.max_stops

    # At least 1 stop
    model += pulp.lpSum(y[j] for j in range(n_candidates)) >= 1

    # Solve
    start_time = time.time()
    solver = pulp.PULP_CBC_CMD(timeLimit=timeout, msg=0)
    status = model.solve(solver)
    solve_time = time.time() - start_time

    if status != pulp.constants.LpStatusOptimal and status != 1:
        return {
            "error": f"MILP status: {pulp.LpStatus[status]}",
            "method": "milp",
            "solve_time": solve_time,
        }

    # Extract solution
    stops = [candidates[j] for j in range(n_candidates) if y[j].value() > 0.5]

    raw_walk_cost = 0.0
    for i in range(n_passengers):
        raw_walk_cost += w[i].value() if w[i].value() is not None else 0.0

    raw_stop_cost = sum(city_map.stop_cost(sx, sy) for sx, sy in stops)
    total = alpha * raw_route_cost + beta * raw_walk_cost + gamma * raw_stop_cost

    # Optimality gap
    obj_val = model.objective.value()
    best_bound = model.solver.bestBound if hasattr(model.solver, 'bestBound') else None
    gap = None
    if best_bound is not None and obj_val is not None and obj_val > 0:
        gap = abs(obj_val - best_bound) / abs(obj_val)

    return {
        "method": "milp",
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
        "solve_time": solve_time,
        "optimality_gap": gap,
        "status": pulp.LpStatus[status],
    }
