"""
Quantum-Inspired Optimization Algorithms for PCB Layout.

This module implements quantum-inspired optimization techniques including:
- Simulated Quantum Annealing (SQA)
- Quantum-Inspired Evolutionary Algorithm (QIEA)
- Variational Quantum Eigensolver-inspired optimization

These algorithms leverage quantum computing concepts like superposition
and tunneling to escape local minima during PCB placement optimization.
"""

import math
import random
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from quantum_pcb_builder.core.circuit import Circuit
from quantum_pcb_builder.core.component import Component


@dataclass
class QuantumState:
    """
    Represents a quantum-inspired state for optimization.

    Uses amplitude encoding to represent multiple possible solutions
    simultaneously, inspired by quantum superposition.
    """

    amplitudes: np.ndarray
    phases: np.ndarray
    num_qubits: int = 0

    def __post_init__(self) -> None:
        """Initialize qubit count from amplitude array."""
        self.num_qubits = int(np.log2(len(self.amplitudes)))

    def measure(self) -> int:
        """
        Measure the quantum state to collapse to a classical solution.

        Returns:
            Index of the measured state based on probability distribution
        """
        probabilities = np.abs(self.amplitudes) ** 2
        probabilities /= probabilities.sum()
        return int(np.random.choice(len(self.amplitudes), p=probabilities))

    def apply_rotation(self, qubit: int, angle: float) -> None:
        """
        Apply a rotation gate to a specific qubit.

        This modifies the probability amplitudes to explore new solutions.

        Args:
            qubit: Index of the qubit to rotate
            angle: Rotation angle in radians
        """
        n = len(self.amplitudes)
        step = 2 ** (qubit + 1)
        for i in range(0, n, step):
            for j in range(2**qubit):
                idx0 = i + j
                idx1 = i + j + 2**qubit
                a0 = self.amplitudes[idx0]
                a1 = self.amplitudes[idx1]
                cos_a = np.cos(angle)
                sin_a = np.sin(angle)
                self.amplitudes[idx0] = cos_a * a0 - sin_a * a1
                self.amplitudes[idx1] = sin_a * a0 + cos_a * a1

    def entangle(self, qubit1: int, qubit2: int) -> None:
        """
        Apply controlled rotation to entangle two qubits.

        This creates correlations between solution components.

        Args:
            qubit1: Control qubit
            qubit2: Target qubit
        """
        n = len(self.amplitudes)
        for i in range(n):
            if (i >> qubit1) & 1:
                j = i ^ (1 << qubit2)
                if j > i:
                    self.amplitudes[i], self.amplitudes[j] = (
                        self.amplitudes[j],
                        self.amplitudes[i],
                    )


@dataclass
class OptimizationResult:
    """Result of an optimization run."""

    best_solution: list[tuple[float, float]]
    best_cost: float
    iterations: int
    convergence_history: list[float] = field(default_factory=list)
    execution_time_ms: float = 0.0


class QuantumInspiredOptimizer(ABC):
    """
    Abstract base class for quantum-inspired optimization algorithms.

    These algorithms use concepts from quantum computing to enhance
    classical optimization, enabling better exploration of solution space.
    """

    def __init__(
        self,
        max_iterations: int = 1000,
        population_size: int = 50,
        random_seed: int | None = None,
    ) -> None:
        """
        Initialize the optimizer.

        Args:
            max_iterations: Maximum optimization iterations
            population_size: Size of solution population
            random_seed: Seed for reproducible results
        """
        self.max_iterations = max_iterations
        self.population_size = population_size
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

    @abstractmethod
    def optimize(
        self,
        circuit: Circuit,
        board_width: float,
        board_height: float,
        cost_function: Callable[[list[tuple[float, float]]], float] | None = None,
    ) -> OptimizationResult:
        """
        Optimize component placement for the given circuit.

        Args:
            circuit: Circuit to optimize
            board_width: PCB board width in mm
            board_height: PCB board height in mm
            cost_function: Custom cost function (optional)

        Returns:
            OptimizationResult with best placement found
        """


