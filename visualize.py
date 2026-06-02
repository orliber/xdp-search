"""Create matplotlib plots from experiment summary CSV files."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def plot_summary(summary_csv: Path, output_dir: Path) -> List[Path]:
    """Plot weight versus average expansions for each domain/variant."""

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("matplotlib is required for plots. Install with: pip install -r requirements.txt") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_rows(summary_csv)
    grouped: Dict[tuple, List[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["domain"], row["variant"])].append(row)

    paths = []
    for (domain, variant), group in sorted(grouped.items()):
        fig, ax = plt.subplots(figsize=(7, 4.5))
        algorithms = sorted({row["algorithm"] for row in group})
        for algorithm in algorithms:
            series = sorted(
                [row for row in group if row["algorithm"] == algorithm],
                key=lambda row: float(row["weight"]),
            )
            ax.plot(
                [float(row["weight"]) for row in series],
                [float(row["avg_expansions"]) for row in series],
                marker="o",
                linewidth=2,
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

        filename = f"{domain}_{variant}_expansions.png".replace(" ", "_").replace(".", "_")
        path = output_dir / filename
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths.append(path)
        print(f"Wrote {path}")

    return paths


def read_rows(path: Path) -> List[dict]:
    """Read a CSV file into a list of dictionaries."""

    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-csv", type=Path, default=Path("results/results_summary.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("plots"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    plot_summary(args.summary_csv, args.output_dir)
