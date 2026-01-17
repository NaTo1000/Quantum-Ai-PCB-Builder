"""
PCB Trace Routing Algorithms.

This module implements advanced routing algorithms for PCB trace routing:
- A* pathfinding with obstacle avoidance
- Lee's algorithm (breadth-first wave propagation)
- Maze routing with cost optimization
- Multi-layer routing support
"""

import heapq
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import numpy as np

from quantum_pcb_builder.core.pcb import PCBBoard


class RoutingCost(Enum):
    """Cost factors for routing optimization."""

    LENGTH = auto()
    VIAS = auto()
    TURNS = auto()
    CONGESTION = auto()


@dataclass
class GridCell:
    """Represents a cell in the routing grid."""

    x: int
    y: int
    layer: int = 0
    blocked: bool = False
    cost: float = 1.0
    net_id: str | None = None


@dataclass
class RoutingPath:
    """Represents a routed path between two points."""

    segments: list[tuple[int, int, int]]
    total_cost: float
    via_count: int = 0
    turn_count: int = 0
    length: float = 0.0


@dataclass
class RoutingGrid:
    """
    Discretized grid for routing algorithms.

    Converts the continuous PCB space into a discrete grid for
    pathfinding algorithms.
    """

    width: int
    height: int
    layers: int
    resolution_mm: float
    cells: np.ndarray = field(default_factory=lambda: np.array([]))

    def __post_init__(self) -> None:
        """Initialize the grid cells."""
        self.cells = np.zeros((self.layers, self.height, self.width), dtype=np.float32)

    def set_obstacle(self, x: int, y: int, layer: int = -1) -> None:
        """Mark a cell as an obstacle."""
        if layer == -1:
            for layer_idx in range(self.layers):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.cells[layer_idx, y, x] = -1
        elif 0 <= x < self.width and 0 <= y < self.height and 0 <= layer < self.layers:
            self.cells[layer, y, x] = -1

    def is_blocked(self, x: int, y: int, layer: int = 0) -> bool:
        """Check if a cell is blocked."""
        if not (0 <= x < self.width and 0 <= y < self.height and 0 <= layer < self.layers):
            return True
        return self.cells[layer, y, x] < 0

    def set_cost(self, x: int, y: int, layer: int, cost: float) -> None:
        """Set the traversal cost for a cell."""
        if 0 <= x < self.width and 0 <= y < self.height and 0 <= layer < self.layers:
            self.cells[layer, y, x] = cost

    def get_cost(self, x: int, y: int, layer: int) -> float:
        """Get the traversal cost for a cell."""
        if not (0 <= x < self.width and 0 <= y < self.height and 0 <= layer < self.layers):
            return float("inf")
        return float(self.cells[layer, y, x]) if self.cells[layer, y, x] >= 0 else float("inf")

    @classmethod
    def from_pcb_board(cls, board: PCBBoard, resolution_mm: float = 0.25) -> "RoutingGrid":
        """
        Create a routing grid from a PCB board.

        Args:
            board: PCB board to convert
            resolution_mm: Grid resolution in mm

        Returns:
            RoutingGrid instance
        """
        width = int(board.width_mm / resolution_mm)
        height = int(board.height_mm / resolution_mm)
        layers = board.layer_count

        grid = cls(
            width=width,
            height=height,
            layers=layers,
            resolution_mm=resolution_mm,
        )

        # Mark component areas as obstacles
        for component in board.components.values():
            bbox = component.get_bounding_box()
            x1 = int(bbox[0] / resolution_mm)
            y1 = int(bbox[1] / resolution_mm)
            x2 = int(bbox[2] / resolution_mm)
            y2 = int(bbox[3] / resolution_mm)

            layer_idx = 0 if component.layer == "top" else layers - 1

            for x in range(max(0, x1), min(width, x2 + 1)):
                for y in range(max(0, y1), min(height, y2 + 1)):
                    grid.set_obstacle(x, y, layer_idx)

        return grid