class SimulatedQuantumAnnealing(QuantumInspiredOptimizer):
    """
    Simulated Quantum Annealing optimizer for PCB placement.

    This algorithm simulates quantum tunneling effects to escape
    local minima, combining classical simulated annealing with
    quantum-inspired exploration strategies.

    The algorithm uses:
    - Transverse field strength to enable quantum tunneling
    - Trotter slices for path-integral representation
    - Temperature schedule for controlled convergence
    """

    def __init__(
        self,
        max_iterations: int = 1000,
        population_size: int = 50,
        initial_temperature: float = 100.0,
        final_temperature: float = 0.1,
        transverse_field_initial: float = 5.0,
        transverse_field_final: float = 0.01,
        trotter_slices: int = 10,
        random_seed: int | None = None,
    ) -> None:
        """
        Initialize Simulated Quantum Annealing optimizer.

        Args:
            max_iterations: Maximum iterations
            population_size: Number of parallel solutions (Trotter replicas)
            initial_temperature: Starting temperature
            final_temperature: Final temperature
            transverse_field_initial: Initial transverse field strength
            transverse_field_final: Final transverse field strength
            trotter_slices: Number of Trotter slices for quantum simulation
            random_seed: Random seed for reproducibility
        """
        super().__init__(max_iterations, population_size, random_seed)
        self.initial_temperature = initial_temperature
        self.final_temperature = final_temperature
        self.transverse_field_initial = transverse_field_initial
        self.transverse_field_final = transverse_field_final
        self.trotter_slices = trotter_slices

    def optimize(
        self,
        circuit: Circuit,
        board_width: float,
        board_height: float,
        cost_function: Callable[[list[tuple[float, float]]], float] | None = None,
    ) -> OptimizationResult:
        """
        Optimize component placement using Simulated Quantum Annealing.

        Args:
            circuit: Circuit to optimize
            board_width: PCB board width in mm
            board_height: PCB board height in mm
            cost_function: Custom cost function (optional)

        Returns:
            OptimizationResult with optimized placement
        """
        import time

        start_time = time.time()

        components = list(circuit.components.values())
        n_components = len(components)

        if n_components == 0:
            return OptimizationResult([], 0.0, 0, [], 0.0)

        # Initialize cost function
        if cost_function is None:
            cost_function = self._default_cost_function(circuit, components)

        # Initialize Trotter replicas (parallel solution representations)
        replicas = self._initialize_replicas(n_components, board_width, board_height)

        best_solution = replicas[0].copy()
        best_cost = cost_function(best_solution)
        convergence_history = [best_cost]

        # Annealing schedule
        for iteration in range(self.max_iterations):
            progress = iteration / self.max_iterations

            # Update temperature and transverse field
            temperature = self._get_temperature(progress)
            gamma = self._get_transverse_field(progress)

            # Update each Trotter replica
            for replica_idx in range(self.trotter_slices):
                current_solution = replicas[replica_idx]
                current_cost = cost_function(current_solution)

                # Generate neighbor solution with quantum-inspired perturbation
                neighbor = self._quantum_perturbation(
                    current_solution,
                    replicas[(replica_idx + 1) % self.trotter_slices],
                    gamma,
                    board_width,
                    board_height,
                )

                neighbor_cost = cost_function(neighbor)

                # Metropolis acceptance with quantum tunneling probability
                delta_e = neighbor_cost - current_cost
                tunneling_factor = gamma * self._coupling_strength(current_solution, neighbor)

                acceptance_prob = self._acceptance_probability(
                    delta_e, temperature, tunneling_factor
                )

                if random.random() < acceptance_prob:
                    replicas[replica_idx] = neighbor
                    if neighbor_cost < best_cost:
                        best_solution = neighbor.copy()
                        best_cost = neighbor_cost

            convergence_history.append(best_cost)

            # Early termination if converged
            if self._is_converged(convergence_history):
                break

        execution_time = (time.time() - start_time) * 1000

        return OptimizationResult(
            best_solution=best_solution,
            best_cost=best_cost,
            iterations=iteration + 1,
            convergence_history=convergence_history,
            execution_time_ms=execution_time,
        )

    def _initialize_replicas(
        self, n_components: int, board_width: float, board_height: float
    ) -> list[list[tuple[float, float]]]:
        """Initialize Trotter replicas with random positions."""
        replicas = []
        for _ in range(self.trotter_slices):
            solution = [
                (
                    random.uniform(5, board_width - 5),
                    random.uniform(5, board_height - 5),
                )
                for _ in range(n_components)
            ]
            replicas.append(solution)
        return replicas

    def _get_temperature(self, progress: float) -> float:
        """Calculate temperature at current progress using exponential decay."""
        return self.initial_temperature * math.exp(
            progress * math.log(self.final_temperature / self.initial_temperature)
        )

    def _get_transverse_field(self, progress: float) -> float:
        """Calculate transverse field strength at current progress."""
        return self.transverse_field_initial * math.exp(
            progress * math.log(self.transverse_field_final / self.transverse_field_initial)
        )

    def _quantum_perturbation(
        self,
        current: list[tuple[float, float]],
        adjacent_replica: list[tuple[float, float]],
        gamma: float,
        board_width: float,
        board_height: float,
    ) -> list[tuple[float, float]]:
        """
        Generate a neighbor solution using quantum-inspired perturbation.

        The perturbation is influenced by adjacent Trotter replica,
        simulating quantum tunneling between states.
        """
        neighbor = []
        for i, (x, y) in enumerate(current):
            adj_x, adj_y = adjacent_replica[i]

            # Quantum tunneling component
            tunnel_x = gamma * (adj_x - x) * random.gauss(0, 0.3)
            tunnel_y = gamma * (adj_y - y) * random.gauss(0, 0.3)

            # Classical random walk component
            classical_x = random.gauss(0, 2.0)
            classical_y = random.gauss(0, 2.0)

            new_x = x + tunnel_x + classical_x
            new_y = y + tunnel_y + classical_y

            # Ensure within bounds
            new_x = max(5, min(board_width - 5, new_x))
            new_y = max(5, min(board_height - 5, new_y))

            neighbor.append((new_x, new_y))

        return neighbor

    def _coupling_strength(
        self,
        solution1: list[tuple[float, float]],
        solution2: list[tuple[float, float]],
    ) -> float:
        """Calculate coupling strength between two solutions."""
        total_dist = 0.0
        for (x1, y1), (x2, y2) in zip(solution1, solution2, strict=True):
            total_dist += ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        return 1.0 / (1.0 + total_dist / len(solution1))

    def _acceptance_probability(
        self, delta_e: float, temperature: float, tunneling_factor: float
    ) -> float:
        """Calculate acceptance probability including quantum tunneling."""
        if delta_e <= 0:
            return 1.0

        classical_prob = math.exp(-delta_e / temperature) if temperature > 0 else 0.0
        quantum_boost = tunneling_factor * math.exp(-delta_e * 0.5 / temperature)

        return min(1.0, classical_prob + quantum_boost)

    def _default_cost_function(
        self, circuit: Circuit, components: list[Component]
    ) -> Callable[[list[tuple[float, float]]], float]:
        """Create default cost function based on wire length and overlaps."""

        def cost(positions: list[tuple[float, float]]) -> float:
            # Update component positions
            for comp, pos in zip(components, positions, strict=True):
                comp.position = pos

            # Wire length cost
            wire_length = circuit.estimate_total_wire_length()

            # Overlap penalty
            overlap_penalty = 0.0
            for i, comp1 in enumerate(components):
                for comp2 in components[i + 1 :]:
                    if comp1.overlaps(comp2):
                        overlap_penalty += 1000.0

            return wire_length + overlap_penalty

        return cost

    def _is_converged(
        self, history: list[float], window: int = 50, threshold: float = 1e-6
    ) -> bool:
        """Check if optimization has converged."""
        if len(history) < window:
            return False
        recent = history[-window:]
        return max(recent) - min(recent) < threshold


