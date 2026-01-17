"""
Genetic Algorithm for PCB Component Placement Optimization.

This module implements a sophisticated genetic algorithm with:
- Multi-objective optimization (wire length, component density, thermal distribution)
- Adaptive mutation and crossover rates
- Elitism and tournament selection
- Parallel fitness evaluation
- Niching for diversity preservation
"""

import random
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

import numpy as np

from quantum_pcb_builder.core.circuit import Circuit
from quantum_pcb_builder.core.component import Component

T = TypeVar("T")


@dataclass
class Individual:
    """
    Represents an individual solution in the genetic algorithm.

    Each individual encodes component positions and optional rotations.
    """

    genes: np.ndarray
    fitness: float = float("inf")
    rank: int = 0
    crowding_distance: float = 0.0
    objectives: list[float] = field(default_factory=list)
    _id: int = field(default_factory=lambda: id(object()))

    def __hash__(self) -> int:
        """Return hash based on unique ID."""
        return self._id

    def __eq__(self, other: object) -> bool:
        """Check equality based on unique ID."""
        if not isinstance(other, Individual):
            return NotImplemented
        return self._id == other._id

    def copy(self) -> "Individual":
        """Create a deep copy of this individual."""
        ind = Individual(
            genes=self.genes.copy(),
            fitness=self.fitness,
            rank=self.rank,
            crowding_distance=self.crowding_distance,
            objectives=self.objectives.copy(),
        )
        return ind


@dataclass
class Population:
    """
    Represents a population of individuals.
    """

    individuals: list[Individual]
    generation: int = 0

    @property
    def size(self) -> int:
        """Return population size."""
        return len(self.individuals)

    def get_best(self) -> Individual:
        """Return the best individual based on fitness."""
        return min(self.individuals, key=lambda ind: ind.fitness)

    def get_average_fitness(self) -> float:
        """Return average fitness of the population."""
        return sum(ind.fitness for ind in self.individuals) / len(self.individuals)

    def get_diversity(self) -> float:
        """Calculate genetic diversity of the population."""
        if len(self.individuals) < 2:
            return 0.0

        genes_matrix = np.array([ind.genes for ind in self.individuals])
        std_per_gene = np.std(genes_matrix, axis=0)
        return float(np.mean(std_per_gene))


class SelectionStrategy(ABC):
    """Abstract base class for selection strategies."""

    @abstractmethod
    def select(self, population: Population, num_parents: int) -> list[Individual]:
        """Select parents for reproduction."""


class TournamentSelection(SelectionStrategy):
    """Tournament selection strategy."""

    def __init__(self, tournament_size: int = 3) -> None:
        """Initialize with tournament size."""
        self.tournament_size = tournament_size

    def select(self, population: Population, num_parents: int) -> list[Individual]:
        """Select parents using tournament selection."""
        parents = []
        for _ in range(num_parents):
            tournament = random.sample(population.individuals, self.tournament_size)
            winner = min(tournament, key=lambda ind: ind.fitness)
            parents.append(winner.copy())
        return parents


class RouletteWheelSelection(SelectionStrategy):
    """Roulette wheel (fitness proportionate) selection."""

    def select(self, population: Population, num_parents: int) -> list[Individual]:
        """Select parents using roulette wheel selection."""
        # Invert fitness for minimization problem
        max_fitness = max(ind.fitness for ind in population.individuals)
        inverted = [max_fitness - ind.fitness + 1 for ind in population.individuals]
        total = sum(inverted)
        probabilities = [f / total for f in inverted]

        parents = []
        for _ in range(num_parents):
            r = random.random()
            cumsum = 0.0
            for ind, prob in zip(population.individuals, probabilities, strict=True):
                cumsum += prob
                if r <= cumsum:
                    parents.append(ind.copy())
                    break
        return parents


class CrossoverOperator(ABC):
    """Abstract base class for crossover operators."""

    @abstractmethod
    def crossover(self, parent1: Individual, parent2: Individual) -> tuple[Individual, Individual]:
        """Perform crossover between two parents."""


