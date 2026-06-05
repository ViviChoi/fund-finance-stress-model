# Operations Guide

> Step-by-step instructions for setting up, running, and modifying
> this project. Time to first artefact: ~30 seconds (Mac, venv
> already cached) or ~2 minutes (first-time, any OS).

---

## Two equivalent command paths

The project produces **bit-identical** outputs on either path
(verified via SHA-256 across macOS Apple-Silicon and Windows ARM64).

### Mac / Linux path (bash + make)

```
./setup.sh           # one-time
make all             # rebuild figures + demo + deck
make test            # run the test suite
make demo            # 5-fund demo only
make serve           # launch the WebUI on localhost:8501
make clean           # remove generated outputs
```

### Universal path (Python only — works on Windows too)

```
python dev.py setup       # one-time
python dev.py all         # rebuild figures + demo + deck
python dev.py test        # run the test suite
python dev.py demo        # 5-fund demo only
python dev.py serve       # launch the WebUI on localhost:8501
python dev.py clean       # remove generated outputs
```

On Windows, you can shorten to `dev.cmd setup` / `dev.cmd all` / etc.

---

## Setup

### Mac / Linux

```
$ cd UniCredit-FundFinancing-Application
$ ./setup.sh
```

### Windows (PowerShell or cmd)

```
> cd UniCredit-FundFinancing-Application
> python dev.py setup
```

What this does: creates `.venv/` with an isolated Python environment,
installs **core dependencies** (numpy, pandas, matplotlib, python-pptx,
pytest), then attempts **WebUI dependencies** (streamlit, plotly) on a
best-effort basis. If streamlit fails to install (this is normal on
Windows ARM64), the model, tests, deck builder, and CLI demo still
work — only the WebUI tab is unavailable.

Expected output ends with:
```
✓  Setup complete.
```

---

## Running the tests (recommended after any edit)

### Mac / Linux

```
$ make test
```

### Windows

```
> python dev.py test
```

You should see **29 passed** (Mac) or **28 passed, 1 skipped** (Windows
ARM64 — the skipped test is the WebUI import smoke test).

The tests catch regressions in two ways:
- **Behavioural tests** (e.g. "EV stress must be the worst sub-sector")
  catch accidental edits to `SECTOR_STRESS`.
- **Documented-finding tests** (e.g. "100% EV at 30% LTV equals 46.2%")
  lock the exact numbers cited in the deck and the write-up.

---

## Launching the WebUI

### Easiest — double-click

* **Mac**: double-click `启动WebUI.command` in Finder
* **Windows**: double-click `启动WebUI.bat` in Explorer

Both launchers auto-detect Python, bootstrap the venv if missing,
launch Streamlit, and open your default browser to
http://localhost:8501.

> ⚠️ **macOS first-time prompt**: macOS may say "cannot verify
> developer". Right-click → **Open** → **Open anyway**. Subsequent
> double-clicks work normally.

### From the command line

```
make serve            # Mac / Linux
python dev.py serve   # any OS
```

Then open `http://localhost:8501` in any browser.

To stop the server: **Ctrl+C** in the terminal, or simply close the
window.

### The four WebUI tabs

1. **Overview** — dataset summary and the methodology in three claims.
2. **Fund Explorer** — pick any fund from the active dataset, see its
   sub-sector exposure as a pie chart, stressed LTV under benign vs
   aggressive facility sizing, and the fund's strategy narrative.
3. **Compare Funds** — side-by-side bars for every fund in the
   dataset, with covenant-breach hatching and a sortable table.
4. **Stress Lab** — adjust sub-sector stress assumptions and facility
   sizing with sliders. The covenant-breach contour on the LTV
   heatmap updates live.

The sidebar lets you switch between the bundled datasets (`Demo (5
realistic PE funds)`, `Edge cases (8 boundary funds)`) or upload your
own JSON.

---

## Running the CLI demo

```
# Default dataset
make demo                                        # Mac / Linux
python dev.py demo                               # any OS

# Custom dataset
python code/demo_runner.py --data path/to/your-funds.json --out path/to/comparison.png
python code/demo_runner.py --help                # all flags
```

