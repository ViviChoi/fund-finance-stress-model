"""
NAV Facility Stress Model — Power Electronics Sector Decomposition
===================================================================

A first-look risk model for a NAV facility extended against a PE fund
concentrated in power electronics. Demonstrates how single-sector
underwriting under-prices risk when "power electronics" is internally
heterogeneous (EV / data center / renewable / industrial).

Author : EE Master's student, Politecnico di Milano
Purpose: Illustrative deliverable for UniCredit CIB Fund Financing outreach
Notes  : Drawdown assumptions are calibrated to observed 2024-2026 public-
         market sector dispersion (see content/01-page-content.md). They
         are placeholders for first-look discussion, not a production model.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 1.  Facility & fund baseline
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Facility:
    """A simplified NAV facility against a sector-concentrated PE fund."""
    nav_initial_musd: float = 500.0
    facility_size_musd: float = 150.0
    covenant_ltv: float = 0.65          # facility events of default trigger
    initial_advance_rate: float = 0.30  # NAV % advanced at close

    @property
    def initial_ltv(self) -> float:
        return self.facility_size_musd / self.nav_initial_musd


# ---------------------------------------------------------------------------
# 2.  Sub-sector stress assumptions (engineer's sector view)
# ---------------------------------------------------------------------------
#
# Calibration anchors (public-market 2024-2026 drawdowns / surges used as
# directional proxies — private valuations lag and dampen, but dispersion
# direction is the point):
#
#   * EV powertrain       : Wolfspeed -70%, ST Micro auto seg. -30%, ON Semi
#                           -40%. Demand pull-in from 2023 EV boom unwound;
#                           OEM concentration (5-10 buyers) amplifies.
#   * Data center power   : Vertiv +280%, Schneider Electric +60%. AI-capex
#                           super-cycle, hyperscaler demand still ramping
#                           but lumpy quarterly.
#   * Renewable power     : Enphase -75%, SolarEdge -85%. US IRA uncertainty
#                           + China oversupply + interest-rate sensitivity.
#   * Industrial drives   : ABB +25%, Rockwell flat. Mid-cycle baseline,
#                           fragmented buyer base.
#
# We translate observed listed-equity dispersion into a conservative PE
# NAV stress (typically ~50-70% of public-market move, given mark-to-model
# lag and partial recoveries already baked in).

SECTOR_STRESS = {
    "ev_powertrain":      -0.35,   # severe consumer-led drawdown
    "data_center_power":  -0.10,   # mild — lumpy but secular tailwind
    "renewable_power":    -0.30,   # policy + oversupply shock
    "industrial_drives":  -0.10,   # mid-cycle, defensive
}


def portfolio_drawdown(weights: dict[str, float]) -> float:
    """Weighted-average NAV drawdown across sub-sectors.

    Assumes within-sub-sector dispersion is averaged out; cross-sub-sector
    correlation is implicitly 0 (additive). A full model would add a
    correlation matrix — flagged as next-step in the Q&A.
    """
    if not np.isclose(sum(weights.values()), 1.0, atol=1e-6):
        raise ValueError(f"weights must sum to 1.0; got {sum(weights.values()):.4f}")
    return sum(w * SECTOR_STRESS[s] for s, w in weights.items())


def stressed_ltv(weights: dict[str, float], facility: Facility) -> float:
    """Facility LTV after applying sub-sector stress drawdowns to NAV."""
    dd = portfolio_drawdown(weights)
    stressed_nav = facility.nav_initial_musd * (1 + dd)
    return facility.facility_size_musd / stressed_nav


# ---------------------------------------------------------------------------
# 3.  Sensitivity sweep — EV exposure x Data-center exposure
# ---------------------------------------------------------------------------

def sweep_ltv_grid(
    facility: Facility,
    grid_points: int = 41,
    residual_split: tuple[float, float] = (0.6, 0.4),  # renewable / industrial
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sweep (EV%, DC%) and compute stressed LTV at each feasible point.

    The remaining (1 - EV - DC) of the portfolio is split between
    renewable_power and industrial_drives by `residual_split`. NaN where
    EV + DC > 1 (infeasible).
    """
    axis = np.linspace(0.0, 1.0, grid_points)
    matrix = np.full((grid_points, grid_points), np.nan)

    for i, ev in enumerate(axis):
        for j, dc in enumerate(axis):
            if ev + dc > 1.0 + 1e-9:
                continue
            residual = max(1.0 - ev - dc, 0.0)
            weights = {
                "ev_powertrain":      ev,
                "data_center_power":  dc,
                "renewable_power":    residual * residual_split[0],
                "industrial_drives":  residual * residual_split[1],
            }
            matrix[i, j] = stressed_ltv(weights, facility)

    return axis, axis, matrix