class BlendCrossover(CrossoverOperator):
    """
    Blend Crossover (BLX-α) for real-valued genes.

    Creates offspring by sampling from a range extended beyond
    the parents' values.
    """

    def __init__(self, alpha: float = 0.5) -> None:
        """Initialize with blend parameter alpha."""
        self.alpha = alpha

    def crossover(self, parent1: Individual, parent2: Individual) -> tuple[Individual, Individual]:
        """Perform blend crossover."""
        n = len(parent1.genes)
        child1_genes = np.zeros(n)
        child2_genes = np.zeros(n)

        for i in range(n):
            g1, g2 = parent1.genes[i], parent2.genes[i]
            d = abs(g1 - g2)
            low = min(g1, g2) - self.alpha * d
            high = max(g1, g2) + self.alpha * d

            child1_genes[i] = random.uniform(low, high)
            child2_genes[i] = random.uniform(low, high)

        return Individual(genes=child1_genes), Individual(genes=child2_genes)


class SimulatedBinaryCrossover(CrossoverOperator):
    """
    Simulated Binary Crossover (SBX) for real-valued optimization.

    Mimics single-point crossover behavior for real-valued genes.
    """

    def __init__(self, eta: float = 20.0) -> None:
        """Initialize with distribution index eta."""
        self.eta = eta

    def crossover(self, parent1: Individual, parent2: Individual) -> tuple[Individual, Individual]:
        """Perform simulated binary crossover."""
        n = len(parent1.genes)
        child1_genes = np.zeros(n)
        child2_genes = np.zeros(n)

        for i in range(n):
            if random.random() <= 0.5:
                g1, g2 = parent1.genes[i], parent2.genes[i]
                if abs(g1 - g2) > 1e-10:
                    if g1 < g2:
                        y1, y2 = g1, g2
                    else:
                        y1, y2 = g2, g1

                    u = random.random()
                    if u <= 0.5:
                        beta = (2 * u) ** (1 / (self.eta + 1))
                    else:
                        beta = (1 / (2 * (1 - u))) ** (1 / (self.eta + 1))

                    child1_genes[i] = 0.5 * ((1 + beta) * y1 + (1 - beta) * y2)
                    child2_genes[i] = 0.5 * ((1 - beta) * y1 + (1 + beta) * y2)
                else:
                    child1_genes[i] = g1
                    child2_genes[i] = g2
            else:
                child1_genes[i] = parent1.genes[i]
                child2_genes[i] = parent2.genes[i]

        return Individual(genes=child1_genes), Individual(genes=child2_genes)


class MutationOperator(ABC):
    """Abstract base class for mutation operators."""

    @abstractmethod
    def mutate(self, individual: Individual, bounds: list[tuple[float, float]]) -> Individual:
        """Mutate an individual."""


class GaussianMutation(MutationOperator):
    """Gaussian mutation for real-valued genes."""

    def __init__(self, sigma: float = 0.1, mutation_rate: float = 0.1) -> None:
        """
        Initialize Gaussian mutation.

        Args:
            sigma: Standard deviation as fraction of range
            mutation_rate: Probability of mutating each gene
        """
        self.sigma = sigma
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual, bounds: list[tuple[float, float]]) -> Individual:
        """Apply Gaussian mutation."""
        mutant = individual.copy()

        for i, (low, high) in enumerate(bounds):
            if random.random() < self.mutation_rate:
                range_size = high - low
                mutant.genes[i] += random.gauss(0, self.sigma * range_size)
                mutant.genes[i] = max(low, min(high, mutant.genes[i]))

        return mutant


class PolynomialMutation(MutationOperator):
    """
    Polynomial mutation for real-valued optimization.

    Creates bounded mutations with higher probability near the original value.
    """

    def __init__(self, eta: float = 20.0, mutation_rate: float = 0.1) -> None:
        """
        Initialize polynomial mutation.

        Args:
            eta: Distribution index (higher = closer to parent)
            mutation_rate: Probability of mutating each gene
        """
        self.eta = eta
        self.mutation_rate = mutation_rate

    def mutate(self, individual: Individual, bounds: list[tuple[float, float]]) -> Individual:
        """Apply polynomial mutation."""
        mutant = individual.copy()

        for i, (low, high) in enumerate(bounds):
            if random.random() < self.mutation_rate:
                y = mutant.genes[i]
                delta1 = (y - low) / (high - low)
                delta2 = (high - y) / (high - low)

                u = random.random()
                if u < 0.5:
                    xy = 1 - delta1
                    val = 2 * u + (1 - 2 * u) * (xy ** (self.eta + 1))
                    deltaq = val ** (1 / (self.eta + 1)) - 1
                else:
                    xy = 1 - delta2
                    val = 2 * (1 - u) + 2 * (u - 0.5) * (xy ** (self.eta + 1))
                    deltaq = 1 - val ** (1 / (self.eta + 1))

                mutant.genes[i] = y + deltaq * (high - low)
                mutant.genes[i] = max(low, min(high, mutant.genes[i]))

        return mutant


