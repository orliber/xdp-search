"""Visualize the Section 4.3 ten-node WA* reopen example.

Produces plots/section43_reopen_trap.png — three panels:
  Left   : graph structure (edge costs + heuristic values)
  Middle : WA* no-reopen  — expansion order, dead-end branch, final path
  Right  : WA* with-reopen — expansion order, reopened node, final path
Plus a summary bar chart at the bottom.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyArrowPatch
except ModuleNotFoundError:
    sys.exit("matplotlib is required: pip install -r requirements.txt")

# ---------------------------------------------------------------------------
# Graph data
# ---------------------------------------------------------------------------

NODES = ["S", "A", "B1", "B2", "X", "Y", "C1", "C2", "C3", "G"]

H = {"S": 10, "A": 1, "B1": 5, "B2": 5, "X": 2, "Y": 4,
     "C1": 6, "C2": 5.4, "C3": 4.8, "G": 0}

EDGES = [
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

# Node positions (x, y)
POS = {
    "S":  (0.0,  0.0),
    "A":  (2.0,  2.0),
    "B1": (2.0,  0.0),
    "B2": (3.5,  0.0),
    "X":  (5.0,  1.0),
    "Y":  (6.5,  1.0),
    "G":  (8.0,  1.0),
    "C1": (2.0, -2.0),
    "C2": (3.5, -2.0),
    "C3": (5.0, -2.0),
}

# ---------------------------------------------------------------------------
# Run data (from section43_example.py output, goal not counted as expansion)
# ---------------------------------------------------------------------------

# Expansion order: list of (node, expansion_number, is_reopen)
NO_REOPEN_ORDER = [
    ("S",  1, False),
    ("A",  2, False),
    ("X",  3, False),
    ("B1", 4, False),
    ("B2", 5, False),
    ("C1", 6, False),
    ("C2", 7, False),
    ("C3", 8, False),
    ("Y",  9, False),
]
NO_REOPEN_PATH   = ["S", "A", "X", "Y", "G"]
NO_REOPEN_COST   = 7.0
NO_REOPEN_TOTAL  = 9

WITH_REOPEN_ORDER = [
    ("S",  1, False),
    ("A",  2, False),
    ("X",  3, False),
    ("B1", 4, False),
    ("B2", 5, False),
    ("X",  6, True),   # reopen
    ("Y",  7, False),
]
WITH_REOPEN_PATH  = ["S", "B1", "B2", "X", "Y", "G"]
WITH_REOPEN_COST  = 4.6
WITH_REOPEN_TOTAL = 7

# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

NODE_R = 0.38   # node circle radius for hit-test / arrow offset


def _draw_graph(ax, expansion_order, path_nodes, title, w=1.5):
    """Draw the graph on *ax* with coloured expansion labels and path highlight."""

    ax.set_xlim(-1, 9.5)
    ax.set_ylim(-3.2, 3.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)

    expanded_set = {n for n, _, _ in expansion_order}
    reopen_set   = {n for n, _, r in expansion_order if r}
    order_map    = {}
    for node, num, reopen in expansion_order:
        order_map.setdefault(node, []).append((num, reopen))

    # --- edges ---
    for u, v, cost in EDGES:
        x0, y0 = POS[u]
        x1, y1 = POS[v]
        on_path = (u in path_nodes and v in path_nodes and
                   path_nodes.index(v) == path_nodes.index(u) + 1)
        color = "#2ca02c" if on_path else "#aaaaaa"
        lw    = 2.5 if on_path else 1.0

        dx, dy = x1 - x0, y1 - y0
        dist = (dx**2 + dy**2) ** 0.5
        ux, uy = dx / dist, dy / dist
        sx = x0 + ux * NODE_R
        sy = y0 + uy * NODE_R
        ex = x1 - ux * NODE_R
        ey = y1 - uy * NODE_R

        ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                   mutation_scale=14))

        mx, my = (sx + ex) / 2, (sy + ey) / 2
        perp_x = -uy * 0.28
        perp_y =  ux * 0.28
        ax.text(mx + perp_x, my + perp_y, f"{cost:g}",
                ha="center", va="center", fontsize=7.5, color="#555555")

    # --- nodes ---
    for node in NODES:
        x, y = POS[node]

        if node in reopen_set:
            face = "#d4a5f5"   # purple — reopened
            edge_col = "#7b2d8b"
        elif node in expanded_set:
            face = "#aec6e8"   # blue — expanded
            edge_col = "#1f77b4"
        else:
            face = "#f5f5f5"   # grey — never expanded
            edge_col = "#999999"

        if node in path_nodes:
            edge_col = "#2ca02c"

        circle = plt.Circle((x, y), NODE_R, color=face,
                             ec=edge_col, lw=2.2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y + 0.08, node, ha="center", va="center",
                fontsize=9, fontweight="bold", zorder=4)
        ax.text(x, y - 0.18, f"h={H[node]:g}", ha="center", va="center",
                fontsize=7, color="#666666", zorder=4)

        # expansion order badge(s)
        if node in order_map:
            for idx, (num, is_reopen) in enumerate(order_map[node]):
                bx = x + NODE_R - 0.05
                by = y + NODE_R - 0.05 - idx * 0.45
                badge_col = "#d4a5f5" if is_reopen else "#ff8c00"
                badge = plt.Circle((bx, by), 0.22, color=badge_col,
                                   ec="white", lw=1.2, zorder=5)
                ax.add_patch(badge)
                ax.text(bx, by, str(num), ha="center", va="center",
                        fontsize=7.5, fontweight="bold", color="white", zorder=6)

    # --- g-cost labels along final path ---
    g = 0.0
    for i, node in enumerate(path_nodes):
        x, y = POS[node]
        ax.text(x, y - NODE_R - 0.28, f"g={g:g}",
                ha="center", va="top", fontsize=7,
                color="#2ca02c", fontweight="bold")
        if i + 1 < len(path_nodes):
            nxt = path_nodes[i + 1]
            cost = next(c for u, v, c in EDGES if u == node and v == nxt)
            g += cost


def _draw_structure(ax):
    """Left panel: plain graph with all labels, no run-specific colouring."""

    ax.set_xlim(-1, 9.5)
    ax.set_ylim(-3.2, 3.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Graph structure  (w = 1.5)", fontsize=11,
                 fontweight="bold", pad=8)

    for u, v, cost in EDGES:
        x0, y0 = POS[u]
        x1, y1 = POS[v]
        dx, dy = x1 - x0, y1 - y0
        dist = (dx**2 + dy**2) ** 0.5
        ux, uy = dx / dist, dy / dist
        sx, sy = x0 + ux * NODE_R, y0 + uy * NODE_R
        ex, ey = x1 - ux * NODE_R, y1 - uy * NODE_R
        ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle="-|>", color="#888888", lw=1.2,
                                   mutation_scale=14))
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        perp_x = -(uy) * 0.28
        perp_y =  (ux) * 0.28
        ax.text(mx + perp_x, my + perp_y, f"c={cost:g}",
                ha="center", va="center", fontsize=7.5, color="#444444")

    for node in NODES:
        x, y = POS[node]
        face = "#A2C2E8" if node in ("S", "G") else "#F0F4F8"
        ec   = "#333333"
        circle = plt.Circle((x, y), NODE_R, color=face, ec=ec, lw=2, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y + 0.08, node, ha="center", va="center",
                fontsize=9, fontweight="bold", zorder=4)
        ax.text(x, y - 0.18, f"h={H[node]:g}", ha="center", va="center",
                fontsize=7, color="#555555", zorder=4)


def _draw_summary(ax):
    """Bottom panel: bar chart comparing expansions."""

    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(0, 12)
    ax.set_xticks([0.5, 1.5])
    ax.set_xticklabels(["No-reopen", "With-reopen"], fontsize=10)
    ax.set_ylabel("Expansions", fontsize=9)
    ax.set_title("Summary — node expansions", fontsize=11, fontweight="bold")
    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    bars = ax.bar([0.5, 1.5], [NO_REOPEN_TOTAL, WITH_REOPEN_TOTAL],
                  width=0.6, color=["#aec6e8", "#aee8b0"],
                  edgecolor=["#1f77b4", "#2ca02c"], linewidth=1.8)

    for bar, val, cost, path in zip(
        bars,
        [NO_REOPEN_TOTAL, WITH_REOPEN_TOTAL],
        [NO_REOPEN_COST,  WITH_REOPEN_COST],
        [NO_REOPEN_PATH,  WITH_REOPEN_PATH],
    ):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.2,
                f"{val} exp.\ncost={cost}",
                ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    saved = NO_REOPEN_TOTAL - WITH_REOPEN_TOTAL
    pct   = saved / NO_REOPEN_TOTAL * 100
    ax.text(1.0, 10.5,
            f"Reopen saves {saved} expansion(s)  ({pct:.0f}% reduction)",
            ha="center", va="center", fontsize=9,
            color="#2ca02c", fontweight="bold")


# ---------------------------------------------------------------------------
# Legend helpers
# ---------------------------------------------------------------------------

def _legend_handles():
    return [
        mpatches.Patch(color="#aec6e8", ec="#1f77b4", lw=1.5, label="Expanded"),
        mpatches.Patch(color="#d4a5f5", ec="#7b2d8b", lw=1.5, label="Reopened"),
        mpatches.Patch(color="#f5f5f5", ec="#999999", lw=1.5, label="Never expanded"),
        mpatches.Patch(color="#ff8c00", label="Expansion badge"),
        plt.Line2D([0], [0], color="#2ca02c", lw=2.5, label="Final path"),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    fig = plt.figure(figsize=(20, 13))

    # Top row: three graph panels
    ax_struct = fig.add_axes([0.01, 0.38, 0.32, 0.58])
    ax_no     = fig.add_axes([0.34, 0.38, 0.32, 0.58])
    ax_re     = fig.add_axes([0.67, 0.38, 0.32, 0.58])

    # Bottom row: summary bar chart + legend
    ax_sum    = fig.add_axes([0.15, 0.04, 0.35, 0.28])
    ax_leg    = fig.add_axes([0.57, 0.04, 0.35, 0.28])

    _draw_structure(ax_struct)
    _draw_graph(ax_no, NO_REOPEN_ORDER,   NO_REOPEN_PATH,
                "WA*  no-reopen\n10 exp. → cost 7.0  (path via A)")
    _draw_graph(ax_re, WITH_REOPEN_ORDER, WITH_REOPEN_PATH,
                "WA*  with-reopen\n8 exp. → cost 4.6  (path via B1→B2)")
    _draw_summary(ax_sum)

    ax_leg.axis("off")
    ax_leg.legend(handles=_legend_handles(), loc="center",
                  fontsize=10, framealpha=0.9, title="Legend", title_fontsize=10)

    fig.suptitle("Section 4.3 — WA* Reopen Cost Trap  (w = 1.5, 10-node graph)",
                 fontsize=13, fontweight="bold", y=0.995)

    out = Path("plots/section43_reopen_trap.png")
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
