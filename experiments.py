"""Run weighted best-first search experiments and write CSV summaries."""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Union

from algorithms import PRIORITIES, best_first_search
from domains import FifteenPuzzle, Grid, make_grid_instances, random_puzzle


ALGORITHMS = ("weighted_astar", "xdp", "xup")

# Table 4 of Chen & Sturtevant (IJCAI 2019): puzzle experiments use w >= 1.5
# (XUP expands an impractical number of nodes on puzzles for smaller weights)
PUZZLE_WEIGHTS: Sequence[float] = (1.5, 2.0, 3.0, 10.0)

# Table 3 of Chen & Sturtevant (IJCAI 2019): grid experiments include w = 1.25
GRID_WEIGHTS: Sequence[float] = (1.25, 1.5, 2.0, 3.0, 10.0)

DENSITIES = (0.10, 0.20, 0.30, 0.40)
SEED = 42

# Safety cap: prevent runaway searches on unexpectedly hard instances
MAX_EXPANSIONS = 2_000_000


def run_all(
    output_dir: Path,
    seed: int = SEED,
    grid_width: int = 50,
    grid_height: int = 50,
    grid_instances: int = 50,
    puzzle_instances: int = 20,
    puzzle_scramble_moves: int = 200,
) -> List[Dict[str, object]]:
    """Run all requested algorithm, weight, and domain combinations."""

    output_dir.mkdir(parents=True, exist_ok=True)
    rows: List[Dict[str, object]] = []

    puzzle_rng = random.Random(seed)
    puzzles = [random_puzzle(puzzle_scramble_moves, puzzle_rng) for _ in range(puzzle_instances)]
    rows.extend(run_domain("15-puzzle", "all", puzzles, PUZZLE_WEIGHTS))

    grids_by_density = make_grid_instances(
        width=grid_width,
        height=grid_height,
        densities=DENSITIES,
        instances_per_density=grid_instances,
        seed=seed + 1,
    )
    for density, grids in grids_by_density.items():
        rows.extend(run_domain("grid", f"{density:.2f}", grids, GRID_WEIGHTS))

    summary_rows = summarize(rows)
    write_csv(output_dir / "results_raw.csv", rows)
    write_csv(output_dir / "results_summary.csv", summary_rows)
    print_tables(summary_rows)
    return summary_rows


def run_domain(
    domain: str,
    variant: str,
    problems: Iterable[Union[FifteenPuzzle, Grid]],
    weights: Sequence[float],
) -> List[Dict[str, object]]:
    """Run every algorithm and weight on a sequence of problem instances."""

    rows: List[Dict[str, object]] = []
    problem_list = list(problems)
    for algorithm in ALGORITHMS:
        for weight in weights:
            print(f"Running {domain} ({variant}) {algorithm} w={weight}", flush=True)
            for instance_id, problem in enumerate(problem_list):
                result = best_first_search(
                    problem=problem,
                    weight=weight,
                    priority_fn=PRIORITIES[algorithm],
                    algorithm=algorithm,
                    max_expansions=MAX_EXPANSIONS,
                )
                rows.append(
                    {
                        "domain": domain,
                        "variant": variant,
                        "instance": instance_id,
                        "algorithm": algorithm,
                        "weight": weight,
                        "found": result.found,
                        "expansions": result.expansions,
                        "runtime": result.runtime,
                        "solution_cost": result.cost if result.cost is not None else "",
                    }
                )
    return rows


def summarize(rows: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    """Average expansions, runtime, and solution cost by benchmark setting."""

    grouped: Dict[tuple, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = (row["domain"], row["variant"], row["algorithm"], row["weight"])
        grouped[key].append(row)

    summary = []
    for (domain, variant, algorithm, weight), group in sorted(grouped.items()):
        solved = [row for row in group if row["found"]]
        costs = [float(row["solution_cost"]) for row in solved]
        summary.append(
            {
                "domain": domain,
                "variant": variant,
                "algorithm": algorithm,
                "weight": weight,
                "instances": len(group),
                "solved": len(solved),
                "avg_expansions": mean(float(row["expansions"]) for row in group),
                "avg_runtime": mean(float(row["runtime"]) for row in group),
                "avg_solution_cost": mean(costs) if costs else "",
            }
        )
    return summary


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    """Write rows to CSV using the keys from the first row."""

    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def print_tables(rows: List[Dict[str, object]]) -> None:
    """Print compact tables grouped by domain and density/variant."""

    grouped: Dict[tuple, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(row["domain"], row["variant"])].append(row)

    for (domain, variant), group in sorted(grouped.items()):
        print(f"\n{domain} ({variant})")
        print("algorithm        w     avg expansions   avg runtime   avg cost   solved")
        print("-----------------------------------------------------------------------")
        for row in sorted(group, key=lambda item: (str(item["algorithm"]), float(item["weight"]))):
            cost = row["avg_solution_cost"]
            cost_text = f"{float(cost):8.2f}" if cost != "" else "      n/a"
            print(
                f"{str(row['algorithm']):15}"
                f"{float(row['weight']):4.1f}"
                f"{float(row['avg_expansions']):17.2f}"
                f"{float(row['avg_runtime']):14.5f}"
                f"{cost_text}"
                f"{int(row['solved']):5d}/{int(row['instances'])}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--grid-width", type=int, default=50)
    parser.add_argument("--grid-height", type=int, default=50)
    parser.add_argument("--grid-instances", type=int, default=50)
    parser.add_argument("--puzzle-instances", type=int, default=20)
    parser.add_argument("--puzzle-scramble-moves", type=int, default=200)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_all(
        output_dir=args.output_dir,
        seed=args.seed,
        grid_width=args.grid_width,
        grid_height=args.grid_height,
        grid_instances=args.grid_instances,
        puzzle_instances=args.puzzle_instances,
        puzzle_scramble_moves=args.puzzle_scramble_moves,
    )
