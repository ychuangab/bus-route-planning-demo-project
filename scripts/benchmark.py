"""
Benchmark runner: run all methods × all maps, produce results.json.
"""

import os
import sys
import time
import json

from scripts.city_map import generate_map, MAP_CONFIGS, export_all_maps
from scripts.evaluation import (
    coverage_rate, multi_run_stats, ablation_experiment, export_results
)
from scripts.optimizers import baseline, greedy, ga, sa, milp


def run_benchmark(output_dir: str = "frontend/public/data",
                  ga_generations: int = 200, sa_max_iter: int = 5000,
                  n_runs: int = 10, milp_timeout: int = 60):
    """Run full benchmark: all methods × all maps."""

    os.makedirs(output_dir, exist_ok=True)

    # Generate and export maps
    print("Generating maps...")
    maps_data = export_all_maps(output_dir)
    maps = {}
    for map_id in MAP_CONFIGS:
        maps[map_id] = generate_map(MAP_CONFIGS[map_id])

    all_results = {"maps": maps_data, "results": {}, "statistics": {}, "ablation": {}}

    for map_id, city_map in maps.items():
        map_key = f"map{map_id}"
        print(f"\n{'='*50}")
        print(f"Map {map_id}: {city_map.name} ({city_map.grid_size}x{city_map.grid_size}, {len(city_map.passengers)} passengers)")
        print(f"{'='*50}")

        all_results["results"][map_key] = {}
        all_results["statistics"][map_key] = {}

        # Scale down iterations for large maps
        n_pass = len(city_map.passengers)
        map_ga_gen = ga_generations if n_pass <= 200 else ga_generations // 2
        map_sa_iter = sa_max_iter if n_pass <= 200 else sa_max_iter // 2
        map_n_runs = n_runs if n_pass <= 200 else max(3, n_runs // 2)

        methods = {
            "baseline": lambda m, **kw: baseline.optimize(m, **kw),
            "greedy": lambda m, **kw: greedy.optimize(m, **kw),
            "ga": lambda m, **kw: ga.optimize(m, seed=42, generations=map_ga_gen, **kw),
            "sa": lambda m, **kw: sa.optimize(m, seed=42, max_iter=map_sa_iter, **kw),
            "milp": lambda m, **kw: milp.optimize(m, timeout=milp_timeout, **kw),
        }

        for method_name, method_fn in methods.items():
            print(f"  Running {method_name}...", end=" ", flush=True)
            start_time = time.time()

            try:
                # Skip MILP on large maps
                if method_name == "milp" and len(city_map.passengers) > 200:
                    result = {"method": "milp", "error": "Skipped (too large)",
                              "total_cost": None, "n_stops": 0}
                    print("SKIPPED (too large)")
                else:
                    result = method_fn(city_map)
                    elapsed = time.time() - start_time
                    result["execution_time"] = elapsed

                    # Add coverage
                    if "stops" in result:
                        result["coverage"] = coverage_rate(city_map, result["stops"])

                    if "error" in result:
                        print(f"ERROR: {result['error']}")
                    else:
                        print(f"cost={result['total_cost']:.1f}, "
                              f"stops={result.get('n_stops', 0)}, "
                              f"coverage={result.get('coverage', 0)*100:.1f}%, "
                              f"time={elapsed:.2f}s")

            except Exception as e:
                result = {"method": method_name, "error": str(e)}
                print(f"EXCEPTION: {e}")

            # Remove large route data for JSON (keep only for display)
            display_result = result.copy()
            all_results["results"][map_key][method_name] = display_result

            # Multi-run statistics for GA and SA
            if method_name in ("ga", "sa") and "error" not in result:
                print(f"    Running {map_n_runs}x for statistics...", end=" ", flush=True)
                if method_name == "ga":
                    multi_results = ga.optimize_multi(
                        city_map, n_runs=map_n_runs, alpha=1.0, beta=1.0, gamma=1.0,
                        generations=map_ga_gen, seed=42
                    )
                else:
                    multi_results = sa.optimize_multi(
                        city_map, n_runs=map_n_runs, alpha=1.0, beta=1.0, gamma=1.0,
                        max_iter=map_sa_iter, seed=42
                    )
                stats = multi_run_stats(multi_results)
                all_results["statistics"][map_key][method_name] = stats
                print(f"mean={stats['mean']:.1f}±{stats['std']:.1f}")

    # Ablation experiment (Map 2 + GA)
    print(f"\n{'='*50}")
    print("Ablation experiment (Map 2 × GA)")
    print(f"{'='*50}")

    city_map_2 = maps[2]
    ablation_results = ablation_experiment(
        city_map_2,
        lambda m, **kw: ga.optimize(m, seed=42, generations=ga_generations, **kw)
    )
    for r in ablation_results:
        r["coverage"] = coverage_rate(city_map_2, r.get("stops", []))
        print(f"  {r['weight_name']}: total={r['total_cost']:.1f}, "
              f"route={r.get('raw_route_cost',0):.1f}, "
              f"walk={r.get('raw_walk_cost',0):.1f}, "
              f"stop={r.get('raw_stop_cost',0):.1f}")

    all_results["ablation"] = {"map2_ga": ablation_results}

    # Export results
    output_path = os.path.join(output_dir, "results.json")
    export_results(all_results, output_path)
    print(f"\nResults exported to {output_path}")

    return all_results


if __name__ == "__main__":
    # Use smaller params for faster testing if --quick flag
    quick = "--quick" in sys.argv
    run_benchmark(
        ga_generations=50 if quick else 200,
        sa_max_iter=1000 if quick else 5000,
        n_runs=3 if quick else 10,
        milp_timeout=30 if quick else 60,
    )
