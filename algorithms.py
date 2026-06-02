"""Best-first search algorithms with shared search machinery."""

from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass
from typing import Callable, Dict, Generic, Iterable, List, Optional, Protocol, Tuple, TypeVar


State = TypeVar("State")


class SearchProblem(Protocol[State]):
    """Protocol implemented by searchable domains."""

    start: State
    goal: State

    def neighbors(self, state: State) -> Iterable[Tuple[State, float]]:
        """Return reachable neighbor states and their step costs."""

    def heuristic(self, state: State) -> float:
        """Estimate the remaining cost from state to the goal."""


@dataclass(frozen=True)
class SearchResult(Generic[State]):
    """Summary returned by every search algorithm."""

    algorithm: str
    weight: float
    allow_reopen: bool
    found: bool
    cost: Optional[float]
    expansions: int
    reopens: int      # how many closed nodes were reopened (always 0 when allow_reopen=False)
    runtime: float
    path: List[State]


def weighted_astar_priority(g: float, h: float, w: float) -> float:
    """Weighted A*: f = g + w * h."""

    return g + w * h


def xdp_priority(g: float, h: float, w: float) -> float:
    """XDP: Φ(h,g) = [g + (2w-1)h + sqrt((g-h)² + 4wgh)] / 2w  (eq. 9, Chen & Sturtevant IJCAI 2019)."""

    return (g + (2 * w - 1) * h + math.sqrt((h - g) ** 2 + 4 * w * g * h)) / (2 * w)


def xup_priority(g: float, h: float, w: float) -> float:
    """XUP: Φ(h,g) = [g + h + sqrt((g+h)² + 4w(w-1)h²)] / 2w  (eq. 11, Chen & Sturtevant IJCAI 2019)."""

    return (g + h + math.sqrt((g + h) ** 2 + 4 * w * (w - 1) * h**2)) / (2 * w)


PRIORITIES: Dict[str, Callable[[float, float, float], float]] = {
    "weighted_astar": weighted_astar_priority,
    "xdp": xdp_priority,
    "xup": xup_priority,
}


def best_first_search(
    problem: SearchProblem[State],
    weight: float,
    priority_fn: Callable[[float, float, float], float],
    algorithm: str,
    max_expansions: int = 10_000_000,
    allow_reopen: bool = False,
) -> SearchResult[State]:
    """Generic best-first search.

    When allow_reopen=False (default) implements Algorithm 1 of Chen & Sturtevant
    (IJCAI 2019): closed nodes are never revisited. XDP and XUP are proven
    (Theorem 9) to remain w-suboptimal under this policy.

    When allow_reopen=True, a closed node is removed from the closed set and
    re-queued whenever a shorter path to it is discovered.
    """

    started = time.perf_counter()
    counter = 0
    expansions = 0
    reopens = 0
    start = problem.start
    g_score: Dict[State, float] = {start: 0.0}
    parent: Dict[State, Optional[State]] = {start: None}
    open_heap: List[Tuple[float, float, int, State]] = []
    h0 = problem.heuristic(start)
    heapq.heappush(open_heap, (priority_fn(0.0, h0, weight), h0, counter, start))
    closed: set[State] = set()

    while open_heap:
        _, _, _, state = heapq.heappop(open_heap)
        if state in closed:
            continue

        if state == problem.goal:
            runtime = time.perf_counter() - started
            return SearchResult(
                algorithm=algorithm,
                weight=weight,
                allow_reopen=allow_reopen,
                found=True,
                cost=g_score[state],
                expansions=expansions,
                reopens=reopens,
                runtime=runtime,
                path=_reconstruct_path(parent, state),
            )

        closed.add(state)
        expansions += 1
        if expansions >= max_expansions:
            break
        current_g = g_score[state]

        for neighbor, step_cost in problem.neighbors(state):
            is_closed = neighbor in closed
            if is_closed and not allow_reopen:
                continue
            tentative_g = current_g + step_cost
            if tentative_g < g_score.get(neighbor, math.inf):
                if is_closed:  # allow_reopen is True here
                    closed.discard(neighbor)
                    reopens += 1
                g_score[neighbor] = tentative_g
                parent[neighbor] = state
                counter += 1
                h = problem.heuristic(neighbor)
                f = priority_fn(tentative_g, h, weight)
                heapq.heappush(open_heap, (f, h, counter, neighbor))

    runtime = time.perf_counter() - started
    return SearchResult(
        algorithm=algorithm,
        weight=weight,
        allow_reopen=allow_reopen,
        found=False,
        cost=None,
        expansions=expansions,
        reopens=reopens,
        runtime=runtime,
        path=[],
    )


def weighted_astar(problem: SearchProblem[State], weight: float) -> SearchResult[State]:
    """Run Weighted A*."""

    return best_first_search(problem, weight, weighted_astar_priority, "weighted_astar")


def xdp(problem: SearchProblem[State], weight: float) -> SearchResult[State]:
    """Run XDP search."""

    return best_first_search(problem, weight, xdp_priority, "xdp")


def xup(problem: SearchProblem[State], weight: float) -> SearchResult[State]:
    """Run XUP search."""

    return best_first_search(problem, weight, xup_priority, "xup")


def _reconstruct_path(parent: Dict[State, Optional[State]], state: State) -> List[State]:
    path = [state]
    while parent[state] is not None:
        state = parent[state]  # type: ignore[assignment]
        path.append(state)
    path.reverse()
    return path