# ---------------------------------------------------------------------------
# 4.  Plot — heatmap + covenant breach contour
# ---------------------------------------------------------------------------

def _draw_panel(ax, ev_axis, dc_axis, ltv_matrix, facility, vmin, vmax):
    """Draw one heatmap panel for a given facility (initial LTV scenario)."""
    im = ax.imshow(
        ltv_matrix.T,
        origin="lower",
        extent=[0.0, 1.0, 0.0, 1.0],
        aspect="auto",
        cmap="RdYlGn_r",
        vmin=vmin,
        vmax=vmax,
    )

    # Covenant breach contour (only if any cell exceeds the covenant)
    if np.nanmax(ltv_matrix) > facility.covenant_ltv:
        cs = ax.contour(
            ev_axis, dc_axis, ltv_matrix.T,
            levels=[facility.covenant_ltv],
            colors="black",
            linewidths=2.2,
            linestyles="--",
        )
        ax.clabel(
            cs,
            fmt={facility.covenant_ltv:
                 f"Covenant {facility.covenant_ltv:.0%}"},
            fontsize=9,
            inline=True,
        )

    # Infeasibility shading (EV + DC > 1)
    ev_mesh, dc_mesh = np.meshgrid(ev_axis, dc_axis, indexing="xy")
    ax.contourf(
        ev_axis, dc_axis, (ev_mesh + dc_mesh > 1.0).astype(float),
        levels=[0.5, 1.5], colors=["#dddddd"], alpha=0.92,
    )
    ax.text(0.80, 0.80, "infeasible\n(EV+DC>1)", fontsize=9,
            ha="center", va="center", color="#444444")

    # Reference points
    for ev, dc, label, off in [
        (1.0, 0.0, "100% EV",       (-8, 12)),
        (0.0, 1.0, "100% DC power", (12, -4)),
        (0.5, 0.5, "50/50",         (10, 10)),
    ]:
        ax.plot(ev, dc, "o", color="white", markeredgecolor="black",
                markersize=8, zorder=5)
        ax.annotate(
            label, xy=(ev, dc), xytext=off, textcoords="offset points",
            fontsize=8.5, ha="left" if off[0] > 0 else "right",
            bbox=dict(boxstyle="round,pad=0.22",
                      fc="white", ec="black", lw=0.5),
        )

    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_xlabel("EV powertrain exposure  (% of NAV)", fontsize=10)
    ax.set_ylabel("Data-center power exposure  (% of NAV)", fontsize=10)
    ax.set_title(
        f"Initial LTV {facility.initial_ltv:.0%}  —  facility "
        f"USD {facility.facility_size_musd:.0f}M / NAV "
        f"USD {facility.nav_initial_musd:.0f}M",
        fontsize=10.5,
    )
    return im


