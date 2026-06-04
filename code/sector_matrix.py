"""
Power-Electronics Sub-Sector Risk Matrix
=========================================

Section 2 figure: positions the four sub-sectors that get aggregated into
"power electronics" on two underwriting-relevant axes:

  x : demand cyclicality        (1 = defensive, 10 = highly cyclical)
  y : customer concentration    (1 = fragmented buyers, 10 = top-3 buyers
                                  account for >70% of revenue)
  bubble size : 2024-2026 listed-sector total-return dispersion (proxy for
                 implied vol of underlying private valuations)
  bubble label : representative listed comparables

Calibration sources: see content/01-page-content.md (Wolfspeed, Vertiv,
Schneider Electric, Enphase, ABB observed returns 2024-2026).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


SUBSECTORS = [
    # name, cyclicality (1-10), customer concentration (1-10),
    # bubble size (sector dispersion proxy), exemplars, colour
    ("EV powertrain",
     8.5, 8.0, 1800,
     "Wolfspeed, ON Semi, ST Micro\n(auto seg.)", "#d62728"),

    ("Data-center power",
     5.0, 7.5, 1500,
     "Vertiv, Schneider Electric\n(secure power div.)", "#1f77b4"),

    ("Renewable power conversion",
     7.0, 4.5, 1700,
     "Enphase, SolarEdge,\nSMA Solar", "#2ca02c"),

    ("Industrial drives",
     4.5, 3.0, 700,
     "ABB, Rockwell, Yaskawa", "#7f7f7f"),
]


def plot_subsector_matrix(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 7.5))

    # Quadrant background tint
    ax.axvspan(5, 10, ymin=0.5, alpha=0.06, color="red")     # high cyc + high conc
    ax.axvspan(0, 5,  ymin=0.0, ymax=0.5, alpha=0.06, color="green")  # low cyc + low conc

    # Sub-sector bubbles
    for name, cyc, conc, size, exemplars, colour in SUBSECTORS:
        ax.scatter(cyc, conc, s=size, c=colour, alpha=0.55,
                   edgecolors="black", linewidths=1.2, zorder=3)
        ax.annotate(f"{name}", xy=(cyc, conc), xytext=(0, 0),
                    textcoords="offset points",
                    ha="center", va="center",
                    fontsize=10, fontweight="bold", zorder=4)
        ax.annotate(exemplars, xy=(cyc, conc),
                    xytext=(0, -38),
                    textcoords="offset points",
                    ha="center", va="top",
                    fontsize=8, style="italic", color="#333333", zorder=4)

    # Diagonal "risk frontier" reference
    ax.plot([1, 10], [1, 10], linestyle=":", color="#888888", linewidth=1)
    ax.text(9.6, 9.0, "risk frontier", rotation=33, fontsize=8,
            color="#888888", ha="right")

    # Axis cosmetics
    ax.set_xlim(1, 10)
    ax.set_ylim(1, 10)
    ax.set_xlabel("Demand cyclicality  →  (defensive ··· highly cyclical)",
                  fontsize=11)
    ax.set_ylabel("Customer concentration  →  (fragmented ··· top-3 >70%)",
                  fontsize=11)
    ax.set_title(
        "‘Power Electronics’ is four different credits\n"
        "Sub-sector dispersion on the two axes that drive NAV facility risk",
        fontsize=12, pad=14,
    )
    ax.grid(True, linestyle="--", alpha=0.35)

    # Quadrant labels
    ax.text(7.5, 1.6, "  cyclical but fragmented\n(industrial-style risk)",
            fontsize=8.5, color="#555555", ha="center")
    ax.text(2.5, 9.4, "  defensive but concentrated\n  (buyer-loss risk)",
            fontsize=8.5, color="#555555", ha="center")
    ax.text(8.0, 9.4, "  cyclical AND concentrated\n  (severe underwriting risk)",
            fontsize=8.5, color="#a00000", ha="center", fontweight="bold")
    ax.text(2.5, 1.6, "  defensive + fragmented\n  (benign)",
            fontsize=8.5, color="#006000", ha="center")

    # Legend: bubble size meaning
    handles = [
        mpatches.Patch(color="#d62728", alpha=0.55, label="EV powertrain"),
        mpatches.Patch(color="#1f77b4", alpha=0.55, label="Data-center power"),
        mpatches.Patch(color="#2ca02c", alpha=0.55, label="Renewable power conversion"),
        mpatches.Patch(color="#7f7f7f", alpha=0.55, label="Industrial drives"),
    ]
    legend = ax.legend(handles=handles, loc="lower right", fontsize=9,
                       title="Sub-sector", framealpha=0.95)
    legend.get_title().set_fontweight("bold")

    # Footnote
    fig.text(
        0.5, 0.02,
        "Bubble area ∝ 2024-2026 listed-comparable total-return dispersion "
        "(proxy for implied vol of underlying private valuations). "
        "Source: public market data, illustrative.",
        ha="center", fontsize=8, style="italic", color="#666666",
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    out = "../figures/sector_matrix.png"
    plot_subsector_matrix(out)
    print(f"Figure saved to: {out}")