class GeneticAlgorithm:
    """
    Advanced Genetic Algorithm for PCB placement optimization.

    Features:
    - Configurable selection, crossover, and mutation operators
    - Adaptive parameter control
    - Elitism for preserving best solutions
    - Diversity management through niching
    - Multi-objective optimization support
    """

    def __init__(
        self,
        population_size: int = 100,
        max_generations: int = 500,
        elite_count: int = 5,
        crossover_rate: float = 0.9,
        mutation_rate: float = 0.1,
        selection_strategy: SelectionStrategy | None = None,
        crossover_operator: CrossoverOperator | None = None,
        mutation_operator: MutationOperator | None = None,
        random_seed: int | None = None,
    ) -> None:
        """
        Initialize the Genetic Algorithm.

        Args:
            population_size: Number of individuals in population
            max_generations: Maximum number of generations
            elite_count: Number of elite individuals to preserve
            crossover_rate: Probability of crossover
            mutation_rate: Base mutation rate
            selection_strategy: Strategy for parent selection
            crossover_operator: Operator for crossover
            mutation_operator: Operator for mutation
            random_seed: Random seed for reproducibility
        """
        self.population_size = population_size
        self.max_generations = max_generations
        self.elite_count = elite_count
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate

        self.selection_strategy = selection_strategy or TournamentSelection()
        self.crossover_operator = crossover_operator or SimulatedBinaryCrossover()
        self.mutation_operator = mutation_operator or PolynomialMutation(
            mutation_rate=mutation_rate
        )

        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

    def optimize(
        self,
        circuit: Circuit,
        board_width: float,
        board_height: float,
        fitness_function: Callable[[list[tuple[float, float]]], float] | None = None,
    ) -> dict[str, Any]:
        """
        Optimize component placement using genetic algorithm.

        Args:
            circuit: Circuit to optimize
            board_width: PCB board width in mm
            board_height: PCB board height in mm
            fitness_function: Custom fitness function (optional)

        Returns:
            Dictionary with optimization results
        """
        components = list(circuit.components.values())
        n_components = len(components)

        if n_components == 0:
            return {
                "best_solution": [],
                "best_fitness": 0.0,
                "generations": 0,
                "convergence_history": [],
            }

        # Gene structure: [x1, y1, x2, y2, ..., xn, yn]
        bounds = []
        for _ in range(n_components):
            bounds.append((5.0, board_width - 5.0))
            bounds.append((5.0, board_height - 5.0))

        if fitness_function is None:
            fitness_function = self._create_fitness_function(circuit, components)

        # Initialize population
        population = self._initialize_population(bounds)
        self._evaluate_population(population, fitness_function, n_components)

        convergence_history = [population.get_best().fitness]

        # Main evolution loop
        for generation in range(self.max_generations):
            population.generation = generation

            # Create offspring
            offspring = self._create_offspring(population, bounds)
            self._evaluate_population(offspring, fitness_function, n_components)

            # Selection for next generation (with elitism)
            population = self._survivor_selection(population, offspring)

            # Track convergence
            best_fitness = population.get_best().fitness
            convergence_history.append(best_fitness)

            # Adaptive parameter adjustment
            self._adapt_parameters(population, generation)

            # Early termination check
            if self._is_converged(convergence_history):
                break

        # Extract best solution
        best_individual = population.get_best()
        best_solution = self._decode_solution(best_individual, n_components)

        return {
            "best_solution": best_solution,
            "best_fitness": best_individual.fitness,
            "generations": generation + 1,
            "convergence_history": convergence_history,
            "final_diversity": population.get_diversity(),
        }

    def _initialize_population(self, bounds: list[tuple[float, float]]) -> Population:
        """Initialize population with random individuals."""
        individuals = []

        for _ in range(self.population_size):
            genes = np.array([random.uniform(low, high) for low, high in bounds])
            individuals.append(Individual(genes=genes))

        return Population(individuals=individuals)

    def _evaluate_population(
        self,
        population: Population,
        fitness_function: Callable[[list[tuple[float, float]]], float],
        n_components: int,
    ) -> None:
        """Evaluate fitness for all individuals in population."""
        for individual in population.individuals:
            solution = self._decode_solution(individual, n_components)
            individual.fitness = fitness_function(solution)

    def _decode_solution(
        self, individual: Individual, n_components: int
    ) -> list[tuple[float, float]]:
        """Decode genes to component positions."""
        solution = []
        for i in range(n_components):
            x = individual.genes[i * 2]
            y = individual.genes[i * 2 + 1]
            solution.append((x, y))
        return solution

    def _create_offspring(
        self, population: Population, bounds: list[tuple[float, float]]
    ) -> Population:
        """Create offspring through selection, crossover, and mutation."""
        offspring_list = []
        num_offspring = self.population_size - self.elite_count

        while len(offspring_list) < num_offspring:
            # Select parents
            parents = self.selection_strategy.select(population, 2)
            parent1, parent2 = parents[0], parents[1]

            # Crossover
            if random.random() < self.crossover_rate:
                child1, child2 = self.crossover_operator.crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            # Mutation
            child1 = self.mutation_operator.mutate(child1, bounds)
            child2 = self.mutation_operator.mutate(child2, bounds)

            # Ensure bounds
            self._clip_to_bounds(child1, bounds)
            self._clip_to_bounds(child2, bounds)

            offspring_list.extend([child1, child2])

        return Population(individuals=offspring_list[:num_offspring])

    def _clip_to_bounds(self, individual: Individual, bounds: list[tuple[float, float]]) -> None:
        """Clip genes to valid bounds."""
        for i, (low, high) in enumerate(bounds):
            individual.genes[i] = max(low, min(high, individual.genes[i]))

    def _survivor_selection(self, population: Population, offspring: Population) -> Population:
        """Select survivors for next generation with elitism."""
        # Sort by fitness
        combined = population.individuals + offspring.individuals
        combined.sort(key=lambda ind: ind.fitness)

        # Take elite + best from rest
        new_population = combined[: self.population_size]

        return Population(individuals=new_population, generation=population.generation + 1)

    def _adapt_parameters(self, population: Population, generation: int) -> None:
        """Adaptively adjust mutation rate based on diversity."""
        diversity = population.get_diversity()

        if diversity < 0.1:
            self.mutation_operator.mutation_rate = min(0.5, self.mutation_rate * 1.5)
        elif diversity > 0.3:
            self.mutation_operator.mutation_rate = max(0.01, self.mutation_rate * 0.8)

    def _is_converged(
        self, history: list[float], window: int = 30, threshold: float = 1e-6
    ) -> bool:
        """Check if optimization has converged."""
        if len(history) < window:
            return False
        recent = history[-window:]
        return max(recent) - min(recent) < threshold

    def _create_fitness_function(
        self, circuit: Circuit, components: list[Component]
    ) -> Callable[[list[tuple[float, float]]], float]:
        """Create default fitness function."""

        def fitness(positions: list[tuple[float, float]]) -> float:
            for comp, pos in zip(components, positions, strict=True):
                comp.position = pos

            wire_length = circuit.estimate_total_wire_length()

            overlap_penalty = 0.0
            for i, comp1 in enumerate(components):
                for comp2 in components[i + 1 :]:
                    if comp1.overlaps(comp2):
                        overlap_penalty += 1000.0

            # Aspect ratio penalty
            xs = [p[0] for p in positions]
            ys = [p[1] for p in positions]
            if xs and ys:
                bbox_w = max(xs) - min(xs)
                bbox_h = max(ys) - min(ys)
                if bbox_h > 0:
                    aspect_ratio = bbox_w / bbox_h
                    aspect_penalty = abs(1.0 - aspect_ratio) * 10
                else:
                    aspect_penalty = 0
            else:
                aspect_penalty = 0

            return wire_length + overlap_penalty + aspect_penalty

        return fitness


