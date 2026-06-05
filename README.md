# Power-Electronics Risk Lens on NAV Facilities

[![Live demo](https://img.shields.io/badge/🚀_Live_demo-Hugging_Face_Spaces-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/spaces/ChoiVivi/fund-finance-stress-model)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **🚀 Try it live (no install, no login):** [huggingface.co/spaces/ChoiVivi/fund-finance-stress-model](https://huggingface.co/spaces/ChoiVivi/fund-finance-stress-model)
>
> A small, opinionated NAV facility stress model that decomposes a
> power-electronics PE fund into its underlying sub-sectors (EV
> powertrain, data-center power, renewables, industrial drives) and
> shows how stressed LTV behaves under sector-specific shocks.
>
> Ships with an interactive Streamlit WebUI, a 13-slide presentation
> deck, a CLI demo runner over multiple example funds, and a 29-test
> pytest suite. Tested on macOS and Windows ARM64.

---

## Quickstart

### Mac / Linux

```bash
./setup.sh           # one-time: creates .venv and installs deps
make all             # rebuild figures + demo + deck
make test            # 29 sanity tests
make serve           # launch the WebUI on localhost:8501
```

Or **double-click** `启动WebUI.command` in Finder — it auto-detects
Python, bootstraps the venv if missing, and opens your browser.

### Windows

```cmd
python dev.py setup
python dev.py all
python dev.py test
python dev.py serve
```

Or **double-click** `启动WebUI.bat`.

---

## What you get

| Artefact | What it is |
|---|---|
| `app.py` | Streamlit WebUI — four tabs (Overview / Fund Explorer / Compare / Stress Lab) |
| `code/nav_stress_model.py` | The core stress model (~300 lines) |
| `code/demo_runner.py` | Runs the model over a JSON dataset of fund profiles |
| `code/build_deck.py` | Generates the 13-slide pptx from source |
| `code/sector_matrix.py` | Generates the sub-sector risk-matrix figure |
| `data/example_funds.json` | 5 hypothetical PE fund profiles |
| `data/edge_cases.json` | 8 boundary-condition test funds |
| `figures/` | Pre-rendered PNG outputs |
| `slides/Fund-Finance-Stress-Model-Deck.pptx` | Presentation deck (16:9, 13 slides) |
| `content/01-page-content.md` | Long-form write-up of the methodology and results |
| `tests/test_model.py` | 29 pytest assertions including documented-finding regressions |

---

## Folder layout

```
.
├── README.md / LICENSE
├── 启动WebUI.command / 启动WebUI.bat   ← double-click launchers
├── setup.sh / Makefile / dev.py / dev.cmd
├── app.py                              ← Streamlit WebUI
├── code/                               ← Python source
├── content/01-page-content.md          ← methodology write-up
├── data/                               ← fund JSON datasets
├── figures/                            ← pre-rendered PNGs
├── slides/                             ← .pptx deck
└── tests/                              ← 29 pytest assertions
```

---

## Methodology — one paragraph

NAV facilities lend against the net asset value of a private-equity
fund's portfolio. When the fund is concentrated in a single industry
label (e.g. *power electronics*), traditional single-sector haircuts
can mis-price the risk — because the label often hides multiple credit
profiles with very different cyclicality. This model decomposes "power
electronics" into four sub-sectors (EV powertrain, data-center power,
renewables, industrial drives), applies sector-specific stress
drawdowns calibrated to 2024–2026 listed-comparable behaviour, and
shows the resulting LTV surface as the portfolio mix and facility
sizing vary.

The model is a *first look*, not a production pricing engine. See
`content/01-page-content.md` for the full write-up, including
limitations and a sketch of how the same decomposition reflex extends
to semiconductors, medical devices, and grid modernisation.

---

## Reproducing the artefacts

Verified bit-for-bit reproducible across Mac Apple-Silicon and Windows
ARM64: all three PNG figures have identical SHA-256 hashes on both
platforms.

```bash
make clean        # remove generated outputs (keeps venv)
make all          # rebuild
make test         # 29 passed (or 28 passed + 1 skipped on Win ARM64
                  # where streamlit's pyarrow wheel isn't prebuilt)
```

The skipped test on Windows ARM64 is the WebUI import smoke test;
the model, deck, demo runner, and CLI all work without streamlit.

---

## Live-tweaking during a discussion

The Streamlit WebUI's **Stress Lab** tab exposes sliders for each
sub-sector's stress assumption and for facility sizing. The
covenant-breach contour on the heatmap updates in real time as you
drag. To swap the fund dataset, use the sidebar's "Upload your own"
option with a JSON file matching the schema in `data/example_funds.json`.

---

## Licence

Released under the **MIT License** — see [`LICENSE`](LICENSE).
Commercial use, modification, and redistribution are permitted with
attribution. All numerical assumptions are illustrative and nothing in
this repository constitutes financial advice.

---

*Built June 2026. Honest about scope, deliberate about depth.*