This prints a table of stressed LTVs per fund, a per-fund talking-point
narrative, and saves a comparison chart PNG to `figures/`.

---

## File map

| Path | Purpose |
|---|---|
| `app.py` | Streamlit WebUI entry point |
| `code/nav_stress_model.py` | The stress model itself |
| `code/sector_matrix.py` | Generates the sub-sector matrix figure |
| `code/build_deck.py` | Generates the 13-slide pptx |
| `code/demo_runner.py` | CLI runner over JSON fund datasets |
| `code/pseudocode.md` | Plain-English walk-through of the model logic |
| `code/requirements.txt` | Core dependencies (always installable) |
| `code/requirements-webui.txt` | WebUI dependencies (best-effort) |
| `content/01-page-content.md` | Full methodology write-up |
| `data/example_funds.json` | 5 realistic PE fund profiles |
| `data/edge_cases.json` | 8 boundary-condition test funds |
| `figures/` | Pre-rendered PNG outputs |
| `slides/` | Generated pptx deck |
| `tests/test_model.py` | 29 pytest assertions |
| `setup.sh` / `Makefile` | Mac / Linux task runner |
| `dev.py` / `dev.cmd` | Cross-platform task runner |
| `启动WebUI.command` / `启动WebUI.bat` | Double-click launchers |

---

## FAQ

### How do I edit a stress assumption and see the new result?

Mac / Linux:
```
$ make demo      # for the 5-fund comparison
$ make all       # for the entire deck rebuild
$ make test      # confirm nothing broke
```

Windows:
```
> python dev.py demo
> python dev.py all
> python dev.py test
```

**Always run `test` after editing model code.** If a test fails, a
documented number cited in the write-up or deck no longer matches the
model — fix the discrepancy before sharing.

### The deck looks low-resolution in macOS Preview.

Preview only shows a thumbnail. Open it in Keynote (free in the App
Store) or upload to Google Slides for the real rendering. The deck is
built for 16:9 widescreen with no animations.

### How do I share this folder with someone else?

Don't send `.venv/` — it's platform-specific and ~190 MB. The
`.gitignore` excludes it by default. On the receiving end:

```
./setup.sh                 # Mac / Linux
python dev.py setup        # any OS
```

### How do I put this in git / GitHub?

```
$ git init
$ git add .
$ git commit -m "Initial commit"
$ git remote add origin <your-repo-url>
$ git push -u origin main
```

The `.gitignore` keeps the venv and Python cache out automatically.
Generated figures and the deck are kept under version control so a
reader of the repo can see them without running setup first.

### I screwed up something and want to start over.

```
make distclean        # Mac / Linux — removes venv + outputs
python dev.py clean   # any OS — outputs only
```

Then re-run setup. All source files are untouched.

### Running on Windows for the first time?

1. **Boot Windows**, then open PowerShell.
2. **Check Python**: `python --version` should be 3.10+. If not,
   install from python.org with "Add to PATH" checked.
3. **Setup**: `python dev.py setup`. First-time installs of numpy /
   pandas / matplotlib can take 2–3 minutes on Windows; some wheels
   build from source.
4. **Verify**: `python dev.py test`. Should print `28 passed, 1
   skipped` on ARM64 Windows or `29 passed` on x64.
5. **Launch**: `python dev.py serve` (or double-click `启动WebUI.bat`).

If the WebUI install failed (common on ARM64 Windows due to pyarrow /
httptools wheels not being prebuilt), the model and deck still work.
Use the Mac path for the WebUI demo, or install Visual C++ Build Tools
on Windows and re-run setup.

### The tests fail. What do I do?

1. Read the failing test name. It tells you what assumption broke.
2. If you intentionally changed the model (e.g. tweaked a stress
   number), update the corresponding test in
   `tests/test_model.py::TestDocumentedFindings`.
3. If you didn't change anything, you've found a bug — most likely in
   a recent edit. `git diff` to see what changed.
4. **Never share artefacts from a folder where tests fail** — it's
   the surest sign something is silently inconsistent.

---

*Tested on macOS (Apple Silicon, Python 3.14) and Windows 11 ARM64
(Python 3.13).*