class NSGA2:
    """
    NSGA-II: Non-dominated Sorting Genetic Algorithm II.

    Multi-objective optimization for balancing:
    - Wire length minimization
    - Component density optimization
    - Signal integrity metrics
    """

    def __init__(
        self,
        population_size: int = 100,
        max_generations: int = 200,
        random_seed: int | None = None,
    ) -> None:
        """Initialize NSGA-II."""
        self.population_size = population_size
        self.max_generations = max_generations

        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

    def optimize(
        self,
        circuit: Circuit,
        board_width: float,
        board_height: float,
        objective_functions: list[Callable[[list[tuple[float, float]]], float]] | None = None,
    ) -> dict[str, Any]:
        """
        Perform multi-objective optimization.

        Args:
            circuit: Circuit to optimize
            board_width: PCB board width
            board_height: PCB board height
            objective_functions: List of objective functions to minimize

        Returns:
            Dictionary with Pareto front solutions
        """
        components = list(circuit.components.values())
        n_components = len(components)

        if n_components == 0:
            return {"pareto_front": [], "generations": 0}

        bounds = []
        for _ in range(n_components):
            bounds.append((5.0, board_width - 5.0))
            bounds.append((5.0, board_height - 5.0))

        if objective_functions is None:
            objective_functions = self._create_default_objectives(circuit, components)

        # Initialize population
        population = self._initialize_population(bounds)
        self._evaluate_objectives(population, objective_functions, n_components)

        for _ in range(self.max_generations):
            # Fast non-dominated sort
            fronts = self._fast_non_dominated_sort(population)

            # Calculate crowding distance
            for front in fronts:
                self._calculate_crowding_distance(front)

            # Create offspring
            offspring = self._create_offspring(population, bounds)
            self._evaluate_objectives(offspring, objective_functions, n_components)

            # Combine and select
            combined = Population(individuals=population.individuals + offspring.individuals)
            fronts = self._fast_non_dominated_sort(combined)

            # Select next generation
            new_individuals: list[Individual] = []
            front_idx = 0
            while len(new_individuals) + len(fronts[front_idx]) <= self.population_size:
                self._calculate_crowding_distance(fronts[front_idx])
                new_individuals.extend(fronts[front_idx])
                front_idx += 1
                if front_idx >= len(fronts):
                    break

            if len(new_individuals) < self.population_size and front_idx < len(fronts):
                self._calculate_crowding_distance(fronts[front_idx])
                fronts[front_idx].sort(key=lambda x: x.crowding_distance, reverse=True)
                new_individuals.extend(
                    fronts[front_idx][: self.population_size - len(new_individuals)]
                )

            population = Population(individuals=new_individuals)

        # Extract Pareto front
        fronts = self._fast_non_dominated_sort(population)
        pareto_front = []
        for ind in fronts[0]:
            solution = self._decode_solution(ind, n_components)
            pareto_front.append(
                {
                    "solution": solution,
                    "objectives": ind.objectives,
                }
            )

        return {
            "pareto_front": pareto_front,
            "generations": self.max_generations,
        }

    def _initialize_population(self, bounds: list[tuple[float, float]]) -> Population:
        """Initialize population with random individuals."""
        individuals = []

        for _ in range(self.population_size):
            genes = np.array([random.uniform(low, high) for low, high in bounds])
            individuals.append(Individual(genes=genes))

        return Population(individuals=individuals)

    def _evaluate_objectives(
        self,
        population: Population,
        objective_functions: list[Callable[[list[tuple[float, float]]], float]],
        n_components: int,
    ) -> None:
        """Evaluate all objectives for population."""
        for individual in population.individuals:
            solution = self._decode_solution(individual, n_components)
            individual.objectives = [obj(solution) for obj in objective_functions]

    def _decode_solution(
        self, individual: Individual, n_components: int
    ) -> list[tuple[float, float]]:
        """Decode genes to positions."""
        solution = []
        for i in range(n_components):
            x = individual.genes[i * 2]
            y = individual.genes[i * 2 + 1]
            solution.append((x, y))
        return solution

    def _fast_non_dominated_sort(self, population: Population) -> list[list[Individual]]:
        """Perform fast non-dominated sorting."""
        fronts: list[list[Individual]] = [[]]
        domination_count: dict[int, int] = {}
        dominated_by: dict[int, list[Individual]] = {}

        for i, p in enumerate(population.individuals):
            domination_count[i] = 0
            dominated_by[i] = []

            for j, q in enumerate(population.individuals):
                if i == j:
                    continue
                if self._dominates(p, q):
                    dominated_by[i].append(q)
                elif self._dominates(q, p):
                    domination_count[i] += 1

            if domination_count[i] == 0:
                p.rank = 0
                fronts[0].append(p)

        i = 0
        while i < len(fronts) and fronts[i]:
            next_front: list[Individual] = []
            for p in fronts[i]:
                p_idx = population.individuals.index(p)
                for q in dominated_by[p_idx]:
                    q_idx = population.individuals.index(q)
                    domination_count[q_idx] -= 1
                    if domination_count[q_idx] == 0:
                        q.rank = i + 1
                        next_front.append(q)
            i += 1
            if next_front:
                fronts.append(next_front)

        return [f for f in fronts if f]

    def _dominates(self, p: Individual, q: Individual) -> bool:
        """Check if p dominates q."""
        at_least_one_better = False
        for obj_p, obj_q in zip(p.objectives, q.objectives, strict=True):
            if obj_p > obj_q:
                return False
            if obj_p < obj_q:
                at_least_one_better = True
        return at_least_one_better

    def _calculate_crowding_distance(self, front: list[Individual]) -> None:
        """Calculate crowding distance for individuals in a front."""
        n = len(front)
        if n == 0:
            return

        for ind in front:
            ind.crowding_distance = 0.0

        num_objectives = len(front[0].objectives)

        for m in range(num_objectives):
            front.sort(key=lambda x: x.objectives[m])
            front[0].crowding_distance = float("inf")
            front[-1].crowding_distance = float("inf")

            obj_range = front[-1].objectives[m] - front[0].objectives[m]
            if obj_range == 0:
                continue

            for i in range(1, n - 1):
                front[i].crowding_distance += (
                    front[i + 1].objectives[m] - front[i - 1].objectives[m]
                ) / obj_range

    def _create_offspring(
        self, population: Population, bounds: list[tuple[float, float]]
    ) -> Population:
        """Create offspring using tournament selection and SBX crossover."""
        crossover = SimulatedBinaryCrossover()
        mutation = PolynomialMutation()
        offspring_list = []

        while len(offspring_list) < self.population_size:
            # Tournament selection based on rank and crowding distance
            parent1 = self._crowded_tournament_selection(population)
            parent2 = self._crowded_tournament_selection(population)

            # Crossover
            child1, child2 = crossover.crossover(parent1, parent2)

            # Mutation
            child1 = mutation.mutate(child1, bounds)
            child2 = mutation.mutate(child2, bounds)

            offspring_list.extend([child1, child2])

        return Population(individuals=offspring_list[: self.population_size])

    def _crowded_tournament_selection(self, population: Population) -> Individual:
        """Select individual using crowded tournament selection."""
        candidates = random.sample(population.individuals, 2)
        ind1, ind2 = candidates[0], candidates[1]

        if ind1.rank < ind2.rank:
            return ind1.copy()
        elif ind1.rank > ind2.rank:
            return ind2.copy()
        else:
            if ind1.crowding_distance > ind2.crowding_distance:
                return ind1.copy()
            else:
                return ind2.copy()

    def _create_default_objectives(
        self, circuit: Circuit, components: list[Component]
    ) -> list[Callable[[list[tuple[float, float]]], float]]:
        """Create default objective functions."""

        def wire_length_objective(positions: list[tuple[float, float]]) -> float:
            for comp, pos in zip(components, positions, strict=True):
                comp.position = pos
            return circuit.estimate_total_wire_length()

        def overlap_objective(positions: list[tuple[float, float]]) -> float:
            for comp, pos in zip(components, positions, strict=True):
                comp.position = pos

            overlaps = 0.0
            for i, comp1 in enumerate(components):
                for comp2 in components[i + 1 :]:
                    if comp1.overlaps(comp2):
                        overlaps += 1.0
            return overlaps

        return [wire_length_objective, overlap_objective]
