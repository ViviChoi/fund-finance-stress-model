"""
Demo Runner — apply the NAV stress model to five hypothetical PE funds.

Reads ../data/example_funds.json, runs each fund through both a benign
(30%-ish) and aggressive (50%-ish) facility, prints a summary table, and
saves a side-by-side comparison chart to ../figures/fund_comparison.png.

Intended use cases:
  1. Live demo during an interview — flip through five different funds
     and show how the model picks up the EV-concentration risk.
  2. Self-study — read the JSON, change a weight, re-run, see the chart shift.

Usage:
    cd code && ../.venv/bin/python demo_runner.py
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from nav_stress_model import Facility, stressed_ltv, portfolio_drawdown


HERE = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = HERE.parent / "data" / "example_funds.json"
DEFAULT_OUT_PATH = HERE.parent / "figures" / "fund_comparison.png"

# Backwards-compat aliases (used by tests and earlier imports)
DATA_PATH = DEFAULT_DATA_PATH
OUT_PATH = DEFAULT_OUT_PATH

COVENANT_LTV = 0.65


# ---------------------------------------------------------------------------
# 1.  Load + structure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FundScenario:
    id: str
    name: str
    vintage: int
    size_musd: float
    strategy: str
    weights: dict[str, float]
    facility_benign: Facility
    facility_aggressive: Facility
    narrative: str


def load_funds(path: Path | None = None) -> list[FundScenario]:
    path = Path(path) if path else DEFAULT_DATA_PATH
    with path.open() as f:
        payload = json.load(f)
    return [
        FundScenario(
            id=f["id"],
            name=f["name"],
            vintage=f["vintage"],
            size_musd=f["size_musd"],
            strategy=f["strategy"],
            weights=f["sub_sector_weights"],
            facility_benign=Facility(
                nav_initial_musd=f["size_musd"],
                facility_size_musd=f["facility_size_musd_benign"],
                covenant_ltv=COVENANT_LTV,
            ),
            facility_aggressive=Facility(
                nav_initial_musd=f["size_musd"],
                facility_size_musd=f["facility_size_musd_aggressive"],
                covenant_ltv=COVENANT_LTV,
            ),
            narrative=f["narrative_for_demo"],
        )
        for f in payload["funds"]
    ]


# ---------------------------------------------------------------------------
# 2.  Scoring + printing
# ---------------------------------------------------------------------------

def score(fund: FundScenario) -> dict:
    dd = portfolio_drawdown(fund.weights)
    ltv_b = stressed_ltv(fund.weights, fund.facility_benign)
    ltv_a = stressed_ltv(fund.weights, fund.facility_aggressive)
    return {
        "drawdown": dd,
        "ltv_benign": ltv_b,
        "ltv_aggressive": ltv_a,
        "initial_ltv_benign": fund.facility_benign.initial_ltv,
        "initial_ltv_aggressive": fund.facility_aggressive.initial_ltv,
        "breach_benign": ltv_b > COVENANT_LTV,
        "breach_aggressive": ltv_a > COVENANT_LTV,
    }


def print_summary(funds: list[FundScenario]) -> None:
    print()
    print("=" * 110)
    print(f"  NAV STRESS MODEL — {len(funds)} hypothetical funds")
    print(f"  Covenant LTV: {COVENANT_LTV:.0%}   Stress: sub-sector specific (see nav_stress_model.SECTOR_STRESS)")
    print("=" * 110)

    header = (
        f"{'Fund':<48}"
        f"{'Drawdown':>11}"
        f"{'Init LTV':>10}"
        f"{'Stressed':>11}"
        f"{'Status':>10}    |   "
        f"{'Init LTV':>9}"
        f"{'Stressed':>11}"
        f"{'Status':>10}"
    )
    print()
    print(f"{'':48}{'':11}{'   ----- BENIGN ------':>31}        {'   ---- AGGRESSIVE ----':>30}")
    print(header)
    print("-" * 130)

    for f in funds:
        s = score(f)
        b_status = "BREACH" if s["breach_benign"] else "ok"
        a_status = "BREACH" if s["breach_aggressive"] else "ok"
        id_col = f.id[:14]
        name_col = f.name[:32]
        print(
            f"{id_col:<16}{name_col:<34}"
            f"{s['drawdown']:>9.1%}"
            f"{s['initial_ltv_benign']:>10.0%}"
            f"{s['ltv_benign']:>10.1%}"
            f"{b_status:>11}    |   "
            f"{s['initial_ltv_aggressive']:>8.0%}"
            f"{s['ltv_aggressive']:>10.1%}"
            f"{a_status:>11}"
        )

    print("-" * 130)
    n_breach_b = sum(score(f)["breach_benign"] for f in funds)
    n_breach_a = sum(score(f)["breach_aggressive"] for f in funds)
    print(f"Breaches: {n_breach_b} / {len(funds)} under benign;  "
          f"{n_breach_a} / {len(funds)} under aggressive")
    print()


# ---------------------------------------------------------------------------
# 3.  Comparison chart
# ---------------------------------------------------------------------------

def plot_comparison(funds: list[FundScenario],
                    out_path: Path | None = None) -> None:
    out_path = Path(out_path) if out_path else DEFAULT_OUT_PATH
    n = len(funds)
    labels = [f.id for f in funds]
    benign  = np.array([score(f)["ltv_benign"]     for f in funds])
    aggro   = np.array([score(f)["ltv_aggressive"] for f in funds])
    drawdown = np.array([score(f)["drawdown"]     for f in funds])

    fig, axes = plt.subplots(1, 2, figsize=(14, 6.0),
                             gridspec_kw={"width_ratios": [3.0, 2.0],
                                          "wspace": 0.30})

    # ---- Left panel: stressed LTV bars by regime ------------------------
    ax = axes[0]
    y = np.arange(n)
    h = 0.38
    bars_b = ax.barh(y + h/2, benign,  height=h, color="#1f7a3c",
                     edgecolor="black", linewidth=0.5, label="Benign facility")
    bars_a = ax.barh(y - h/2, aggro,   height=h, color="#a81b1b",
                     edgecolor="black", linewidth=0.5, label="Aggressive facility")

    # Highlight breaches
    for i, (b, a) in enumerate(zip(benign, aggro)):
        if b > COVENANT_LTV:
            bars_b[i].set_color("#a81b1b")
        if a > COVENANT_LTV:
            bars_a[i].set_hatch("///")

    # Covenant line
    ax.axvline(COVENANT_LTV, color="black", linestyle="--", linewidth=1.8,
               label=f"Covenant LTV {COVENANT_LTV:.0%}")

    # Value labels at bar ends
    for i, v in enumerate(benign):
        ax.text(v + 0.005, i + h/2, f"{v:.0%}", va="center", fontsize=9)
    for i, v in enumerate(aggro):
        breach_tag = "  BREACH" if v > COVENANT_LTV else ""
        ax.text(v + 0.005, i - h/2, f"{v:.0%}{breach_tag}",
                va="center", fontsize=9,
                color="#a81b1b" if v > COVENANT_LTV else "black",
                fontweight="bold" if v > COVENANT_LTV else "normal")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=11, fontweight="bold")
    ax.set_xlim(0, max(aggro.max(), 1.0) + 0.10)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_xlabel("Stressed LTV", fontsize=11)
    ax.set_title("Stressed LTV by fund and facility regime\n"
                 "(hatched = covenant breach)",
                 fontsize=11.5)
    ax.legend(loc="lower right", fontsize=9)
    ax.invert_yaxis()
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)

    # ---- Right panel: portfolio drawdown by fund -----------------------
    ax2 = axes[1]
    colors = ["#a81b1b" if d <= -0.25 else
              "#d97706" if d <= -0.18 else "#1f7a3c"
              for d in drawdown]
    bars = ax2.barh(y, -drawdown * 100, color=colors,
                    edgecolor="black", linewidth=0.5)
    for i, d in enumerate(drawdown):
        ax2.text(-d*100 + 0.6, i, f"{d:.1%}", va="center", fontsize=10)

    ax2.set_yticks(y)
    ax2.set_yticklabels(labels, fontsize=11, fontweight="bold")
    ax2.xaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax2.set_xlabel("Portfolio NAV drawdown under sub-sector stress",
                   fontsize=11)
    ax2.set_title("Sector-weighted drawdown\n"
                  "(driven by EV exposure)", fontsize=11.5)
    ax2.invert_yaxis()
    ax2.grid(True, axis="x", linestyle="--", alpha=0.4)

    # ---- Footer ---------------------------------------------------------
    fig.suptitle(
        "Demo: five hypothetical PE funds run through the NAV stress model",
        fontsize=13.5, fontweight="bold", y=1.02,
    )

    plt.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4.  Talking-point output for live demo
# ---------------------------------------------------------------------------

def print_narratives(funds: list[FundScenario]) -> None:
    """Print one talking-point line per fund — what to say while clicking through."""
    print()
    print("=" * 110)
    print("  TALKING POINTS — read these while showing each fund on screen")
    print("=" * 110)
    for f in funds:
        s = score(f)
        verdict = (
            "BREACH under aggressive sizing" if s["breach_aggressive"]
            else "stays inside covenant, but thin headroom"
            if s["ltv_aggressive"] > 0.55
            else "comfortably inside"
        )
        print()
        print(f"  [{f.id}]  {f.name}  (vintage {f.vintage})")
        print(f"     Strategy: {f.strategy}")
        print(f"     Model verdict: {verdict} "
              f"(stressed LTV: {s['ltv_benign']:.0%} benign → {s['ltv_aggressive']:.0%} aggressive)")
        print(f"     Talking point: {f.narrative}")
    print()


# ---------------------------------------------------------------------------
# 5.  Main
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the NAV stress model over a JSON dataset of funds.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data", "-d", type=Path, default=DEFAULT_DATA_PATH,
        help="Path to a fund JSON file (schema: see data/example_funds.json).",
    )
    parser.add_argument(
        "--out", "-o", type=Path, default=DEFAULT_OUT_PATH,
        help="Where to write the comparison PNG.",
    )
    parser.add_argument(
        "--no-narratives", action="store_true",
        help="Skip printing per-fund talking-point narratives.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if not args.data.exists():
        raise SystemExit(f"✗ Data file not found: {args.data}")

    funds = load_funds(args.data)
    print_summary(funds)
    plot_comparison(funds, args.out)
    try:
        rel = args.out.relative_to(HERE.parent)
    except ValueError:
        rel = args.out
    print(f"Comparison chart saved to: {rel}")
    if not args.no_narratives:
        print_narratives(funds)


if __name__ == "__main__":
    main()
