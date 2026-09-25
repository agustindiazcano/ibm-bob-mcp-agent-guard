"""
Generate docs/img/results-en-{light,dark}.png from the numbers in AGENTS.md §7.

Requires the optional `docs` extra: pip install -e ".[docs]"

These numbers are not computed here — they are copied from the last real
measurement recorded in AGENTS.md §7 (own AST mutation engine, demo-repo).
Whenever those numbers change, update BEFORE/AFTER below in the same change,
the same way README.md's table gets updated (AGENTS.md §11).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

BEFORE = {"Coverage": 65.1, "Mutation score": 20.25}
AFTER = {"Coverage": 100.0, "Mutation score": 89.87}

OUT_DIR = Path(__file__).parent / "img"


def _render(theme: str, out_path: Path) -> None:
    dark = theme == "dark"
    fg = "#e2e8f0" if dark else "#1e293b"
    bg = "#0f172a" if dark else "#ffffff"
    grid = "#334155" if dark else "#e2e8f0"
    before_color = "#64748b"
    after_color = "#34d399"

    metrics = list(BEFORE.keys())
    before_vals = [BEFORE[m] for m in metrics]
    after_vals = [AFTER[m] for m in metrics]

    fig, ax = plt.subplots(figsize=(6, 3.6), dpi=150)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    y = range(len(metrics))
    height = 0.32

    ax.barh(
        [i + height / 2 for i in y], before_vals, height=height,
        color=before_color, label="Before",
    )
    ax.barh(
        [i - height / 2 for i in y], after_vals, height=height,
        color=after_color, label="After",
    )

    for i, (b, a) in enumerate(zip(before_vals, after_vals)):
        ax.text(b + 1.5, i + height / 2, f"{b:g}%", va="center", color=fg, fontsize=9)
        ax.text(a + 1.5, i - height / 2, f"{a:g}%", va="center", color=fg, fontsize=9)

    ax.set_yticks(list(y))
    ax.set_yticklabels(metrics, color=fg, fontsize=10)
    ax.set_xlim(0, 122)
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False)
    ax.grid(axis="x", color=grid, linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)

    ax.legend(
        loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2,
        frameon=False, fontsize=9, labelcolor=fg,
    )

    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(out_path, facecolor=bg)
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _render("light", OUT_DIR / "results-en-light.png")
    _render("dark", OUT_DIR / "results-en-dark.png")
    print(f"Wrote {OUT_DIR / 'results-en-light.png'}")
    print(f"Wrote {OUT_DIR / 'results-en-dark.png'}")


if __name__ == "__main__":
    main()