class Router(ABC):
    """Abstract base class for routing algorithms."""

    def __init__(
        self,
        via_cost: float = 10.0,
        turn_cost: float = 1.0,
        layer_preference: int = 0,
    ) -> None:
        """
        Initialize router.

        Args:
            via_cost: Cost penalty for layer changes (vias)
            turn_cost: Cost penalty for direction changes
            layer_preference: Preferred routing layer
        """
        self.via_cost = via_cost
        self.turn_cost = turn_cost
        self.layer_preference = layer_preference

    @abstractmethod
    def route(
        self,
        grid: RoutingGrid,
        start: tuple[int, int, int],
        end: tuple[int, int, int],
    ) -> RoutingPath | None:
        """
        Find a route between two points.

        Args:
            grid: Routing grid
            start: Start position (x, y, layer)
            end: End position (x, y, layer)

        Returns:
            RoutingPath if found, None otherwise
        """

    def route_net(
        self,
        grid: RoutingGrid,
        pins: list[tuple[int, int, int]],
    ) -> list[RoutingPath]:
        """
        Route a complete net connecting multiple pins.

        Uses minimum spanning tree approach for multi-pin nets.

        Args:
            grid: Routing grid
            pins: List of pin positions to connect

        Returns:
            List of RoutingPaths connecting all pins
        """
        if len(pins) < 2:
            return []

        # Simple sequential routing (Steiner tree approximation)
        routes = []
        connected = [pins[0]]

        remaining = list(pins[1:])
        while remaining:
            best_route = None
            best_cost = float("inf")
            best_pin_idx = -1

            for i, pin in enumerate(remaining):
                for connected_pin in connected:
                    route = self.route(grid, connected_pin, pin)
                    if route and route.total_cost < best_cost:
                        best_route = route
                        best_cost = route.total_cost
                        best_pin_idx = i

            if best_route is None:
                break

            routes.append(best_route)
            connected.append(remaining.pop(best_pin_idx))

            # Mark route as occupied
            self._mark_route_used(grid, best_route)

        return routes

    def _mark_route_used(self, grid: RoutingGrid, route: RoutingPath) -> None:
        """Mark cells used by a route as occupied."""
        for x, y, layer in route.segments:
            grid.set_cost(x, y, layer, 5.0)


class AStarRouter(Router):
    """
    A* pathfinding algorithm for PCB routing.

    Uses heuristic-guided search for efficient routing with
    obstacle avoidance and cost optimization.
    """

    def __init__(
        self,
        via_cost: float = 10.0,
        turn_cost: float = 1.0,
        layer_preference: int = 0,
        diagonal: bool = False,
    ) -> None:
        """
        Initialize A* router.

        Args:
            via_cost: Cost for layer changes
            turn_cost: Cost for direction changes
            layer_preference: Preferred routing layer
            diagonal: Allow diagonal routing
        """
        super().__init__(via_cost, turn_cost, layer_preference)
        self.diagonal = diagonal

    def route(
        self,
        grid: RoutingGrid,
        start: tuple[int, int, int],
        end: tuple[int, int, int],
    ) -> RoutingPath | None:
        """
        Find optimal route using A* algorithm.

        Args:
            grid: Routing grid
            start: Start position (x, y, layer)
            end: End position (x, y, layer)

        Returns:
            RoutingPath if found, None otherwise
        """
        if grid.is_blocked(start[0], start[1], start[2]):
            return None
        if grid.is_blocked(end[0], end[1], end[2]):
            return None

        # Priority queue: (f_score, g_score, x, y, layer, prev_direction)
        open_set: list[tuple[float, float, int, int, int, int]] = []
        heapq.heappush(
            open_set, (self._heuristic(start, end), 0.0, start[0], start[1], start[2], -1)
        )

        came_from: dict[tuple[int, int, int], tuple[int, int, int]] = {}
        g_score: dict[tuple[int, int, int], float] = {start: 0.0}

        directions = self._get_directions()

        while open_set:
            _, current_g, x, y, layer, prev_dir = heapq.heappop(open_set)
            current = (x, y, layer)

            if current == end:
                return self._reconstruct_path(came_from, end, start)

            if current in came_from and current_g > g_score.get(current, float("inf")):
                continue

            # Explore neighbors
            for dir_idx, (dx, dy, dl) in enumerate(directions):
                nx, ny, nl = x + dx, y + dy, layer + dl

                if grid.is_blocked(nx, ny, nl):
                    continue

                # Calculate movement cost
                move_cost = grid.get_cost(nx, ny, nl)
                if dl != 0:
                    move_cost += self.via_cost
                if prev_dir >= 0 and dir_idx != prev_dir:
                    move_cost += self.turn_cost

                tentative_g = current_g + move_cost
                neighbor = (nx, ny, nl)

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score, tentative_g, nx, ny, nl, dir_idx))

        return None

    def _get_directions(self) -> list[tuple[int, int, int]]:
        """Get movement directions."""
        directions = [
            (1, 0, 0),
            (-1, 0, 0),
            (0, 1, 0),
            (0, -1, 0),
            (0, 0, 1),
            (0, 0, -1),
        ]
        if self.diagonal:
            directions.extend(
                [
                    (1, 1, 0),
                    (1, -1, 0),
                    (-1, 1, 0),
                    (-1, -1, 0),
                ]
            )
        return directions

    def _heuristic(self, pos: tuple[int, int, int], goal: tuple[int, int, int]) -> float:
        """Calculate heuristic (Manhattan distance with layer penalty)."""
        dx = abs(pos[0] - goal[0])
        dy = abs(pos[1] - goal[1])
        dl = abs(pos[2] - goal[2])
        return dx + dy + dl * self.via_cost

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int, int], tuple[int, int, int]],
        end: tuple[int, int, int],
        start: tuple[int, int, int],
    ) -> RoutingPath:
        """Reconstruct path from came_from dictionary."""
        path = [end]
        current = end

        while current in came_from:
            current = came_from[current]
            path.append(current)

        path.reverse()

        # Calculate metrics
        via_count = sum(1 for i in range(1, len(path)) if path[i][2] != path[i - 1][2])
        turn_count = self._count_turns(path)
        length = len(path) - 1

        return RoutingPath(
            segments=path,
            total_cost=length + via_count * self.via_cost + turn_count * self.turn_cost,
            via_count=via_count,
            turn_count=turn_count,
            length=float(length),
        )

    def _count_turns(self, path: list[tuple[int, int, int]]) -> int:
        """Count direction changes in path."""
        if len(path) < 3:
            return 0

        turns = 0
        for i in range(2, len(path)):
            dx1 = path[i - 1][0] - path[i - 2][0]
            dy1 = path[i - 1][1] - path[i - 2][1]
            dx2 = path[i][0] - path[i - 1][0]
            dy2 = path[i][1] - path[i - 1][1]

            if dx1 != dx2 or dy1 != dy2:
                turns += 1

        return turns


