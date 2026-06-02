"""Create matplotlib plots from experiment summary CSV files."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


# Consistent colors per algorithm across all plots
ALGO_COLORS = {"weighted_astar": "#1f77b4", "xdp": "#ff7f0e", "xup": "#2ca02c"}


def plot_summary(summary_csv: Path, output_dir: Path) -> List[Path]:
    """Plot weight versus average expansions for each domain/variant."""

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("matplotlib is required. Install with: pip install -r requirements.txt") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_rows(summary_csv)
    grouped: Dict[tuple, List[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["domain"], row["variant"])].append(row)

    paths = []
    for (domain, variant), group in sorted(grouped.items()):
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for algorithm in sorted({row["algorithm"] for row in group}):
            series = sorted(
                [row for row in group if row["algorithm"] == algorithm],
                key=lambda row: float(row["weight"]),
            )
            ax.plot(
                [float(row["weight"]) for row in series],
                [float(row["avg_expansions"]) for row in series],
                marker="o",
                linewidth=2,
                color=ALGO_COLORS.get(algorithm),
                label=algorithm,
            )

        title = domain if variant == "all" else f"{domain} density {variant}"
        ax.set_title(title)
        ax.set_xlabel("Weight w")
        ax.set_ylabel("Average expansions")
        ax.set_xticks(sorted({float(row["weight"]) for row in group}))
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()

        stem = f"{domain}_{variant}_expansions".replace(" ", "_").replace(".", "_")
        path = output_dir / f"{stem}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths.append(path)
        print(f"Wrote {path}")

    return paths


def plot_reopen_comparison(reopen_csv: Path, output_dir: Path) -> List[Path]:
    """Plot no-reopen vs with-reopen expansions to validate Theorem 9.

    For each domain/variant we draw one subplot per algorithm.
    The solid line is no-reopen; the dashed line is with-reopen.
    Overlapping lines confirm that reopening never changes the result,
    which is the empirical validation of Theorem 9 (Chen & Sturtevant, IJCAI 2019).
    """

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("matplotlib is required. Install with: pip install -r requirements.txt") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_rows(reopen_csv)

    grouped: Dict[tuple, List[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["domain"], row["variant"])].append(row)

    paths = []
    for (domain, variant), group in sorted(grouped.items()):
        algorithms = sorted({row["algorithm"] for row in group})
        fig, axes = plt.subplots(1, len(algorithms), figsize=(5 * len(algorithms), 4.5), sharey=False)
        if len(algorithms) == 1:
            axes = [axes]

        for ax, algorithm in zip(axes, algorithms):
            color = ALGO_COLORS.get(algorithm, "black")
            for allow_reopen, linestyle, label_suffix in (
                ("False", "-",  " (no reopen)"),
                ("True",  "--", " (with reopen)"),
            ):
                series = sorted(
                    [
                        row for row in group
                        if row["algorithm"] == algorithm and row["allow_reopen"] == allow_reopen
                    ],
                    key=lambda row: float(row["weight"]),
                )
                if not series:
                    continue
                ax.plot(
                    [float(row["weight"]) for row in series],
                    [float(row["avg_expansions"]) for row in series],
                    marker="o",
                    linewidth=2,
                    linestyle=linestyle,
                    color=color,
                    label=algorithm + label_suffix,
                )

            ax.set_title(algorithm)
            ax.set_xlabel("Weight w")
            ax.set_ylabel("Average expansions")
            ax.set_xticks(sorted({float(row["weight"]) for row in group if row["algorithm"] == algorithm}))
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8)

        title = domain if variant == "all" else f"{domain} density {variant}"
        fig.suptitle(f"{title} — reopen vs no-reopen", fontsize=12)
        fig.tight_layout()

        stem = f"reopen_{domain}_{variant}".replace(" ", "_").replace(".", "_")
        path = output_dir / f"{stem}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths.append(path)
        print(f"Wrote {path}")

    return paths


def _read_rows(path: Path) -> List[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-csv", type=Path, default=Path("results/results_summary.csv"))
    parser.add_argument("--reopen-csv", type=Path, default=Path("results/results_reopen_summary.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("plots"))
    parser.add_argument(
        "--reopen-comparison",
        action="store_true",
        help="Plot the reopen comparison instead of the main summary.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.reopen_comparison:
        plot_reopen_comparison(args.reopen_csv, args.output_dir)
    else:
        plot_summary(args.summary_csv, args.output_dir)