class QuantumEvolutionaryAlgorithm(QuantumInspiredOptimizer):
    """
    Quantum-Inspired Evolutionary Algorithm (QIEA) for PCB optimization.

    Uses quantum bits (Q-bits) to represent solution probabilities,
    with quantum rotation gates for evolution.
    """

    def __init__(
        self,
        max_iterations: int = 500,
        population_size: int = 30,
        num_qubits_per_dim: int = 10,
        rotation_angle: float = 0.01 * math.pi,
        random_seed: int | None = None,
    ) -> None:
        """
        Initialize QIEA optimizer.

        Args:
            max_iterations: Maximum iterations
            population_size: Population size
            num_qubits_per_dim: Qubits per dimension for encoding
            rotation_angle: Base rotation angle for Q-gate
            random_seed: Random seed
        """
        super().__init__(max_iterations, population_size, random_seed)
        self.num_qubits_per_dim = num_qubits_per_dim
        self.rotation_angle = rotation_angle

    def optimize(
        self,
        circuit: Circuit,
        board_width: float,
        board_height: float,
        cost_function: Callable[[list[tuple[float, float]]], float] | None = None,
    ) -> OptimizationResult:
        """
        Optimize using Quantum-Inspired Evolutionary Algorithm.

        Args:
            circuit: Circuit to optimize
            board_width: PCB board width in mm
            board_height: PCB board height in mm
            cost_function: Custom cost function (optional)

        Returns:
            OptimizationResult with optimized placement
        """
        import time

        start_time = time.time()

        components = list(circuit.components.values())
        n_components = len(components)

        if n_components == 0:
            return OptimizationResult([], 0.0, 0, [], 0.0)

        if cost_function is None:
            cost_function = self._default_cost_function(circuit, components)

        # Initialize quantum population (Q-bit representation)
        num_dims = n_components * 2
        q_population = self._initialize_q_population(num_dims)

        # Best solution tracking
        best_solution: list[tuple[float, float]] = []
        best_cost = float("inf")
        convergence_history: list[float] = []

        for _ in range(self.max_iterations):
            # Observe classical solutions from quantum population
            solutions = self._observe_solutions(
                q_population, n_components, board_width, board_height
            )

            # Evaluate all solutions
            costs = [cost_function(sol) for sol in solutions]

            # Update best
            min_idx = int(np.argmin(costs))
            if costs[min_idx] < best_cost:
                best_cost = costs[min_idx]
                best_solution = solutions[min_idx].copy()

            convergence_history.append(best_cost)

            # Update Q-bits using rotation gates
            for i, (solution, cost) in enumerate(zip(solutions, costs, strict=True)):
                if cost >= best_cost:
                    # Rotate towards best solution
                    self._rotate_towards_best(
                        q_population[i],
                        self._encode_solution(best_solution, board_width, board_height),
                        self._encode_solution(solution, board_width, board_height),
                    )

        execution_time = (time.time() - start_time) * 1000

        return OptimizationResult(
            best_solution=best_solution,
            best_cost=best_cost,
            iterations=self.max_iterations,
            convergence_history=convergence_history,
            execution_time_ms=execution_time,
        )

    def _initialize_q_population(self, num_dims: int) -> list[np.ndarray]:
        """Initialize Q-bit population with uniform superposition."""
        q_population = []
        for _ in range(self.population_size):
            q_individual = np.full(
                (num_dims, self.num_qubits_per_dim, 2),
                1.0 / math.sqrt(2),
            )
            q_population.append(q_individual)
        return q_population

    def _observe_solutions(
        self,
        q_population: list[np.ndarray],
        n_components: int,
        board_width: float,
        board_height: float,
    ) -> list[list[tuple[float, float]]]:
        """Observe classical solutions from quantum population."""
        solutions = []
        for q_individual in q_population:
            solution = []
            for i in range(n_components):
                x_idx = i * 2
                y_idx = i * 2 + 1

                x_binary = self._collapse_qubits(q_individual[x_idx])
                y_binary = self._collapse_qubits(q_individual[y_idx])

                x = 5 + (board_width - 10) * x_binary / (2**self.num_qubits_per_dim - 1)
                y = 5 + (board_height - 10) * y_binary / (2**self.num_qubits_per_dim - 1)

                solution.append((x, y))
            solutions.append(solution)
        return solutions

    def _collapse_qubits(self, qubits: np.ndarray) -> int:
        """Collapse Q-bits to classical binary value."""
        value = 0
        for j, qubit in enumerate(qubits):
            prob_one = qubit[1] ** 2
            if random.random() < prob_one:
                value |= 1 << j
        return value

    def _encode_solution(
        self,
        solution: list[tuple[float, float]],
        board_width: float,
        board_height: float,
    ) -> list[int]:
        """Encode solution as binary values."""
        encoded = []
        max_val = 2**self.num_qubits_per_dim - 1
        for x, y in solution:
            x_norm = (x - 5) / (board_width - 10)
            y_norm = (y - 5) / (board_height - 10)
            encoded.append(int(x_norm * max_val))
            encoded.append(int(y_norm * max_val))
        return encoded

    def _rotate_towards_best(
        self,
        q_individual: np.ndarray,
        best_encoded: list[int],
        current_encoded: list[int],
    ) -> None:
        """Rotate Q-bits towards best solution."""
        for dim_idx in range(len(best_encoded)):
            for qubit_idx in range(self.num_qubits_per_dim):
                best_bit = (best_encoded[dim_idx] >> qubit_idx) & 1
                curr_bit = (current_encoded[dim_idx] >> qubit_idx) & 1

                if best_bit != curr_bit:
                    angle = self.rotation_angle if best_bit == 1 else -self.rotation_angle

                    cos_a = math.cos(angle)
                    sin_a = math.sin(angle)

                    alpha = q_individual[dim_idx, qubit_idx, 0]
                    beta = q_individual[dim_idx, qubit_idx, 1]

                    q_individual[dim_idx, qubit_idx, 0] = cos_a * alpha - sin_a * beta
                    q_individual[dim_idx, qubit_idx, 1] = sin_a * alpha + cos_a * beta

    def _default_cost_function(
        self, circuit: Circuit, components: list[Component]
    ) -> Callable[[list[tuple[float, float]]], float]:
        """Create default cost function."""

        def cost(positions: list[tuple[float, float]]) -> float:
            for comp, pos in zip(components, positions, strict=True):
                comp.position = pos

            wire_length = circuit.estimate_total_wire_length()

            overlap_penalty = 0.0
            for i, comp1 in enumerate(components):
                for comp2 in components[i + 1 :]:
                    if comp1.overlaps(comp2):
                        overlap_penalty += 1000.0

            return wire_length + overlap_penalty

        return cost
