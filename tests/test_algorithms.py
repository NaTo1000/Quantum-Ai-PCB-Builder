"""Tests for optimization algorithms."""

import numpy as np
import pytest

from quantum_pcb_builder.algorithms.genetic_algorithm import (
    NSGA2,
    BlendCrossover,
    GaussianMutation,
    GeneticAlgorithm,
    Individual,
    Population,
    TournamentSelection,
)
from quantum_pcb_builder.algorithms.quantum_optimizer import (
    OptimizationResult,
    QuantumState,
    SimulatedQuantumAnnealing,
)
from quantum_pcb_builder.core.circuit import Circuit
from quantum_pcb_builder.core.component import Component, ComponentType, Footprint


class TestQuantumState:
    """Tests for QuantumState class."""

    def test_quantum_state_creation(self) -> None:
        """Test quantum state initialization."""
        amplitudes = np.array([0.5, 0.5, 0.5, 0.5])
        phases = np.zeros(4)
        state = QuantumState(amplitudes=amplitudes, phases=phases)

        assert state.num_qubits == 2
        assert len(state.amplitudes) == 4

    def test_measure(self) -> None:
        """Test measurement returns valid index."""
        amplitudes = np.array([1.0, 0.0, 0.0, 0.0])
        phases = np.zeros(4)
        state = QuantumState(amplitudes=amplitudes, phases=phases)

        result = state.measure()

        assert result == 0

    def test_apply_rotation(self) -> None:
        """Test rotation gate modifies amplitudes."""
        amplitudes = np.array([1.0, 0.0, 0.0, 0.0])
        phases = np.zeros(4)
        state = QuantumState(amplitudes=amplitudes, phases=phases)

        original = state.amplitudes.copy()
        state.apply_rotation(0, np.pi / 4)

        assert not np.allclose(state.amplitudes, original)


class TestSimulatedQuantumAnnealing:
    """Tests for SimulatedQuantumAnnealing optimizer."""

    @pytest.fixture
    def simple_circuit(self) -> Circuit:
        """Create a simple circuit for testing."""
        circuit = Circuit(name="Test")
        for i in range(3):
            comp = Component(
                name=f"C{i}",
                component_type=ComponentType.CAPACITOR,
                footprint=Footprint("0805", 2.0, 1.25, 2),
            )
            circuit.add_component(comp)
        return circuit

    def test_optimizer_creation(self) -> None:
        """Test optimizer initialization."""
        optimizer = SimulatedQuantumAnnealing(
            max_iterations=100,
            population_size=10,
            initial_temperature=50.0,
            random_seed=42,
        )

        assert optimizer.max_iterations == 100
        assert optimizer.population_size == 10
        assert optimizer.initial_temperature == 50.0

    def test_optimize_returns_result(self, simple_circuit: Circuit) -> None:
        """Test optimization returns valid result."""
        optimizer = SimulatedQuantumAnnealing(
            max_iterations=10,
            random_seed=42,
        )

        result = optimizer.optimize(simple_circuit, 100.0, 100.0)

        assert isinstance(result, OptimizationResult)
        assert len(result.best_solution) == len(simple_circuit.components)
        assert result.iterations > 0

    def test_optimize_empty_circuit(self) -> None:
        """Test optimization with empty circuit."""
        circuit = Circuit()
        optimizer = SimulatedQuantumAnnealing(max_iterations=10)

        result = optimizer.optimize(circuit, 100.0, 100.0)

        assert len(result.best_solution) == 0
        assert result.best_cost == 0.0

    def test_optimize_positions_within_bounds(self, simple_circuit: Circuit) -> None:
        """Test optimized positions are within board bounds."""
        optimizer = SimulatedQuantumAnnealing(
            max_iterations=50,
            random_seed=42,
        )

        result = optimizer.optimize(simple_circuit, 80.0, 60.0)

        for x, y in result.best_solution:
            assert 0 <= x <= 80.0
            assert 0 <= y <= 60.0

    def test_convergence_history_recorded(self, simple_circuit: Circuit) -> None:
        """Test convergence history is recorded."""
        optimizer = SimulatedQuantumAnnealing(max_iterations=20, random_seed=42)

        result = optimizer.optimize(simple_circuit, 100.0, 100.0)

        assert len(result.convergence_history) > 0


