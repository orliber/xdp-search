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


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

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
    rows.extend(_run_domain("15-puzzle", "all", puzzles, PUZZLE_WEIGHTS))

    grids_by_density = make_grid_instances(
        width=grid_width,
        height=grid_height,
        densities=DENSITIES,
        instances_per_density=grid_instances,
        seed=seed + 1,
    )
    for density, grids in grids_by_density.items():
        rows.extend(_run_domain("grid", f"{density:.2f}", grids, GRID_WEIGHTS))

    summary_rows = _summarize(rows)
    _write_csv(output_dir / "results_raw.csv", rows)
    _write_csv(output_dir / "results_summary.csv", summary_rows)
    _print_tables(summary_rows)
    return summary_rows


def _run_domain(
    domain: str,
    variant: str,
    problems: Iterable[Union[FifteenPuzzle, Grid]],
    weights: Sequence[float],
    allow_reopen: bool = False,
) -> List[Dict[str, object]]:
    """Run every algorithm and weight on a sequence of problem instances."""

    rows: List[Dict[str, object]] = []
    problem_list = list(problems)
    for algorithm in ALGORITHMS:
        for weight in weights:
            print(f"  {domain} ({variant}) {algorithm} w={weight}", flush=True)
            for instance_id, problem in enumerate(problem_list):
                result = best_first_search(
                    problem=problem,
                    weight=weight,
                    priority_fn=PRIORITIES[algorithm],
                    algorithm=algorithm,
                    max_expansions=MAX_EXPANSIONS,
                    allow_reopen=allow_reopen,
                )
                rows.append(
                    {
                        "domain": domain,
                        "variant": variant,
                        "instance": instance_id,
                        "algorithm": algorithm,
                        "weight": weight,
                        "allow_reopen": allow_reopen,
                        "found": result.found,
                        "expansions": result.expansions,
                        "reopens": result.reopens,
                        "runtime": result.runtime,
                        "solution_cost": result.cost if result.cost is not None else "",
                    }
                )
    return rows


# ---------------------------------------------------------------------------
# Reopen comparison experiment (Part 2 contribution)
# ---------------------------------------------------------------------------

