"""
UniCredit Fund Financing — First Look (Streamlit WebUI)

Interactive front-end for the NAV stress model. Lets a non-coder reader
(target audience: a CFA-trained recruiter / a banker on the desk) drive
the model directly: upload a fund profile, tweak stress assumptions,
see the covenant-breach contour shift live.

Run locally:
    .venv/bin/python -m streamlit run app.py         (Mac / Linux)
    .venv\\Scripts\\python -m streamlit run app.py    (Windows)

Or via dev.py:
    python dev.py serve

Then open http://localhost:8501 in any browser.
"""

from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "code"))

from nav_stress_model import (   # noqa: E402  (path setup above)
    Facility,
    SECTOR_STRESS as DEFAULT_SECTOR_STRESS,
    portfolio_drawdown,
    stressed_ltv,
    sweep_ltv_grid,
)


# ===========================================================================
# Configuration
# ===========================================================================

st.set_page_config(
    page_title="UniCredit Fund Financing — First Look",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Visual system — matches the deck
INK = "#1B1F29"
INK_SOFT = "#555B6B"
ACCENT = "#B6142E"
ACCENT_SOFT = "#D7AEB5"
OK = "#1F7A3C"
BAD = "#A81B1B"
WARN = "#D97706"
BG_PANEL = "#F4F5F7"

SECTOR_LABELS = {
    "ev_powertrain":     "EV powertrain",
    "data_center_power": "Data-center power",
    "renewable_power":   "Renewable power conv.",
    "industrial_drives": "Industrial drives",
}

SECTOR_COLORS = {
    "ev_powertrain":     "#d62728",
    "data_center_power": "#1f77b4",
    "renewable_power":   "#2ca02c",
    "industrial_drives": "#7f7f7f",
}


# ===========================================================================
# Custom CSS — tighten Streamlit defaults to feel less "demo-y"
# ===========================================================================

st.markdown(f"""
<style>
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }}
    h1, h2, h3 {{
        color: {INK};
        font-weight: 600;
    }}
    h1 {{
        border-bottom: 3px solid {ACCENT};
        padding-bottom: 0.4rem;
        margin-bottom: 1rem;
    }}
    .accent-bar {{
        height: 4px;
        background: {ACCENT};
        margin-bottom: 1rem;
        border-radius: 2px;
    }}
    div[data-testid="stMetricValue"] {{
        color: {INK};
        font-size: 1.8rem;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {INK_SOFT};
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.25rem;
        border-bottom: 1px solid #d7dae0;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }}
    .stTabs [aria-selected="true"] {{
        color: {ACCENT};
        font-weight: 600;
        border-bottom: 2px solid {ACCENT};
    }}
    section[data-testid="stSidebar"] {{
        background-color: {INK};
    }}
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {{
        color: white !important;
    }}
    .stAlert {{
        border-radius: 4px;
    }}
</style>
""", unsafe_allow_html=True)


# ===========================================================================
# Data loading
# ===========================================================================

DATASETS = {
    "Demo (5 realistic PE funds)": ROOT / "data" / "example_funds.json",
    "Edge cases (8 boundary funds)": ROOT / "data" / "edge_cases.json",
}


@st.cache_data
def load_fund_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_uploaded(uploaded_bytes: bytes) -> dict | None:
    try:
        data = json.loads(uploaded_bytes.decode("utf-8"))
        # Light validation
        assert "funds" in data, "JSON must contain a 'funds' key."
        for f in data["funds"]:
            assert "sub_sector_weights" in f, f"Fund missing weights: {f.get('id')}"
            w = f["sub_sector_weights"]
            assert abs(sum(w.values()) - 1.0) < 0.001, (
                f"Fund {f.get('id')!r} weights sum to {sum(w.values()):.4f}, not 1.0"
            )
        return data
    except (json.JSONDecodeError, AssertionError, KeyError) as e:
        st.error(f"Invalid fund JSON: {e}")
        return None


# ===========================================================================
# Sidebar
# ===========================================================================

with st.sidebar:
    st.markdown(f'<h2 style="color: {ACCENT_SOFT}; font-size: 0.9rem; '
                f'letter-spacing: 0.15em; margin: 0;">FIRST LOOK</h2>',
                unsafe_allow_html=True)
    st.markdown(
        '<h2 style="color: white; margin-top: 0.2rem; font-size: 1.3rem;">'
        'NAV Facility Stress Model</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div style="height: 3px; background: {ACCENT}; '
                'width: 50px; margin-bottom: 1.5rem;"></div>',
                unsafe_allow_html=True)

    st.markdown("### Dataset")
    dataset_choice = st.radio(
        "Choose a fund dataset",
        list(DATASETS.keys()) + ["Upload your own"],
        label_visibility="collapsed",
    )

    if dataset_choice == "Upload your own":
        uploaded = st.file_uploader(
            "Drop a fund JSON file",
            type=["json"],
            help="Must contain a 'funds' list. Each fund needs "
                 "'sub_sector_weights' summing to 1.0. See "
                 "data/example_funds.json for the schema.",
        )
        if uploaded is not None:
            data = load_uploaded(uploaded.read())
        else:
            data = None
            st.info("Waiting for a JSON file — or pick a built-in dataset above.")
    else:
        data = load_fund_json(str(DATASETS[dataset_choice]))

    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        f'<p style="color: {ACCENT_SOFT}; font-size: 0.8rem; line-height: 1.4;">'
        'Built by an EE M.Sc. student at Politecnico di Milano as a first-look '
        'for UniCredit CIB Fund Financing. Interactive front-end on top of a '
        '~300-line Python sensitivity model. All numbers illustrative.'
        '</p>',
        unsafe_allow_html=True,
    )