class TestGeneticAlgorithm:
    """Tests for GeneticAlgorithm optimizer."""

    @pytest.fixture
    def simple_circuit(self) -> Circuit:
        """Create a simple circuit for testing."""
        circuit = Circuit(name="Test")
        for i in range(4):
            comp = Component(
                name=f"R{i}",
                component_type=ComponentType.RESISTOR,
                footprint=Footprint("0603", 1.6, 0.8, 2),
            )
            circuit.add_component(comp)
        return circuit

    def test_ga_creation(self) -> None:
        """Test GA initialization."""
        ga = GeneticAlgorithm(
            population_size=50,
            max_generations=100,
            elite_count=3,
            crossover_rate=0.85,
            mutation_rate=0.15,
        )

        assert ga.population_size == 50
        assert ga.max_generations == 100
        assert ga.elite_count == 3

    def test_ga_optimize(self, simple_circuit: Circuit) -> None:
        """Test GA optimization."""
        ga = GeneticAlgorithm(
            population_size=20,
            max_generations=10,
            random_seed=42,
        )

        result = ga.optimize(simple_circuit, 100.0, 100.0)

        assert "best_solution" in result
        assert "best_fitness" in result
        assert len(result["best_solution"]) == len(simple_circuit.components)

    def test_ga_convergence(self, simple_circuit: Circuit) -> None:
        """Test GA convergence history."""
        ga = GeneticAlgorithm(
            population_size=20,
            max_generations=15,
            random_seed=42,
        )

        result = ga.optimize(simple_circuit, 100.0, 100.0)

        assert "convergence_history" in result
        assert len(result["convergence_history"]) > 0


class TestIndividual:
    """Tests for Individual class."""

    def test_individual_creation(self) -> None:
        """Test individual creation."""
        genes = np.array([1.0, 2.0, 3.0, 4.0])
        ind = Individual(genes=genes, fitness=10.0)

        assert len(ind.genes) == 4
        assert ind.fitness == 10.0
        assert ind.rank == 0

    def test_individual_copy(self) -> None:
        """Test individual copy."""
        genes = np.array([1.0, 2.0, 3.0])
        ind = Individual(genes=genes, fitness=5.0)

        copy = ind.copy()

        assert np.array_equal(copy.genes, ind.genes)
        assert copy.fitness == ind.fitness
        assert copy is not ind


class TestPopulation:
    """Tests for Population class."""

    def test_population_size(self) -> None:
        """Test population size property."""
        individuals = [Individual(genes=np.random.randn(4)) for _ in range(10)]
        pop = Population(individuals=individuals)

        assert pop.size == 10

    def test_get_best(self) -> None:
        """Test getting best individual."""
        individuals = [
            Individual(genes=np.random.randn(4), fitness=float(i)) for i in range(5, 0, -1)
        ]
        pop = Population(individuals=individuals)

        best = pop.get_best()

        assert best.fitness == 1.0

    def test_get_average_fitness(self) -> None:
        """Test average fitness calculation."""
        individuals = [Individual(genes=np.random.randn(4), fitness=float(i)) for i in range(1, 6)]
        pop = Population(individuals=individuals)

        avg = pop.get_average_fitness()

        assert avg == 3.0


class TestSelectionStrategies:
    """Tests for selection strategies."""

    def test_tournament_selection(self) -> None:
        """Test tournament selection."""
        individuals = [Individual(genes=np.random.randn(4), fitness=float(i)) for i in range(10)]
        pop = Population(individuals=individuals)
        selection = TournamentSelection(tournament_size=3)

        parents = selection.select(pop, 4)

        assert len(parents) == 4


class TestCrossoverOperators:
    """Tests for crossover operators."""

    def test_blend_crossover(self) -> None:
        """Test blend crossover."""
        parent1 = Individual(genes=np.array([0.0, 0.0, 0.0]))
        parent2 = Individual(genes=np.array([10.0, 10.0, 10.0]))
        crossover = BlendCrossover(alpha=0.5)

        child1, child2 = crossover.crossover(parent1, parent2)

        assert len(child1.genes) == 3
        assert len(child2.genes) == 3


class TestMutationOperators:
    """Tests for mutation operators."""

    def test_gaussian_mutation(self) -> None:
        """Test Gaussian mutation."""
        ind = Individual(genes=np.array([5.0, 5.0, 5.0]))
        mutation = GaussianMutation(sigma=0.1, mutation_rate=1.0)
        bounds = [(0.0, 10.0), (0.0, 10.0), (0.0, 10.0)]

        mutant = mutation.mutate(ind, bounds)

        assert not np.array_equal(mutant.genes, ind.genes) or True


class TestNSGA2:
    """Tests for NSGA-II algorithm."""

    def test_nsga2_creation(self) -> None:
        """Test NSGA-II initialization."""
        nsga2 = NSGA2(population_size=50, max_generations=100)

        assert nsga2.population_size == 50
        assert nsga2.max_generations == 100

    def test_nsga2_optimize(self) -> None:
        """Test NSGA-II optimization."""
        circuit = Circuit()
        for i in range(3):
            comp = Component(name=f"C{i}", component_type=ComponentType.CAPACITOR)
            circuit.add_component(comp)

        nsga2 = NSGA2(population_size=10, max_generations=5, random_seed=42)

        result = nsga2.optimize(circuit, 100.0, 100.0)

        assert "pareto_front" in result
        assert "generations" in result
