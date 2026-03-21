"""
GA (Genetic Algorithm) optimizer for bus route planning.
Chromosome: waypoint sequence + stop indices on the resulting route.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from scripts.city_map import CityMap
from scripts.astar import astar, path_cost, waypoint_route


def optimize(city_map: CityMap, alpha: float = 1.0, beta: float = 1.0,
             gamma: float = 1.0, population_size: int = 50,
             generations: int = 200, seed: Optional[int] = None) -> Dict:
    """GA optimizer with waypoints + stop placement."""
    rng = np.random.RandomState(seed)
    N = city_map.grid_size

    # Initialize population
    population = [_random_chromosome(city_map, rng) for _ in range(population_size)]
    best_solution = None
    best_fitness = float('inf')
    convergence = []

    for gen in range(generations):
        # Evaluate fitness
        fitnesses = []
        for chrom in population:
            sol = _decode(city_map, chrom, alpha, beta, gamma)
            cost = sol["total_cost"] if sol and "total_cost" in sol else float('inf')
            fitnesses.append(cost)
            if cost < best_fitness:
                best_fitness = cost
                best_solution = sol

        convergence.append(best_fitness)

        # Selection (tournament)
        new_pop = []
        for _ in range(population_size):
            i, j = rng.randint(0, population_size, 2)
            winner = population[i] if fitnesses[i] < fitnesses[j] else population[j]
            new_pop.append(winner.copy())

        # Crossover
        for i in range(0, population_size - 1, 2):
            if rng.random() < 0.7:
                new_pop[i], new_pop[i+1] = _crossover(new_pop[i], new_pop[i+1], rng)

        # Mutation
        for i in range(population_size):
            if rng.random() < 0.3:
                new_pop[i] = _mutate(new_pop[i], city_map, rng)

        population = new_pop

    if best_solution:
        best_solution["convergence"] = convergence
    return best_solution or {"error": "GA failed to find solution"}


def _random_chromosome(city_map: CityMap, rng: np.random.RandomState) -> dict:
    """Generate a random chromosome: 0-3 waypoints + stop count."""
    N = city_map.grid_size
    n_waypoints = rng.randint(0, 4)
    waypoints = []
    for _ in range(n_waypoints):
        x, y = rng.randint(0, N), rng.randint(0, N)
        attempts = 0
        while not city_map.is_passable(x, y) and attempts < 50:
            x, y = rng.randint(0, N), rng.randint(0, N)
            attempts += 1
        if city_map.is_passable(x, y):
            waypoints.append((x, y))

    n_stops = rng.randint(1, city_map.max_stops + 1)
    # Stop positions as fractions along the route (0.0 to 1.0)
    stop_fracs = sorted(rng.random(n_stops).tolist())

    return {"waypoints": waypoints, "stop_fracs": stop_fracs}


def _decode(city_map: CityMap, chrom: dict, alpha: float, beta: float,
            gamma: float) -> Optional[Dict]:
    """Decode chromosome into a solution."""
    wp_list = [city_map.start] + chrom["waypoints"] + [city_map.end]
    route = waypoint_route(city_map, wp_list)
    if route is None or len(route) < 2:
        return {"total_cost": float('inf'), "error": "invalid route"}

    # Place stops at fractional positions along route
    stops = []
    for frac in chrom["stop_fracs"]:
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
        "method": "ga",
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


def _crossover(a: dict, b: dict, rng: np.random.RandomState) -> Tuple[dict, dict]:
    """Single-point crossover on waypoints and stop fractions."""
    # Swap waypoints
    wp_a, wp_b = a["waypoints"][:], b["waypoints"][:]
    if wp_a and wp_b:
        cut = rng.randint(0, max(len(wp_a), len(wp_b)))
        new_wp_a = wp_a[:cut] + wp_b[cut:]
        new_wp_b = wp_b[:cut] + wp_a[cut:]
    else:
        new_wp_a, new_wp_b = wp_a, wp_b

    # Swap stop fracs
    sf_a, sf_b = a["stop_fracs"][:], b["stop_fracs"][:]
    if sf_a and sf_b:
        cut = rng.randint(0, max(len(sf_a), len(sf_b)))
        new_sf_a = sorted(sf_a[:cut] + sf_b[cut:])
        new_sf_b = sorted(sf_b[:cut] + sf_a[cut:])
    else:
        new_sf_a, new_sf_b = sf_a, sf_b

    return ({"waypoints": new_wp_a, "stop_fracs": new_sf_a},
            {"waypoints": new_wp_b, "stop_fracs": new_sf_b})


def _mutate(chrom: dict, city_map: CityMap, rng: np.random.RandomState) -> dict:
    """Mutate: randomly modify waypoint or stop fraction."""
    chrom = {"waypoints": chrom["waypoints"][:], "stop_fracs": chrom["stop_fracs"][:]}
    N = city_map.grid_size

    action = rng.randint(0, 4)
    if action == 0 and chrom["waypoints"]:
        # Move a waypoint
        idx = rng.randint(0, len(chrom["waypoints"]))
        x, y = rng.randint(0, N), rng.randint(0, N)
        if city_map.is_passable(x, y):
            chrom["waypoints"][idx] = (x, y)
    elif action == 1:
        # Add a waypoint
        if len(chrom["waypoints"]) < 5:
            x, y = rng.randint(0, N), rng.randint(0, N)
            if city_map.is_passable(x, y):
                chrom["waypoints"].append((x, y))
    elif action == 2 and chrom["waypoints"]:
        # Remove a waypoint
        idx = rng.randint(0, len(chrom["waypoints"]))
        chrom["waypoints"].pop(idx)
    elif action == 3 and chrom["stop_fracs"]:
        # Perturb a stop fraction
        idx = rng.randint(0, len(chrom["stop_fracs"]))
        chrom["stop_fracs"][idx] = np.clip(
            chrom["stop_fracs"][idx] + rng.normal(0, 0.1), 0.01, 0.99
        )
        chrom["stop_fracs"].sort()

    return chrom


def optimize_multi(city_map: CityMap, n_runs: int = 10, **kwargs) -> List[Dict]:
    """Run GA multiple times and return all results."""
    results = []
    for i in range(n_runs):
        seed = kwargs.get("seed", 0) + i if kwargs.get("seed") is not None else i
        result = optimize(city_map, seed=seed, **{k: v for k, v in kwargs.items() if k != "seed"})
        results.append(result)
    return results