class LeeRouter(Router):
    """
    Lee's algorithm (wave propagation) for PCB routing.

    Guarantees shortest path when one exists, using breadth-first
    wave expansion.
    """

    def route(
        self,
        grid: RoutingGrid,
        start: tuple[int, int, int],
        end: tuple[int, int, int],
    ) -> RoutingPath | None:
        """
        Find shortest route using Lee's algorithm.

        Args:
            grid: Routing grid
            start: Start position (x, y, layer)
            end: End position (x, y, layer)

        Returns:
            RoutingPath if found, None otherwise
        """
        if grid.is_blocked(start[0], start[1], start[2]):
            return None
        if grid.is_blocked(end[0], end[1], end[2]):
            return None

        # Wave propagation grid
        wave = np.full(
            (grid.layers, grid.height, grid.width),
            -1,
            dtype=np.int32,
        )
        wave[start[2], start[1], start[0]] = 0

        queue = [start]
        found = False

        directions = [
            (1, 0, 0),
            (-1, 0, 0),
            (0, 1, 0),
            (0, -1, 0),
            (0, 0, 1),
            (0, 0, -1),
        ]

        # Forward wave propagation
        while queue and not found:
            next_queue = []
            for x, y, layer in queue:
                current_wave = wave[layer, y, x]

                for dx, dy, dl in directions:
                    nx, ny, nl = x + dx, y + dy, layer + dl

                    if not grid.is_blocked(nx, ny, nl) and wave[nl, ny, nx] == -1:
                        wave[nl, ny, nx] = current_wave + 1
                        next_queue.append((nx, ny, nl))

                        if (nx, ny, nl) == end:
                            found = True
                            break

                if found:
                    break

            queue = next_queue

        if not found:
            return None

        # Backtrace to find path
        path = [end]
        current = end

        while current != start:
            x, y, layer = current
            current_wave = wave[layer, y, x]

            for dx, dy, dl in directions:
                nx, ny, nl = x + dx, y + dy, layer + dl
                if (
                    0 <= nx < grid.width
                    and 0 <= ny < grid.height
                    and 0 <= nl < grid.layers
                    and wave[nl, ny, nx] == current_wave - 1
                ):
                    current = (nx, ny, nl)
                    path.append(current)
                    break

        path.reverse()

        via_count = sum(1 for i in range(1, len(path)) if path[i][2] != path[i - 1][2])

        return RoutingPath(
            segments=path,
            total_cost=len(path) - 1 + via_count * self.via_cost,
            via_count=via_count,
            length=float(len(path) - 1),
        )


