"""Section 4.3 — ten-node graph demonstrating the WA* reopen cost trap.

Graph from the report:
  Nodes : S, A, B1, B2, X, Y, C1, C2, C3, G
  Weight: w = 1.5

Expected results (goal node is checked but not counted as an expansion)
  allow_reopen=False :  9 expansions, cost 7.0   (path S→A→X→Y→G)
  allow_reopen=True  :  7 expansions, cost 4.6   (path S→B1→B2→X→Y→G)

Note: the report (section 4.3) counts the goal expansion too (+1 each),
giving 10 vs 8 — the 2-expansion saving and 22% reduction are identical.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from algorithms import SearchResult, best_first_search, weighted_astar_priority


_H = {
    "S":  10.0,
    "A":   1.0,
    "B1":  5.0,
    "B2":  5.0,
    "X":   2.0,
    "Y":   4.0,
    "C1":  6.0,
    "C2":  5.4,
    "C3":  4.8,
    "G":   0.0,
}

_EDGES: List[Tuple[str, str, float]] = [
    ("S",  "A",  1.0),
    ("A",  "X",  4.0),
    ("S",  "B1", 2.0),
    ("B1", "B2", 0.5),
    ("B2", "X",  0.1),
    ("X",  "Y",  1.0),
    ("Y",  "G",  1.0),
    ("S",  "C1", 2.0),
    ("C1", "C2", 1.0),
    ("C2", "C3", 1.0),
]


class TenNodeGraph:
    start = "S"
    goal  = "G"

    def __init__(self) -> None:
        self._adj: dict[str, list[tuple[str, float]]] = {}
        for u, v, c in _EDGES:
            self._adj.setdefault(u, []).append((v, c))

    def neighbors(self, state: str) -> Iterable[Tuple[str, float]]:
        return self._adj.get(state, [])

    def heuristic(self, state: str) -> float:
        return _H[state]


def _fmt(r: SearchResult) -> str:
    policy = "reopen " if r.allow_reopen else "no-reopen"
    path   = " → ".join(str(n) for n in r.path)
    return (
        f"  [{policy}]  expansions={r.expansions:2d}  "
        f"cost={r.cost}  reopens={r.reopens}  path: {path}"
    )


def main() -> None:
    problem = TenNodeGraph()
    w = 1.5

    no_reopen = best_first_search(
        problem, w, weighted_astar_priority, "WA*", allow_reopen=False
    )
    with_reopen = best_first_search(
        problem, w, weighted_astar_priority, "WA*", allow_reopen=True
    )

    print(f"Section 4.3 — WA* w={w} on 10-node graph\n")
    print(_fmt(no_reopen))
    print(_fmt(with_reopen))
    print()
    saved = no_reopen.expansions - with_reopen.expansions
    print(f"  reopen saved {saved} expansion(s) "
          f"({saved / no_reopen.expansions * 100:.0f}% reduction)")


if __name__ == "__main__":
    main()