# ===========================================================================
# Main — gate on data being loaded
# ===========================================================================

if data is None:
    st.title("UniCredit Fund Financing — First Look")
    st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
    st.info("Pick a dataset in the sidebar to begin.")
    st.stop()

funds = data["funds"]


# ===========================================================================
# Header
# ===========================================================================

st.title("UniCredit Fund Financing — First Look")
st.markdown(
    f'<p style="color: {INK_SOFT}; font-size: 1.05rem; margin-top: -0.5rem;">'
    'A power-electronics sub-sector risk lens on NAV / hybrid facilities. '
    f'Currently loaded: <strong style="color: {ACCENT};">{dataset_choice}</strong> '
    f'({len(funds)} funds).'
    '</p>',
    unsafe_allow_html=True,
)


# ===========================================================================
# Tabs
# ===========================================================================

tab_overview, tab_explorer, tab_compare, tab_stress = st.tabs([
    "📋  Overview",
    "🔍  Fund Explorer",
    "📊  Compare Funds",
    "🧪  Stress Lab",
])


# ---------------------------------------------------------------------------
# TAB 1 — Overview
# ---------------------------------------------------------------------------

with tab_overview:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Funds in dataset", len(funds))
    with col2:
        total_aum = sum(f["size_musd"] for f in funds)
        st.metric("Combined NAV", f"${total_aum/1000:.1f}B")
    with col3:
        n_breach_aggro = sum(
            1 for f in funds
            if stressed_ltv(
                f["sub_sector_weights"],
                Facility(
                    nav_initial_musd=f["size_musd"],
                    facility_size_musd=f["facility_size_musd_aggressive"],
                ),
            ) > 0.65
        )
        st.metric("Aggressive breaches", f"{n_breach_aggro} / {len(funds)}")
    with col4:
        st.metric("Covenant LTV", "65%")

    st.markdown("---")
    st.markdown("### The argument in three claims")
    c1, c2, c3 = st.columns(3)
    for col, num, text in zip(
        [c1, c2, c3], ["01", "02", "03"],
        [
            "2026 fund finance is shifting toward NAV and hybrid facilities — "
            "and the next underwriting bottleneck is **sector-specific risk "
            "modelling on concentrated portfolios**.",

            "**'Power electronics' is internally heterogeneous.** "
            "EV powertrain, data-center power, renewables and industrial drives "
            "behaved like four different credits in 2024–26 — listed comparables "
            "ranged from −75% to +280%.",

            "A small Python model makes the gap visible: at 50% initial LTV, "
            "**EV-heavy tilts breach a 65% covenant** under stress; data-center "
            "heavy tilts don't. Single-bucket haircuts can't see the line.",
        ]
    ):
        with col:
            st.markdown(
                f'<div style="background:{BG_PANEL};padding:1rem;border-radius:6px;'
                f'border-left:4px solid {ACCENT};height:100%;">'
                f'<div style="color:{ACCENT};font-weight:700;font-size:1.5rem;'
                'margin-bottom:0.4rem;">' + num + '</div>'
                f'<div style="color:{INK};font-size:0.95rem;line-height:1.4;">'
                + text + '</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    with st.expander("📖  How to read this model", expanded=False):
        st.markdown("""
* The model takes a **PE fund's sub-sector exposure** and a **facility size** as input.
* It applies a **sub-sector-specific drawdown** (calibrated from 2024–26 listed comparables) to each portion of the portfolio.
* It computes the **stressed NAV** and the resulting **stressed LTV**.
* A **covenant LTV** (default 65%) above which the facility breaches.

The headline finding: the same fund profile can be either safe or in
breach depending purely on **how much facility you put against it** —
and that decision should be informed by the fund's sub-sector mix, not
a single 'power electronics' bucket.
        """)


# ---------------------------------------------------------------------------
# TAB 2 — Fund Explorer
# ---------------------------------------------------------------------------

with tab_explorer:
    fund_labels = [f"{f['id']}  —  {f['name']}" for f in funds]
    chosen_label = st.selectbox("Pick a fund to explore", fund_labels)
    chosen_idx = fund_labels.index(chosen_label)
    fund = funds[chosen_idx]

    st.markdown(
        f'<h3 style="margin-bottom:0;">{fund["name"]}</h3>'
        f'<p style="color:{INK_SOFT};margin-top:0.2rem;">'
        f'Vintage {fund["vintage"]}  ·  NAV USD {fund["size_musd"]:,.0f}M  ·  '
        f'<em>{fund["strategy"]}</em></p>',
        unsafe_allow_html=True,
    )

    weights = fund["sub_sector_weights"]
    fac_benign = Facility(
        nav_initial_musd=fund["size_musd"],
        facility_size_musd=fund["facility_size_musd_benign"],
    )
    fac_aggressive = Facility(
        nav_initial_musd=fund["size_musd"],
        facility_size_musd=fund["facility_size_musd_aggressive"],
    )
    dd = portfolio_drawdown(weights)
    ltv_b = stressed_ltv(weights, fac_benign)
    ltv_a = stressed_ltv(weights, fac_aggressive)

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio drawdown", f"{dd:.1%}")
    m2.metric("Stressed NAV", f"${fund['size_musd'] * (1+dd):,.0f}M")
    m3.metric(
        "Stressed LTV — benign", f"{ltv_b:.1%}",
        delta="BREACH" if ltv_b > 0.65 else f"{(0.65-ltv_b)*100:.1f}pp inside covenant",
        delta_color="inverse" if ltv_b > 0.65 else "normal",
    )
    m4.metric(
        "Stressed LTV — aggressive", f"{ltv_a:.1%}",
        delta="BREACH" if ltv_a > 0.65 else f"{(0.65-ltv_a)*100:.1f}pp inside covenant",
        delta_color="inverse" if ltv_a > 0.65 else "normal",
    )

    st.markdown("---")

    # Two-column: weights pie + stressed LTV bars
    left, right = st.columns([1.1, 1.3])

    with left:
        st.markdown("##### Sub-sector exposure")
        fig_pie = go.Figure(go.Pie(
            labels=[SECTOR_LABELS[k] for k in weights],
            values=list(weights.values()),
            marker=dict(
                colors=[SECTOR_COLORS[k] for k in weights],
                line=dict(color="white", width=2),
            ),
            textinfo="label+percent",
            textposition="outside",
            hole=0.45,
        ))
        fig_pie.update_layout(
            height=350, showlegend=False,
            margin=dict(l=0, r=0, t=10, b=10),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with right:
        st.markdown("##### Stressed LTV vs covenant")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=["Benign facility", "Aggressive facility"],
            y=[ltv_b, ltv_a],
            marker_color=[
                BAD if ltv_b > 0.65 else OK,
                BAD if ltv_a > 0.65 else (WARN if ltv_a > 0.55 else OK),
            ],
            text=[f"{ltv_b:.1%}", f"{ltv_a:.1%}"],
            textposition="outside",
            textfont=dict(size=14, color=INK),
        ))
        fig_bar.add_hline(
            y=0.65, line_dash="dash", line_color="black", line_width=2,
            annotation_text="Covenant 65%", annotation_position="top right",
        )
        fig_bar.update_layout(
            height=350,
            yaxis=dict(tickformat=".0%", range=[0, max(ltv_a, 0.80) + 0.10]),
            margin=dict(l=20, r=20, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("##### Narrative")
    st.info(fund.get("narrative_for_demo", "—"))


# ---------------------------------------------------------------------------
# TAB 3 — Compare Funds
# ---------------------------------------------------------------------------

with tab_compare:
    rows = []
    for f in funds:
        w = f["sub_sector_weights"]
        fac_b = Facility(nav_initial_musd=f["size_musd"],
                         facility_size_musd=f["facility_size_musd_benign"])
        fac_a = Facility(nav_initial_musd=f["size_musd"],
                         facility_size_musd=f["facility_size_musd_aggressive"])
        rows.append({
            "id": f["id"],
            "name": f["name"],
            "drawdown": portfolio_drawdown(w),
            "ltv_b": stressed_ltv(w, fac_b),
            "ltv_a": stressed_ltv(w, fac_a),
        })

    # Comparison bar chart
    st.markdown("##### Stressed LTV by fund and facility regime")
    fig = make_subplots(rows=1, cols=2,
                        column_widths=[0.65, 0.35],
                        subplot_titles=("Stressed LTV  (hatched = covenant breach)",
                                        "Portfolio drawdown"))

    y_labels = [r["id"] for r in rows]
    benign = [r["ltv_b"] for r in rows]
    aggro = [r["ltv_a"] for r in rows]
    dds = [r["drawdown"] for r in rows]

    # Left: stressed LTV bars
    fig.add_trace(go.Bar(
        y=y_labels, x=benign, orientation="h",
        name="Benign facility", marker_color=OK,
        text=[f"{v:.0%}" for v in benign], textposition="outside",
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        y=y_labels, x=aggro, orientation="h",
        name="Aggressive facility",
        marker=dict(
            color=[BAD if v > 0.65 else WARN for v in aggro],
            pattern=dict(
                shape=["x" if v > 0.65 else "" for v in aggro],
                bgcolor=[BAD if v > 0.65 else WARN for v in aggro],
                fgcolor="white",
            ),
        ),
        text=[f"{v:.0%}{'  BREACH' if v>0.65 else ''}" for v in aggro],
        textposition="outside",
    ), row=1, col=1)
    fig.add_vline(x=0.65, line_dash="dash", line_color="black", line_width=2,
                  row=1, col=1,
                  annotation_text="Covenant 65%", annotation_position="top")

    # Right: drawdown
    fig.add_trace(go.Bar(
        y=y_labels, x=[-d * 100 for d in dds], orientation="h",
        marker_color=[
            BAD if d <= -0.25 else WARN if d <= -0.18 else OK for d in dds
        ],
        text=[f"{d:.1%}" for d in dds], textposition="outside",
        showlegend=False,
    ), row=1, col=2)

    fig.update_xaxes(tickformat=".0%", title_text="Stressed LTV",
                     range=[0, max(aggro) + 0.18], row=1, col=1)
    fig.update_xaxes(ticksuffix="%", title_text="NAV drawdown under stress",
                     row=1, col=2)
    fig.update_yaxes(autorange="reversed", row=1, col=1)
    fig.update_yaxes(autorange="reversed", row=1, col=2)
    fig.update_layout(height=110 + 70 * len(rows),
                      barmode="group", legend=dict(orientation="h", y=-0.15),
                      margin=dict(l=10, r=10, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # Sortable table
    st.markdown("##### Detailed table")
    import pandas as pd
    df = pd.DataFrame(rows).rename(columns={
        "id": "ID", "name": "Fund",
        "drawdown": "Drawdown",
        "ltv_b": "LTV @ benign", "ltv_a": "LTV @ aggressive",
    })
    df["Drawdown"] = df["Drawdown"].map(lambda v: f"{v:.1%}")
    df["LTV @ benign"] = df["LTV @ benign"].map(lambda v: f"{v:.1%}")
    df["LTV @ aggressive"] = df["LTV @ aggressive"].map(
        lambda v: f"{v:.1%}  ⚠️" if v > 0.65 else f"{v:.1%}"
    )
    st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# TAB 4 — Stress Lab
# ---------------------------------------------------------------------------

with tab_stress:
    st.markdown(
        "Adjust the **sub-sector stress assumptions** and **facility sizing** "
        "below. The heatmap on the right shows the stressed LTV across all "
        "feasible (EV exposure × Data-center exposure) combinations for a "
        "$500M reference fund. Watch the covenant contour shift as you tweak."
    )

    left, right = st.columns([1, 2])

    with left:
        st.markdown("##### Sub-sector stress assumptions")
        st.caption("Negative = drawdown. Default: −35% / −10% / −30% / −10%")
        stress = {}
        stress["ev_powertrain"] = st.slider(
            "EV powertrain stress (%)",
            min_value=-70, max_value=0, value=-35, step=1,
        ) / 100
        stress["data_center_power"] = st.slider(
            "Data-center power stress (%)",
            min_value=-50, max_value=0, value=-10, step=1,
        ) / 100
        stress["renewable_power"] = st.slider(
            "Renewable power stress (%)",
            min_value=-70, max_value=0, value=-30, step=1,
        ) / 100
        stress["industrial_drives"] = st.slider(
            "Industrial drives stress (%)",
            min_value=-50, max_value=0, value=-10, step=1,
        ) / 100

        st.markdown("##### Facility")
        nav = st.number_input("Fund NAV (USD M)", min_value=100, max_value=5000,
                              value=500, step=50)
        facility_size = st.number_input(
            "Facility size (USD M)", min_value=10, max_value=int(nav),
            value=int(nav * 0.40), step=10,
            help="Initial LTV = facility size / NAV",
        )
        covenant = st.slider("Covenant LTV (%)", min_value=40, max_value=90,
                             value=65, step=1) / 100

        st.metric("Initial LTV", f"{facility_size/nav:.1%}")

    with right:
        # Apply the slider-overridden stress to the model
        import nav_stress_model as nsm
        original_stress = nsm.SECTOR_STRESS
        try:
            nsm.SECTOR_STRESS = stress
            fac = Facility(nav_initial_musd=nav,
                           facility_size_musd=facility_size,
                           covenant_ltv=covenant)
            ev_axis, dc_axis, ltv_grid = sweep_ltv_grid(fac, grid_points=41)
        finally:
            nsm.SECTOR_STRESS = original_stress

        # Plotly heatmap
        fig = go.Figure()

        # Build a mask: NaN cells (infeasible) become grey
        z = np.where(np.isnan(ltv_grid.T), None, ltv_grid.T)
        fig.add_trace(go.Heatmap(
            x=ev_axis, y=dc_axis,
            z=ltv_grid.T,
            colorscale=[
                [0.0, OK], [0.25, "#9bd17a"], [0.50, "#fbf17c"],
                [0.75, "#f7a35c"], [1.0, BAD],
            ],
            zmin=max(0.20, covenant - 0.40),
            zmax=min(1.0,  covenant + 0.30),
            colorbar=dict(title="Stressed LTV", tickformat=".0%"),
            hovertemplate=(
                "EV: %{x:.0%}<br>DC: %{y:.0%}<br>"
                "Stressed LTV: %{z:.1%}<extra></extra>"
            ),
        ))

        # Covenant breach contour
        if np.nanmax(ltv_grid) > covenant:
            fig.add_trace(go.Contour(
                x=ev_axis, y=dc_axis, z=ltv_grid.T,
                contours=dict(start=covenant, end=covenant, size=0.001,
                              showlabels=True),
                line=dict(color="black", width=3, dash="dash"),
                showscale=False,
                contours_coloring="none",
                hoverinfo="skip",
            ))

        fig.update_layout(
            height=540,
            xaxis=dict(title="EV powertrain exposure", tickformat=".0%",
                       range=[0, 1]),
            yaxis=dict(title="Data-center power exposure", tickformat=".0%",
                       range=[0, 1]),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Three reference points
        c1, c2, c3 = st.columns(3)
        for col, label, w in zip(
            [c1, c2, c3],
            ["100% EV", "100% Data-center", "Diversified (25/25/25/25)"],
            [
                {"ev_powertrain": 1.0, "data_center_power": 0.0,
                 "renewable_power": 0.0, "industrial_drives": 0.0},
                {"ev_powertrain": 0.0, "data_center_power": 1.0,
                 "renewable_power": 0.0, "industrial_drives": 0.0},
                {k: 0.25 for k in SECTOR_LABELS},
            ],
        ):
            try:
                nsm.SECTOR_STRESS = stress
                v = stressed_ltv(w, fac)
            finally:
                nsm.SECTOR_STRESS = original_stress
            col.metric(
                label, f"{v:.1%}",
                delta="BREACH" if v > covenant
                else f"{(covenant-v)*100:.1f}pp inside",
                delta_color="inverse" if v > covenant else "normal",
            )


# ===========================================================================
# Footer
# ===========================================================================

st.markdown("---")
st.markdown(
    f'<p style="color:{INK_SOFT};font-size:0.8rem;text-align:center;">'
    'UniCredit Fund Financing  ·  First Look  ·  Jiawen Cc  ·  '
    'Polimi EE M.Sc.  ·  June 2026  ·  '
    'Built with Streamlit + Plotly  ·  Source: this folder'
    '</p>',
    unsafe_allow_html=True,
)
