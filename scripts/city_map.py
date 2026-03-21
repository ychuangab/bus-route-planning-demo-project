"""
City map model: NxN grid with terrain costs, forbidden zones, passengers, endpoints.
"""

import json
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class CityMap:
    """2D city grid model for bus route planning."""
    grid_size: int
    terrain: np.ndarray          # (N, N) int array, terrain cost per cell
    forbidden: np.ndarray        # (N, N) bool array
    passengers: List[Tuple[int, int]]
    start: Tuple[int, int]       # endpoint A
    end: Tuple[int, int]         # endpoint B
    seed: int = 0
    name: str = ""
    description: str = ""
    max_stops: int = 10
    fixed_stop_cost: float = 5.0

    def is_passable(self, x: int, y: int) -> bool:
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            return not self.forbidden[y, x]
        return False

    def terrain_cost(self, x: int, y: int) -> float:
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            return float(self.terrain[y, x])
        return float('inf')

    def stop_cost(self, x: int, y: int) -> float:
        """Cost of placing a stop at (x, y): fixed cost + terrain bonus."""
        return self.fixed_stop_cost + self.terrain_cost(x, y)

    def to_dict(self) -> dict:
        """Export map data as a JSON-serializable dict."""
        return {
            "name": self.name,
            "description": self.description,
            "grid_size": self.grid_size,
            "terrain": self.terrain.tolist(),
            "forbidden": self.forbidden.astype(int).tolist(),
            "passengers": self.passengers,
            "start": list(self.start),
            "end": list(self.end),
            "seed": self.seed,
            "max_stops": self.max_stops,
            "fixed_stop_cost": self.fixed_stop_cost,
        }

    def to_json(self, path: str):
        """Export map to JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


def generate_map(config: dict) -> CityMap:
    """
    Generate a CityMap from a configuration dict.

    Config keys:
        grid_size: int
        seed: int
        n_passengers: int
        start: (x, y)
        end: (x, y)
        forbidden_zones: list of {"type": "rect", "x1", "y1", "x2", "y2"}
        terrain_zones: list of {"type": "rect", "x1", "y1", "x2", "y2", "cost": int}
        passenger_clusters: list of {"cx", "cy", "radius", "count"} (optional)
        name: str
        description: str
        max_stops: int
        fixed_stop_cost: float
    """
    rng = np.random.RandomState(config["seed"])
    N = config["grid_size"]

    # Initialize terrain (default cost = 1)
    terrain = np.ones((N, N), dtype=int)
    for tz in config.get("terrain_zones", []):
        x1, y1, x2, y2 = tz["x1"], tz["y1"], tz["x2"], tz["y2"]
        terrain[y1:y2+1, x1:x2+1] = tz["cost"]

    # Forbidden zones
    forbidden = np.zeros((N, N), dtype=bool)
    for fz in config.get("forbidden_zones", []):
        x1, y1, x2, y2 = fz["x1"], fz["y1"], fz["x2"], fz["y2"]
        forbidden[y1:y2+1, x1:x2+1] = True

    # Generate passengers
    passengers = []
    clusters = config.get("passenger_clusters", [])
    if clusters:
        for cluster in clusters:
            cx, cy, radius, count = cluster["cx"], cluster["cy"], cluster["radius"], cluster["count"]
            placed = 0
            attempts = 0
            while placed < count and attempts < count * 20:
                x = int(np.clip(rng.normal(cx, radius / 2), 0, N - 1))
                y = int(np.clip(rng.normal(cy, radius / 2), 0, N - 1))
                if not forbidden[y, x] and (x, y) not in passengers:
                    passengers.append((x, y))
                    placed += 1
                attempts += 1
    else:
        # Uniform random placement
        n_passengers = config["n_passengers"]
        placed = 0
        attempts = 0
        while placed < n_passengers and attempts < n_passengers * 20:
            x = rng.randint(0, N)
            y = rng.randint(0, N)
            if not forbidden[y, x] and (x, y) not in passengers:
                passengers.append((x, y))
                placed += 1
            attempts += 1

    start = tuple(config["start"])
    end = tuple(config["end"])

    return CityMap(
        grid_size=N,
        terrain=terrain,
        forbidden=forbidden,
        passengers=passengers,
        start=start,
        end=end,
        seed=config["seed"],
        name=config.get("name", ""),
        description=config.get("description", ""),
        max_stops=config.get("max_stops", 10),
        fixed_stop_cost=config.get("fixed_stop_cost", 5.0),
    )


# ── Test Map Definitions ──

MAP_CONFIGS = {
    1: {
        "name": "Map 1",
        "description": "小規模 (20人), 無禁區, 均勻地形 — 基礎驗證",
        "grid_size": 30,
        "seed": 42,
        "n_passengers": 20,
        "start": (0, 15),
        "end": (29, 15),
        "forbidden_zones": [],
        "terrain_zones": [],
        "max_stops": 5,
        "fixed_stop_cost": 5.0,
    },
    2: {
        "name": "Map 2",
        "description": "中規模 (100人), 兩群聚乘客 — 測試繞路效益",
        "grid_size": 50,
        "seed": 123,
        "n_passengers": 100,
        "start": (0, 25),
        "end": (49, 25),
        "forbidden_zones": [],
        "terrain_zones": [
            {"x1": 20, "y1": 0, "x2": 30, "y2": 10, "cost": 3},
        ],
        "passenger_clusters": [
            {"cx": 15, "cy": 10, "radius": 8, "count": 50},
            {"cx": 35, "cy": 40, "radius": 8, "count": 50},
        ],
        "max_stops": 8,
        "fixed_stop_cost": 5.0,
    },
    3: {
        "name": "Map 3",
        "description": "中規模 (100人), 大禁區擋中間 — 測試路徑規劃能力",
        "grid_size": 50,
        "seed": 456,
        "n_passengers": 100,
        "start": (0, 25),
        "end": (49, 25),
        "forbidden_zones": [
            {"x1": 20, "y1": 15, "x2": 30, "y2": 35},
        ],
        "terrain_zones": [],
        "max_stops": 8,
        "fixed_stop_cost": 5.0,
    },
    4: {
        "name": "Map 4",
        "description": "大規模 (500人), 分散, 局部高地形成本 — 測試擴展性",
        "grid_size": 80,
        "seed": 789,
        "n_passengers": 500,
        "start": (0, 40),
        "end": (79, 40),
        "forbidden_zones": [
            {"x1": 30, "y1": 30, "x2": 35, "y2": 50},
        ],
        "terrain_zones": [
            {"x1": 50, "y1": 20, "x2": 70, "y2": 60, "cost": 5},
        ],
        "max_stops": 15,
        "fixed_stop_cost": 5.0,
    },
    5: {
        "name": "Map 5",
        "description": "中規模 (100人), 乘客沿對角線分布 — 測試路線偏移策略",
        "grid_size": 50,
        "seed": 321,
        "n_passengers": 100,
        "start": (0, 0),
        "end": (49, 49),
        "forbidden_zones": [],
        "terrain_zones": [
            {"x1": 0, "y1": 40, "x2": 10, "y2": 49, "cost": 3},
        ],
        "passenger_clusters": [
            {"cx": 25, "cy": 25, "radius": 15, "count": 100},
        ],
        "max_stops": 8,
        "fixed_stop_cost": 5.0,
    },
}


def generate_all_maps() -> dict:
    """Generate all 5 test maps."""
    maps = {}
    for map_id, config in MAP_CONFIGS.items():
        maps[map_id] = generate_map(config)
    return maps


def export_all_maps(output_dir: str):
    """Export all maps to JSON files."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    maps = generate_all_maps()
    all_maps_data = {}
    for map_id, city_map in maps.items():
        city_map.to_json(os.path.join(output_dir, f"map{map_id}.json"))
        all_maps_data[f"map{map_id}"] = city_map.to_dict()
    return all_maps_data


if __name__ == "__main__":
    maps = generate_all_maps()
    for map_id, m in maps.items():
        print(f"Map {map_id}: {m.name} — {m.grid_size}x{m.grid_size}, "
              f"{len(m.passengers)} passengers, "
              f"forbidden cells: {m.forbidden.sum()}")
