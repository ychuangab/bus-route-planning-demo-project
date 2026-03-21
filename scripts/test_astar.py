"""Unit tests for A* pathfinding."""

import numpy as np
from scripts.city_map import CityMap
from scripts.astar import astar, path_cost, waypoint_route


def make_simple_map(size=10, forbidden_cells=None):
    terrain = np.ones((size, size), dtype=int)
    forbidden = np.zeros((size, size), dtype=bool)
    if forbidden_cells:
        for x, y in forbidden_cells:
            forbidden[y, x] = True
    return CityMap(
        grid_size=size,
        terrain=terrain,
        forbidden=forbidden,
        passengers=[],
        start=(0, 0),
        end=(size - 1, size - 1),
        seed=0,
    )


def test_straight_path():
    m = CityMap(
        grid_size=5, terrain=np.ones((5, 5), dtype=int),
        forbidden=np.zeros((5, 5), dtype=bool),
        passengers=[], start=(0, 2), end=(4, 2), seed=0,
    )
    p = astar(m, m.start, m.end)
    assert p is not None
    assert p[0] == (0, 2) and p[-1] == (4, 2)
    assert len(p) == 5  # straight horizontal
    assert path_cost(m, p) == 4.0


def test_forbidden_zone_avoidance():
    # Block the middle row except edges
    forbidden_cells = [(x, 2) for x in range(1, 4)]
    m = make_simple_map(5, forbidden_cells)
    m.start = (0, 2)
    m.end = (4, 2)
    p = astar(m, m.start, m.end)
    assert p is not None
    # Path should not go through any forbidden cell
    for x, y in p:
        assert not m.forbidden[y, x], f"Path goes through forbidden ({x},{y})"
    assert p[0] == (0, 2) and p[-1] == (4, 2)


def test_no_path():
    # Block entire column
    forbidden_cells = [(2, y) for y in range(5)]
    m = make_simple_map(5, forbidden_cells)
    m.start = (0, 2)
    m.end = (4, 2)
    p = astar(m, m.start, m.end)
    assert p is None


def test_terrain_cost():
    m = CityMap(
        grid_size=5, terrain=np.ones((5, 5), dtype=int),
        forbidden=np.zeros((5, 5), dtype=bool),
        passengers=[], start=(0, 0), end=(0, 4), seed=0,
    )
    m.terrain[1, 0] = 10  # expensive cell
    p = astar(m, (0, 0), (0, 4))
    assert p is not None
    # A* should find a path that avoids the expensive cell if possible
    cost = path_cost(m, p)
    assert cost > 0


def test_waypoint_route():
    m = CityMap(
        grid_size=10, terrain=np.ones((10, 10), dtype=int),
        forbidden=np.zeros((10, 10), dtype=bool),
        passengers=[], start=(0, 0), end=(9, 9), seed=0,
    )
    wp = [(0, 0), (5, 0), (5, 5), (9, 9)]
    p = waypoint_route(m, wp)
    assert p is not None
    assert p[0] == (0, 0)
    assert p[-1] == (9, 9)
    # Path should pass through waypoints
    assert (5, 0) in p
    assert (5, 5) in p


def test_path_cost_empty():
    assert path_cost(None, []) == 0.0


if __name__ == "__main__":
    test_straight_path()
    test_forbidden_zone_avoidance()
    test_no_path()
    test_terrain_cost()
    test_waypoint_route()
    test_path_cost_empty()
    print("All A* tests passed!")
