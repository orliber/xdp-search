"""Search domains for the XDP/XUP experiments."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple


PuzzleState = Tuple[int, ...]
GridPoint = Tuple[int, int]
GOAL_15: PuzzleState = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0)


@dataclass(frozen=True)
class FifteenPuzzle:
    """A 4x4 sliding-tile puzzle using Manhattan Distance."""

    start: PuzzleState
    goal: PuzzleState = GOAL_15
    size: int = 4

    def neighbors(self, state: PuzzleState) -> Iterable[Tuple[PuzzleState, float]]:
        blank = state.index(0)
        row, col = divmod(blank, self.size)
        moves = ((-1, 0), (1, 0), (0, -1), (0, 1))

        for dr, dc in moves:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                swap = nr * self.size + nc
                next_state = list(state)
                next_state[blank], next_state[swap] = next_state[swap], next_state[blank]
                yield tuple(next_state), 1.0

    def heuristic(self, state: PuzzleState) -> float:
        total = 0
        for index, tile in enumerate(state):
            if tile == 0:
                continue
            current_row, current_col = divmod(index, self.size)
            goal_row, goal_col = divmod(tile - 1, self.size)
            total += abs(current_row - goal_row) + abs(current_col - goal_col)
        return float(total)


@dataclass(frozen=True)
class Grid:
    """Four-connected grid pathfinding with blocked cells and Manhattan Distance."""

    width: int
    height: int
    obstacles: frozenset[GridPoint]
    start: GridPoint = (0, 0)

    @property
    def goal(self) -> GridPoint:
        return (self.width - 1, self.height - 1)

    def neighbors(self, state: GridPoint) -> Iterable[Tuple[GridPoint, float]]:
        row, col = state
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            point = (nr, nc)
            if 0 <= nr < self.height and 0 <= nc < self.width and point not in self.obstacles:
                yield point, 1.0

    def heuristic(self, state: GridPoint) -> float:
        goal_row, goal_col = self.goal
        row, col = state
        return float(abs(row - goal_row) + abs(col - goal_col))


def random_puzzle(scramble_moves: int, rng: random.Random) -> FifteenPuzzle:
    """Create a reproducible solvable 15-puzzle by scrambling from the goal."""

    state = GOAL_15
    previous: Optional[PuzzleState] = None
    puzzle = FifteenPuzzle(start=state)

    for _ in range(scramble_moves):
        candidates = [neighbor for neighbor, _ in puzzle.neighbors(state) if neighbor != previous]
        previous = state
        state = rng.choice(candidates)

    return FifteenPuzzle(start=state)


def random_grid(
    width: int,
    height: int,
    density: float,
    rng: random.Random,
    require_solvable: bool = True,
) -> Grid:
    """Generate a random grid, optionally retrying until start can reach goal."""

    while True:
        obstacles = set()
        for row in range(height):
            for col in range(width):
                point = (row, col)
                if point in ((0, 0), (height - 1, width - 1)):
                    continue
                if rng.random() < density:
                    obstacles.add(point)

        grid = Grid(width=width, height=height, obstacles=frozenset(obstacles))
        if not require_solvable or grid_is_solvable(grid):
            return grid


def grid_is_solvable(grid: Grid) -> bool:
    """Check grid connectivity with a lightweight breadth-first search."""

    frontier: List[GridPoint] = [grid.start]
    seen = {grid.start}
    index = 0

    while index < len(frontier):
        state = frontier[index]
        index += 1
        if state == grid.goal:
            return True
        for neighbor, _ in grid.neighbors(state):
            if neighbor not in seen:
                seen.add(neighbor)
                frontier.append(neighbor)
    return False


def make_grid_instances(
    width: int,
    height: int,
    densities: Sequence[float],
    instances_per_density: int,
    seed: int,
) -> dict[float, List[Grid]]:
    """Build reproducible grid benchmark instances for each obstacle density."""

    rng = random.Random(seed)
    return {
        density: [
            random_grid(width=width, height=height, density=density, rng=rng)
            for _ in range(instances_per_density)
        ]
        for density in densities
    }