def plot_ltv_heatmap_dual(
    ev_axis: np.ndarray,
    dc_axis: np.ndarray,
    ltv_benign: np.ndarray,
    ltv_aggressive: np.ndarray,
    facility_benign: Facility,
    facility_aggressive: Facility,
    out_path: str,
) -> None:
    """Two-panel comparison: benign (30% initial LTV) vs aggressive (50%)."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.2),
                             gridspec_kw={"wspace": 0.30})

    # Use the maximum value across both panels to set a shared scale,
    # but cap at a reasonable visual range so dispersion stays visible.
    vmin = 0.30
    vmax = max(np.nanmax(ltv_aggressive), 0.90)

    _draw_panel(axes[0], ev_axis, dc_axis, ltv_benign,
                facility_benign, vmin, vmax)
    im = _draw_panel(axes[1], ev_axis, dc_axis, ltv_aggressive,
                     facility_aggressive, vmin, vmax)

    # Shared colourbar to the right
    cbar = fig.colorbar(im, ax=axes, shrink=0.85, pad=0.02,
                        label="Post-stress LTV")
    cbar.formatter = mticker.PercentFormatter(1.0)
    cbar.update_ticks()

    # Suptitle communicates the comparison
    fig.suptitle(
        "Stressed NAV Facility LTV under sector-specific shocks\n"
        "Same fund, two facility-sizing regimes  —  covenant "
        f"{facility_benign.covenant_ltv:.0%}",
        fontsize=12.5, y=1.02,
    )

    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


# Backwards-compatible single-panel wrapper (kept for users who only want one)
def plot_ltv_heatmap(ev_axis, dc_axis, ltv_matrix, facility, out_path):
    fig, ax = plt.subplots(figsize=(9, 7))
    im = _draw_panel(ax, ev_axis, dc_axis, ltv_matrix, facility,
                     vmin=0.30, vmax=max(np.nanmax(ltv_matrix), 0.80))
    cbar = plt.colorbar(im, ax=ax, label="Post-stress LTV")
    cbar.formatter = mticker.PercentFormatter(1.0)
    cbar.update_ticks()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5.  Driver — quantify three reference portfolios + sweep + plot
# ---------------------------------------------------------------------------

def reference_portfolios(facility: Facility) -> None:
    """Print stressed LTV for three illustrative single-theme portfolios."""
    cases = {
        "100% EV powertrain":    {"ev_powertrain": 1.0, "data_center_power": 0.0,
                                  "renewable_power": 0.0, "industrial_drives": 0.0},
        "100% data-center power": {"ev_powertrain": 0.0, "data_center_power": 1.0,
                                   "renewable_power": 0.0, "industrial_drives": 0.0},
        "Diversified (25/25/25/25)": {"ev_powertrain": 0.25, "data_center_power": 0.25,
                                       "renewable_power": 0.25, "industrial_drives": 0.25},
    }
    print(f"\nFacility — NAV ${facility.nav_initial_musd:.0f}M, "
          f"size ${facility.facility_size_musd:.0f}M, "
          f"initial LTV {facility.initial_ltv:.1%}, "
          f"covenant {facility.covenant_ltv:.0%}\n")
    print(f"{'Portfolio':<32}{'Drawdown':>12}{'Stressed NAV':>16}{'Stressed LTV':>16}{'Status':>14}")
    print("-" * 90)
    for name, w in cases.items():
        dd = portfolio_drawdown(w)
        snav = facility.nav_initial_musd * (1 + dd)
        ltv = stressed_ltv(w, facility)
        status = "BREACH" if ltv > facility.covenant_ltv else "ok"
        print(f"{name:<32}{dd:>11.1%}{snav:>15.1f}M{ltv:>15.1%}{status:>14}")
    print()


def main() -> None:
    # Scenario A — benign 30% initial LTV
    facility_benign = Facility(nav_initial_musd=500.0,
                               facility_size_musd=150.0,
                               covenant_ltv=0.65)
    reference_portfolios(facility_benign)

    # Scenario B — aggressive 50% initial LTV (where breach becomes plausible)
    facility_aggressive = Facility(nav_initial_musd=500.0,
                                   facility_size_musd=250.0,
                                   covenant_ltv=0.65)
    reference_portfolios(facility_aggressive)

    ev_axis, dc_axis, ltv_benign = sweep_ltv_grid(facility_benign, grid_points=41)
    _, _, ltv_aggressive = sweep_ltv_grid(facility_aggressive, grid_points=41)

    out_path = "../figures/nav_ltv_heatmap.png"
    plot_ltv_heatmap_dual(
        ev_axis, dc_axis,
        ltv_benign, ltv_aggressive,
        facility_benign, facility_aggressive,
        out_path,
    )
    print(f"Dual-panel heatmap saved to: {out_path}")


if __name__ == "__main__":
    main()