class MazeRouter(Router):
    """
    Maze routing with multi-objective cost optimization.

    Combines A* efficiency with Lee's completeness guarantee,
    optimizing for length, vias, and congestion.
    """

    def __init__(
        self,
        via_cost: float = 10.0,
        turn_cost: float = 1.0,
        congestion_weight: float = 2.0,
        layer_preference: int = 0,
    ) -> None:
        """
        Initialize maze router.

        Args:
            via_cost: Cost for layer changes
            turn_cost: Cost for direction changes
            congestion_weight: Weight for congestion avoidance
            layer_preference: Preferred routing layer
        """
        super().__init__(via_cost, turn_cost, layer_preference)
        self.congestion_weight = congestion_weight

    def route(
        self,
        grid: RoutingGrid,
        start: tuple[int, int, int],
        end: tuple[int, int, int],
    ) -> RoutingPath | None:
        """
        Find optimal route using maze routing.

        Args:
            grid: Routing grid
            start: Start position (x, y, layer)
            end: End position (x, y, layer)

        Returns:
            RoutingPath if found, None otherwise
        """
        # Use A* with congestion-aware cost function
        astar = AStarRouter(
            via_cost=self.via_cost,
            turn_cost=self.turn_cost,
            layer_preference=self.layer_preference,
        )

        # Modify grid costs based on congestion
        self._apply_congestion_costs(grid)

        return astar.route(grid, start, end)

    def _apply_congestion_costs(self, grid: RoutingGrid) -> None:
        """Apply congestion-based cost modifiers to grid."""
        # Simple congestion estimation based on obstacle density
        for layer in range(grid.layers):
            for y in range(grid.height):
                for x in range(grid.width):
                    if not grid.is_blocked(x, y, layer):
                        # Count nearby obstacles
                        obstacle_count = 0
                        for dx in range(-2, 3):
                            for dy in range(-2, 3):
                                if grid.is_blocked(x + dx, y + dy, layer):
                                    obstacle_count += 1

                        # Increase cost in congested areas
                        congestion_factor = 1.0 + (obstacle_count / 25.0) * self.congestion_weight
                        current_cost = grid.get_cost(x, y, layer)
                        grid.set_cost(x, y, layer, current_cost * congestion_factor)


def route_board(
    board: PCBBoard,
    nets: dict[str, list[tuple[float, float, str]]],
    router: Router | None = None,
    resolution_mm: float = 0.25,
) -> dict[str, Any]:
    """
    Route all nets on a PCB board.

    Args:
        board: PCB board to route
        nets: Dictionary mapping net names to lists of (x, y, layer) pin positions
        router: Router to use (defaults to AStarRouter)
        resolution_mm: Grid resolution in mm

    Returns:
        Dictionary with routing results and statistics
    """
    if router is None:
        router = AStarRouter()

    grid = RoutingGrid.from_pcb_board(board, resolution_mm)

    results: dict[str, list[RoutingPath]] = {}
    total_vias = 0
    total_length = 0.0
    failed_nets = []

    for net_name, pins in nets.items():
        # Convert mm positions to grid coordinates
        grid_pins = []
        for x_mm, y_mm, layer_name in pins:
            x = int(x_mm / resolution_mm)
            y = int(y_mm / resolution_mm)
            layer_idx = 0 if layer_name == "top" else board.layer_count - 1
            grid_pins.append((x, y, layer_idx))

        routes = router.route_net(grid, grid_pins)

        if len(routes) == len(pins) - 1:
            results[net_name] = routes
            for route in routes:
                total_vias += route.via_count
                total_length += route.length * resolution_mm
        else:
            failed_nets.append(net_name)

    return {
        "routed_nets": results,
        "total_vias": total_vias,
        "total_length_mm": total_length,
        "failed_nets": failed_nets,
        "success_rate": len(results) / len(nets) if nets else 1.0,
    }
