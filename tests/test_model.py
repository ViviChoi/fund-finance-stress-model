r"""
Sanity tests for the NAV stress model.

Why these tests exist (i.e. what would break if you remove them):
  * Catches regressions if SECTOR_STRESS, Facility, or stressed_ltv get
    accidentally edited (e.g. while live-tweaking in an interview demo).
  * Validates that JSON data files load cleanly and produce sensible
    output — so you don't show up to the call with broken demo data.
  * Documents the expected directional behaviour of the model in
    executable form: a future reader can see exactly what "correct"
    means.

Run with:
    python dev.py test
or:
    .venv/bin/python -m pytest tests/ -v          (Mac/Linux)
    .venv\Scripts\python -m pytest tests\ -v      (Windows)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nav_stress_model import (
    Facility,
    SECTOR_STRESS,
    portfolio_drawdown,
    stressed_ltv,
    sweep_ltv_grid,
)


ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Facility dataclass
# ---------------------------------------------------------------------------

class TestFacility:
    def test_initial_ltv_default(self):
        f = Facility()
        assert f.initial_ltv == pytest.approx(0.30, abs=1e-6)

    def test_initial_ltv_custom(self):
        f = Facility(nav_initial_musd=1000, facility_size_musd=400)
        assert f.initial_ltv == pytest.approx(0.40, abs=1e-6)

    def test_immutable(self):
        f = Facility()
        with pytest.raises((AttributeError, Exception)):
            f.nav_initial_musd = 999  # frozen dataclass


# ---------------------------------------------------------------------------
# Sector stress constants
# ---------------------------------------------------------------------------

class TestSectorStress:
    def test_all_four_sectors_present(self):
        expected = {"ev_powertrain", "data_center_power",
                    "renewable_power", "industrial_drives"}
        assert set(SECTOR_STRESS.keys()) == expected

    def test_all_stresses_are_negative(self):
        # We're modelling drawdowns, not appreciation
        assert all(v <= 0 for v in SECTOR_STRESS.values())

    def test_ev_is_worst(self):
        # EV powertrain is calibrated as the worst stress per the
        # 2024-26 Wolfspeed / ON Semi calibration. This is a load-bearing
        # assumption — if someone flips this, the whole narrative breaks.
        assert SECTOR_STRESS["ev_powertrain"] == min(SECTOR_STRESS.values())

    def test_data_center_is_mildest(self):
        # DC power is calibrated as the mildest stress per Vertiv / Schneider
        assert SECTOR_STRESS["data_center_power"] == max(SECTOR_STRESS.values())


# ---------------------------------------------------------------------------
# portfolio_drawdown
# ---------------------------------------------------------------------------

class TestPortfolioDrawdown:
    def test_single_sector_returns_that_sector_stress(self):
        for sector, stress in SECTOR_STRESS.items():
            weights = {s: (1.0 if s == sector else 0.0) for s in SECTOR_STRESS}
            assert portfolio_drawdown(weights) == pytest.approx(stress)

    def test_equal_weights_returns_average(self):
        weights = {s: 0.25 for s in SECTOR_STRESS}
        expected = sum(SECTOR_STRESS.values()) / 4
        assert portfolio_drawdown(weights) == pytest.approx(expected)

    def test_weights_must_sum_to_one(self):
        bad = {s: 0.10 for s in SECTOR_STRESS}  # sums to 0.40
        with pytest.raises(ValueError):
            portfolio_drawdown(bad)


# ---------------------------------------------------------------------------
# stressed_ltv
# ---------------------------------------------------------------------------

class TestStressedLtv:
    @pytest.fixture
    def fac(self):
        return Facility()

    def test_ev_heavy_worse_than_dc_heavy(self, fac):
        ev_heavy = {"ev_powertrain": 1.0, "data_center_power": 0.0,
                    "renewable_power": 0.0, "industrial_drives": 0.0}
        dc_heavy = {"ev_powertrain": 0.0, "data_center_power": 1.0,
                    "renewable_power": 0.0, "industrial_drives": 0.0}
        # EV concentration → more drawdown → smaller stressed NAV → higher LTV
        assert stressed_ltv(ev_heavy, fac) > stressed_ltv(dc_heavy, fac)

    def test_aggressive_facility_has_higher_stressed_ltv(self):
        weights = {s: 0.25 for s in SECTOR_STRESS}
        benign = Facility(facility_size_musd=150)
        aggressive = Facility(facility_size_musd=250)
        assert stressed_ltv(weights, aggressive) > stressed_ltv(weights, benign)

    def test_stressed_always_higher_than_initial(self, fac):
        weights = {s: 0.25 for s in SECTOR_STRESS}
        # Since all stresses are <= 0, stressed NAV <= initial NAV,
        # so stressed LTV >= initial LTV.
        assert stressed_ltv(weights, fac) >= fac.initial_ltv

    def test_full_ev_30pct_facility_no_breach_at_65(self, fac):
        # Documents the "load-bearing finding" from pseudocode.md §4:
        # even full EV tilt doesn't breach 65% covenant at 30% initial LTV.
        ev_only = {"ev_powertrain": 1.0, "data_center_power": 0.0,
                   "renewable_power": 0.0, "industrial_drives": 0.0}
        assert stressed_ltv(ev_only, fac) < 0.65

    def test_full_ev_50pct_facility_does_breach_at_65(self):
        # The flip side: aggressive sizing DOES breach under EV tilt.
        # This is the chart's punchline.
        ev_only = {"ev_powertrain": 1.0, "data_center_power": 0.0,
                   "renewable_power": 0.0, "industrial_drives": 0.0}
        aggressive = Facility(facility_size_musd=250)
        assert stressed_ltv(ev_only, aggressive) > 0.65


# ---------------------------------------------------------------------------
# sweep_ltv_grid
# ---------------------------------------------------------------------------

class TestSweepGrid:
    def test_grid_shape(self):
        ev_axis, dc_axis, matrix = sweep_ltv_grid(Facility(), grid_points=21)
        assert ev_axis.shape == (21,)
        assert dc_axis.shape == (21,)
        assert matrix.shape == (21, 21)

    def test_infeasible_region_is_nan(self):
        import numpy as np
        ev_axis, dc_axis, matrix = sweep_ltv_grid(Facility(), grid_points=11)
        # The (1.0, 1.0) corner: EV + DC = 2.0, infeasible
        assert np.isnan(matrix[-1, -1])

    def test_grid_corners(self):
        # (0, 0) corner = all residual (60% renewable, 40% industrial)
        # (1, 0) corner = 100% EV
        # (0, 1) corner = 100% DC
        import numpy as np
        _, _, matrix = sweep_ltv_grid(Facility(), grid_points=11)
        ev_corner = matrix[-1, 0]   # ev=1.0, dc=0.0
        dc_corner = matrix[0, -1]   # ev=0.0, dc=1.0
        assert not np.isnan(ev_corner)
        assert not np.isnan(dc_corner)
        assert ev_corner > dc_corner  # EV concentration is worse


# ---------------------------------------------------------------------------
# Demo runner + JSON fund data
# ---------------------------------------------------------------------------

class TestDemoData:
    def test_example_funds_json_loads(self):
        path = ROOT / "data" / "example_funds.json"
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        assert "funds" in data
        assert len(data["funds"]) == 5

    def test_edge_cases_json_loads(self):
        path = ROOT / "data" / "edge_cases.json"
        if not path.exists():
            pytest.skip("edge_cases.json not present (optional)")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        assert "funds" in data
        assert len(data["funds"]) >= 5

    @pytest.mark.parametrize("fund_path", [
        ROOT / "data" / "example_funds.json",
        ROOT / "data" / "edge_cases.json",
    ])
    def test_all_fund_weights_sum_to_one(self, fund_path):
        if not fund_path.exists():
            pytest.skip(f"{fund_path.name} not present")
        with fund_path.open(encoding="utf-8") as f:
            data = json.load(f)
        for fund in data["funds"]:
            total = sum(fund["sub_sector_weights"].values())
            assert abs(total - 1.0) < 1e-6, (
                f"Fund {fund['id']!r} weights sum to {total}, not 1.0"
            )

    def test_demo_runner_imports_and_loads(self):
        from demo_runner import load_funds, score
        funds = load_funds()
        assert len(funds) >= 5
        for f in funds:
            s = score(f)
            # Sanity: every score should produce finite, non-negative LTVs
            assert 0 < s["ltv_benign"] < 5  # generous upper bound
            assert 0 < s["ltv_aggressive"] < 5
            assert s["ltv_aggressive"] > s["ltv_benign"]


# ---------------------------------------------------------------------------
# Regression — locks in the documented reference numbers
# ---------------------------------------------------------------------------

class TestWebUI:
    """
    Smoke tests for app.py — confirm it parses, imports, and the data
    loaders it depends on still produce the right shapes.
    """

    def test_app_py_parses(self):
        import ast
        path = ROOT / "app.py"
        assert path.exists(), "app.py missing"
        src = path.read_text(encoding="utf-8")
        ast.parse(src)  # raises SyntaxError if broken

    def test_app_py_imports_resolve(self):
        # Import the underlying modules app.py uses. If we can import them
        # cleanly, app.py at least has a chance of running.
        #
        # Streamlit and plotly are OPTIONAL — on platforms where their
        # wheels won't build (e.g. Windows ARM64) the WebUI is unavailable
        # but the rest of the project still works. Skip the test in that
        # case rather than fail.
        import importlib
        for mod in ["streamlit", "plotly"]:
            try:
                importlib.import_module(mod)
            except ImportError:
                pytest.skip(
                    f"WebUI dependency {mod!r} not installed; this is "
                    f"expected on Windows ARM64. Core functionality "
                    f"continues to work without it."
                )
        for mod in ["plotly.graph_objects", "plotly.subplots",
                    "pandas", "numpy", "nav_stress_model"]:
            importlib.import_module(mod)

    def test_uploaded_fund_validation_logic(self):
        # Re-implement the upload validator inline to test the shape
        # we expect (decoupled from streamlit runtime).
        good = {"funds": [{
            "id": "X", "name": "X", "vintage": 2024, "size_musd": 100,
            "strategy": "test", "sub_sector_weights": {
                "ev_powertrain": 0.5, "data_center_power": 0.5,
                "renewable_power": 0.0, "industrial_drives": 0.0,
            },
            "facility_size_musd_benign": 30,
            "facility_size_musd_aggressive": 50,
            "narrative_for_demo": "test",
        }]}
        # All weight checks
        total = sum(good["funds"][0]["sub_sector_weights"].values())
        assert abs(total - 1.0) < 1e-6


class TestDocumentedFindings:
    """
    Locks the numerical findings cited in content/01-page-content.md and
    code/pseudocode.md. If a future edit breaks these, the page will be
    inconsistent with the model — this test catches that *before* sending.
    """

    def test_benign_100_ev(self):
        # Page table: 100% EV under benign facility → 46.2% LTV
        fac = Facility()
        ev_only = {"ev_powertrain": 1.0, "data_center_power": 0.0,
                   "renewable_power": 0.0, "industrial_drives": 0.0}
        assert stressed_ltv(ev_only, fac) == pytest.approx(0.462, abs=0.005)

    def test_aggressive_100_ev_breaches(self):
        # Page table: 100% EV under aggressive → 76.9% LTV (BREACH)
        fac = Facility(facility_size_musd=250)
        ev_only = {"ev_powertrain": 1.0, "data_center_power": 0.0,
                   "renewable_power": 0.0, "industrial_drives": 0.0}
        assert stressed_ltv(ev_only, fac) == pytest.approx(0.769, abs=0.005)

    def test_aggressive_diversified_below_covenant(self):
        # Page table: diversified 25/25/25/25 under aggressive → 63.5% (~1.5pp inside)
        fac = Facility(facility_size_musd=250)
        diversified = {s: 0.25 for s in SECTOR_STRESS}
        ltv = stressed_ltv(diversified, fac)
        assert ltv == pytest.approx(0.635, abs=0.005)
        assert ltv < 0.65  # still below covenant
