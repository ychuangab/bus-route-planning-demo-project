"""
Evaluation engine: cost breakdown, coverage rate, multi-run statistics, ablation.
"""

import json
import numpy as np
from typing import Dict, List, Tuple


def cost_breakdown(city_map, route, stops, alpha=1.0, beta=1.0, gamma=1.0) -> Dict:
    """Calculate detailed cost breakdown for a solution."""
    from scripts.astar import path_cost

    raw_route_cost = path_cost(city_map, route)

    raw_walk_cost = 0.0
    walk_distances = []
    for px, py in city_map.passengers:
        if stops:
            min_dist = min(abs(px - sx) + abs(py - sy) for sx, sy in stops)
        else:
            min_dist = float('inf')
        raw_walk_cost += min_dist
        walk_distances.append(min_dist)

    raw_stop_cost = sum(city_map.stop_cost(sx, sy) for sx, sy in stops)

    return {
        "route_cost": alpha * raw_route_cost,
        "walk_cost": beta * raw_walk_cost,
        "stop_cost": gamma * raw_stop_cost,
        "total_cost": alpha * raw_route_cost + beta * raw_walk_cost + gamma * raw_stop_cost,
        "raw_route_cost": raw_route_cost,
        "raw_walk_cost": raw_walk_cost,
        "raw_stop_cost": raw_stop_cost,
        "walk_distances": walk_distances,
    }


def coverage_rate(city_map, stops, threshold=10) -> float:
    """
    Calculate passenger coverage rate: fraction of passengers
    within `threshold` Manhattan distance of any stop.
    """
    if not city_map.passengers or not stops:
        return 0.0

    covered = 0
    for px, py in city_map.passengers:
        min_dist = min(abs(px - sx) + abs(py - sy) for sx, sy in stops)
        if min_dist <= threshold:
            covered += 1

    return covered / len(city_map.passengers)


def multi_run_stats(results: List[Dict]) -> Dict:
    """Compute mean, std, min, max of total_cost across runs."""
    costs = [r["total_cost"] for r in results if "total_cost" in r and r["total_cost"] < float('inf')]
    if not costs:
        return {"mean": None, "std": None, "min": None, "max": None, "n_valid": 0}

    return {
        "mean": float(np.mean(costs)),
        "std": float(np.std(costs)),
        "min": float(np.min(costs)),
        "max": float(np.max(costs)),
        "n_valid": len(costs),
    }


ABLATION_WEIGHTS = [
    {"name": "均衡", "alpha": 1.0, "beta": 1.0, "gamma": 1.0},
    {"name": "乘客優先", "alpha": 0.3, "beta": 1.0, "gamma": 0.3},
    {"name": "營運優先", "alpha": 1.0, "beta": 0.3, "gamma": 0.3},
    {"name": "站牌節省", "alpha": 0.3, "beta": 0.3, "gamma": 1.0},
    {"name": "極端乘客", "alpha": 0.1, "beta": 1.0, "gamma": 0.1},
]


def ablation_experiment(city_map, optimizer_fn, weights=None) -> List[Dict]:
    """
    Run ablation experiment with multiple weight combinations.
    optimizer_fn(city_map, alpha, beta, gamma) -> result dict
    """
    if weights is None:
        weights = ABLATION_WEIGHTS

    results = []
    for w in weights:
        result = optimizer_fn(city_map, alpha=w["alpha"], beta=w["beta"], gamma=w["gamma"])
        result["weight_name"] = w["name"]
        result["weights"] = {"alpha": w["alpha"], "beta": w["beta"], "gamma": w["gamma"]}
        results.append(result)

    return results


def export_results(all_results: Dict, output_path: str):
    """Export all results to JSON file."""
    # Convert route/stops tuples to lists for JSON serialization
    def sanitize(obj):
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(v) for v in obj]
        elif isinstance(obj, tuple):
            return list(obj)
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif obj == float('inf'):
            return None
        return obj

    clean = sanitize(all_results)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
