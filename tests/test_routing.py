"""Tests for routing algorithms."""

from quantum_pcb_builder.algorithms.routing import (
    AStarRouter,
    LeeRouter,
    MazeRouter,
    RoutingGrid,
    RoutingPath,
    route_board,
)
from quantum_pcb_builder.core.component import Component, ComponentType, Footprint
from quantum_pcb_builder.core.pcb import PCBBoard


class TestRoutingGrid:
    """Tests for RoutingGrid class."""

    def test_grid_creation(self) -> None:
        """Test basic grid creation."""
        grid = RoutingGrid(
            width=100,
            height=100,
            layers=2,
            resolution_mm=0.25,
        )

        assert grid.width == 100
        assert grid.height == 100
        assert grid.layers == 2
        assert grid.cells.shape == (2, 100, 100)

    def test_set_obstacle(self) -> None:
        """Test setting obstacles."""
        grid = RoutingGrid(width=50, height=50, layers=2, resolution_mm=0.5)

        grid.set_obstacle(10, 10, 0)

        assert grid.is_blocked(10, 10, 0)
        assert not grid.is_blocked(10, 10, 1)

    def test_set_obstacle_all_layers(self) -> None:
        """Test setting obstacle on all layers."""
        grid = RoutingGrid(width=50, height=50, layers=2, resolution_mm=0.5)

        grid.set_obstacle(10, 10, -1)

        assert grid.is_blocked(10, 10, 0)
        assert grid.is_blocked(10, 10, 1)

    def test_is_blocked_out_of_bounds(self) -> None:
        """Test blocked check for out-of-bounds coordinates."""
        grid = RoutingGrid(width=50, height=50, layers=2, resolution_mm=0.5)

        assert grid.is_blocked(-1, 0, 0) is True
        assert grid.is_blocked(0, -1, 0) is True
        assert grid.is_blocked(50, 0, 0) is True
        assert grid.is_blocked(0, 50, 0) is True

    def test_from_pcb_board(self) -> None:
        """Test creating grid from PCB board."""
        board = PCBBoard(
            name="Test",
            width_mm=50.0,
            height_mm=50.0,
            layer_count=2,
        )

        comp = Component(
            name="U1",
            component_type=ComponentType.IC,
            footprint=Footprint("QFN", 6.0, 6.0, 32),
        )
        board.place_component(comp, (25.0, 25.0))

        grid = RoutingGrid.from_pcb_board(board, resolution_mm=0.5)

        assert grid.width == 100
        assert grid.height == 100
        assert grid.is_blocked(50, 50, 0)


class TestAStarRouter:
    """Tests for A* router."""

    def test_router_creation(self) -> None:
        """Test router initialization."""
        router = AStarRouter(via_cost=15.0, turn_cost=2.0)

        assert router.via_cost == 15.0
        assert router.turn_cost == 2.0

    def test_route_simple_path(self) -> None:
        """Test routing a simple path."""
        grid = RoutingGrid(width=50, height=50, layers=1, resolution_mm=0.5)
        router = AStarRouter()

        path = router.route(grid, (5, 5, 0), (45, 5, 0))

        assert path is not None
        assert isinstance(path, RoutingPath)
        assert path.segments[0] == (5, 5, 0)
        assert path.segments[-1] == (45, 5, 0)

    def test_route_around_obstacle(self) -> None:
        """Test routing around an obstacle."""
        grid = RoutingGrid(width=50, height=50, layers=1, resolution_mm=0.5)

        for x in range(20, 30):
            grid.set_obstacle(x, 25, 0)

        router = AStarRouter()
        path = router.route(grid, (10, 25, 0), (40, 25, 0))

        assert path is not None
        for x, y, layer in path.segments:
            assert not grid.is_blocked(x, y, layer)

    def test_route_no_path(self) -> None:
        """Test when no path exists."""
        grid = RoutingGrid(width=50, height=50, layers=1, resolution_mm=0.5)

        for x in range(50):
            grid.set_obstacle(x, 25, 0)

        router = AStarRouter()
        path = router.route(grid, (10, 10, 0), (10, 40, 0))

        assert path is None

    def test_route_blocked_start(self) -> None:
        """Test routing from blocked start."""
        grid = RoutingGrid(width=50, height=50, layers=1, resolution_mm=0.5)
        grid.set_obstacle(10, 10, 0)

        router = AStarRouter()
        path = router.route(grid, (10, 10, 0), (40, 40, 0))

        assert path is None

    def test_route_multi_layer(self) -> None:
        """Test multi-layer routing."""
        grid = RoutingGrid(width=50, height=50, layers=2, resolution_mm=0.5)

        for x in range(50):
            grid.set_obstacle(x, 25, 0)

        router = AStarRouter(via_cost=5.0)
        path = router.route(grid, (10, 10, 0), (10, 40, 0))

        assert path is not None
        assert path.via_count > 0


class TestLeeRouter:
    """Tests for Lee's algorithm router."""

    def test_lee_router_creation(self) -> None:
        """Test Lee router initialization."""
        router = LeeRouter(via_cost=10.0)
        assert router.via_cost == 10.0

    def test_lee_route_simple(self) -> None:
        """Test simple routing with Lee's algorithm."""
        grid = RoutingGrid(width=50, height=50, layers=1, resolution_mm=0.5)
        router = LeeRouter()

        path = router.route(grid, (5, 5, 0), (25, 25, 0))

        assert path is not None
        assert path.segments[0] == (5, 5, 0)
        assert path.segments[-1] == (25, 25, 0)

    def test_lee_shortest_path(self) -> None:
        """Test Lee's algorithm finds shortest path."""
        grid = RoutingGrid(width=50, height=50, layers=1, resolution_mm=0.5)
        router = LeeRouter()

        path = router.route(grid, (0, 0, 0), (10, 0, 0))

        assert path is not None
        assert len(path.segments) == 11


class TestMazeRouter:
    """Tests for maze router."""

    def test_maze_router_creation(self) -> None:
        """Test maze router initialization."""
        router = MazeRouter(congestion_weight=2.0)
        assert router.congestion_weight == 2.0

    def test_maze_route(self) -> None:
        """Test maze routing."""
        grid = RoutingGrid(width=50, height=50, layers=1, resolution_mm=0.5)
        router = MazeRouter()

        path = router.route(grid, (5, 5, 0), (40, 40, 0))

        assert path is not None


class TestRouteNet:
    """Tests for net routing."""

    def test_route_multi_pin_net(self) -> None:
        """Test routing a multi-pin net."""
        grid = RoutingGrid(width=100, height=100, layers=1, resolution_mm=0.5)
        router = AStarRouter()

        pins = [
            (10, 10, 0),
            (50, 10, 0),
            (50, 50, 0),
            (10, 50, 0),
        ]

        routes = router.route_net(grid, pins)

        assert len(routes) == len(pins) - 1


class TestRouteBoardFunction:
    """Tests for board routing function."""

    def test_route_board_simple(self) -> None:
        """Test routing a simple board."""
        board = PCBBoard(
            name="Test",
            width_mm=100.0,
            height_mm=100.0,
            layer_count=2,
        )

        nets = {
            "NET1": [
                (10.0, 10.0, "top"),
                (50.0, 10.0, "top"),
            ],
            "NET2": [
                (10.0, 50.0, "top"),
                (50.0, 50.0, "top"),
            ],
        }

        result = route_board(board, nets)

        assert "routed_nets" in result
        assert "total_vias" in result
        assert "success_rate" in result
        assert result["success_rate"] > 0