def run_reopen_comparison(
    output_dir: Path,
    seed: int = SEED,
    grid_width: int = 50,
    grid_height: int = 50,
    grid_instances: int = 20,
    puzzle_instances: int = 10,
    puzzle_scramble_moves: int = 200,
) -> List[Dict[str, object]]:
    """Compare with-reopen vs no-reopen to validate Theorem 9 of Chen & Sturtevant (IJCAI 2019).

    For every (domain, algorithm, weight) pair we run the search twice:
    once allowing the algorithm to reopen closed nodes, once forbidding it.
    If the results are identical and the reopen count is zero, that confirms
    the theorem: a consistent heuristic makes reopening unnecessary for all
    three priority functions.
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    puzzle_rng = random.Random(seed)
    puzzles = [random_puzzle(puzzle_scramble_moves, puzzle_rng) for _ in range(puzzle_instances)]
    grids_by_density = make_grid_instances(
        width=grid_width, height=grid_height,
        densities=DENSITIES, instances_per_density=grid_instances,
        seed=seed + 1,
    )

    domain_specs = [("15-puzzle", "all", puzzles, PUZZLE_WEIGHTS)]
    for density, grids in grids_by_density.items():
        domain_specs.append(("grid", f"{density:.2f}", grids, GRID_WEIGHTS))

    all_rows: List[Dict[str, object]] = []
    for domain, variant, problems, weights in domain_specs:
        for allow_reopen in (False, True):
            label = "with_reopen" if allow_reopen else "no_reopen"
            print(f"[{label}]", flush=True)
            all_rows.extend(_run_domain(domain, variant, problems, weights, allow_reopen=allow_reopen))

    _write_csv(output_dir / "results_reopen_raw.csv", all_rows)

    summary = _summarize_reopen(all_rows)
    _write_csv(output_dir / "results_reopen_summary.csv", summary)
    _print_reopen_table(summary)
    return summary


def _summarize_reopen(rows: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    """Produce one summary row per (domain, variant, algorithm, weight, allow_reopen)."""

    grouped: Dict[tuple, List[Dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = (row["domain"], row["variant"], row["algorithm"], row["weight"], row["allow_reopen"])
        grouped[key].append(row)

    summary = []
    for (domain, variant, algorithm, weight, allow_reopen), group in sorted(grouped.items()):
        solved = [r for r in group if r["found"]]
        costs = [float(r["solution_cost"]) for r in solved if r["solution_cost"] != ""]
        summary.append(
            {
                "domain": domain,
                "variant": variant,
                "algorithm": algorithm,
                "weight": weight,
                "allow_reopen": allow_reopen,
                "instances": len(group),
                "solved": len(solved),
                "avg_expansions": mean(float(r["expansions"]) for r in group),
                "total_reopens": sum(int(r["reopens"]) for r in group),
                "avg_cost": mean(costs) if costs else "",
            }
        )
    return summary


def _print_reopen_table(rows: List[Dict[str, object]]) -> None:
    """Print a side-by-side comparison of no-reopen vs with-reopen results."""

    idx: Dict[tuple, Dict[str, object]] = {}
    for row in rows:
        key = (row["domain"], row["variant"], row["algorithm"], row["weight"], row["allow_reopen"])
        idx[key] = row

    # Unique (domain, variant, algorithm, weight) combos — no allow_reopen in key
    unique = sorted({
        (str(d), str(v), str(a), float(w))
        for d, v, a, w, _ in idx
    })

    current_group: tuple = ()
    for (domain, variant, algorithm, weight) in unique:
        group_key = (domain, variant)
        if group_key != current_group:
            current_group = group_key
            print(f"\n{domain} ({variant})")
            print(f"{'algorithm':15} {'w':>5}  {'no-reopen exp':>15} {'reopen exp':>12} "
                  f"{'reopens':>8}  {'no-r cost':>10}  {'r cost':>8}  match")
            print("-" * 85)

        no_r = idx.get((domain, variant, algorithm, weight, False))
        wi_r = idx.get((domain, variant, algorithm, weight, True))
        if no_r is None or wi_r is None:
            continue
        exp_no = float(no_r["avg_expansions"])
        exp_wi = float(wi_r["avg_expansions"])
        total_reopens = int(wi_r["total_reopens"])
        cost_no = no_r["avg_cost"]
        cost_wi = wi_r["avg_cost"]
        cost_no_s = f"{float(cost_no):10.2f}" if cost_no != "" else "       n/a"
        cost_wi_s = f"{float(cost_wi):8.2f}" if cost_wi != "" else "     n/a"
        match = "✓" if abs(exp_no - exp_wi) < 0.01 and total_reopens == 0 else "✗"
        print(
            f"{algorithm:15} {weight:5.2f}"
            f"  {exp_no:15.2f} {exp_wi:12.2f} {total_reopens:8d}"
            f"  {cost_no_s}  {cost_wi_s}  {match}"
        )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _summarize(rows: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
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


def _write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    """Write rows to CSV using the keys from the first row."""

    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _print_tables(rows: List[Dict[str, object]]) -> None:
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--grid-width", type=int, default=50)
    parser.add_argument("--grid-height", type=int, default=50)
    parser.add_argument("--grid-instances", type=int, default=50)
    parser.add_argument("--puzzle-instances", type=int, default=20)
    parser.add_argument("--puzzle-scramble-moves", type=int, default=200)
    parser.add_argument(
        "--reopen-comparison",
        action="store_true",
        help="Run the with-reopen vs no-reopen comparison experiment instead of the main experiment.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    shared = dict(
        output_dir=args.output_dir,
        seed=args.seed,
        grid_width=args.grid_width,
        grid_height=args.grid_height,
        puzzle_scramble_moves=args.puzzle_scramble_moves,
    )
    if args.reopen_comparison:
        run_reopen_comparison(
            **shared,
            grid_instances=min(args.grid_instances, 20),
            puzzle_instances=min(args.puzzle_instances, 10),
        )
    else:
        run_all(**shared, grid_instances=args.grid_instances, puzzle_instances=args.puzzle_instances)
