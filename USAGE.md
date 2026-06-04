# How to use this package — sequential guide

> Read this top to bottom **once**, then come back as a reference.
> Time to first action: about 10 minutes.
>
> The project works on **macOS, Linux, and Windows**. There are two
> equivalent command paths — pick the one for your OS.

---

## Two equivalent command paths — pick one

The project produces **bit-identical** outputs on either path (verified
via SHA256 in a clean-room test on macOS).

### Mac / Linux path (uses bash + make)

```
./setup.sh           # one-time
make all             # rebuild figures + demo + deck
make test            # run the test suite
make demo            # 5-fund demo only
make serve           # ⭐ launch the WebUI on localhost:8501
make clean           # remove generated outputs
```

### Universal path (Python only — works on Windows too)

```
python dev.py setup       # one-time
python dev.py all         # rebuild figures + demo + deck
python dev.py test        # run the test suite
python dev.py demo        # 5-fund demo only
python dev.py serve       # ⭐ launch the WebUI on localhost:8501
python dev.py clean       # remove generated outputs
```

On Windows, you can shorten to `dev.cmd setup` / `dev.cmd all` / etc.

**Both paths use the same Python code under the hood** — `make all`
just calls the same `.venv/bin/python ...` commands that `dev.py all`
does. Pick whichever you find more natural.

---

## Step 0 — Open the folder

### macOS / Linux

```
$ cd ~/Desktop/UniCredit-FundFinancing-Application
$ ls
```

### Windows (PowerShell or cmd)

```
> cd %USERPROFILE%\Desktop\UniCredit-FundFinancing-Application
> dir
```

You should see: `README.md`, `USAGE.md`, `setup.sh`, `Makefile`,
`dev.py`, `dev.cmd`, `code/`, `content/`, `data/`, `figures/`,
`slides/`, `tests/`.

---

## Step 1 — One-time setup (~30 seconds)

### macOS / Linux

```
$ ./setup.sh
```

### Windows

```
> python dev.py setup
```
(or `> dev.cmd setup` — the `.cmd` file just calls `python dev.py`.)

**What this does** (both paths): creates a `.venv/` folder with an
isolated Python environment, installs numpy / pandas / matplotlib /
python-pptx / pytest.

Expected output ends with:
```
✓  Setup complete.
```

If you ever move this folder to another machine, **just re-run the
setup command on that machine** — that's the only first-time step.

---

## Step 2 — Regenerate everything (~5 seconds)

### macOS / Linux

```
$ make all
```

### Windows

```
> python dev.py all
```

This rebuilds:
- `figures/sector_matrix.png` — Section 2 sub-sector matrix
- `figures/nav_ltv_heatmap.png` — Section 3 dual-panel heatmap
- `figures/fund_comparison.png` — 5-fund demo chart
- `slides/UniCredit-FirstLook-Deck.pptx` — 12-slide deck

You don't need to do this unless you've edited code or data — every
artefact is pre-built when you first see this folder.

---

## Step 2½ — Run the tests (recommended before any demo)

### macOS / Linux

```
$ make test     # or: ./.venv/bin/python -m pytest tests/ -v
```

### Windows

```
> python dev.py test
```

You should see **26 passed**. If any test fails, **don't go into the
demo with broken assumptions** — read the failing test, figure out
what changed, fix the model or fix the test, then re-run.

The tests catch regressions in two ways:
- **Behavioural tests** (e.g. EV stress must be the worst) catch
  accidental edits to `SECTOR_STRESS`.
- **Documented-finding tests** (e.g. "100% EV at 30% LTV = 46.2%")
  lock the exact numbers cited in the page and the deck — so if you
  change the model, the page/deck will silently disagree with the
  test, and the test will fail loudly.

---

## Step 3 — Understand what's in the folder

| Folder       | What's in it                            | When you open it             |
|--------------|-----------------------------------------|-------------------------------|
| `content/`   | All the writing you'll send / present   | When preparing what to say   |
| `code/`      | Python source + pseudocode walkthrough  | When learning the model      |
| `figures/`   | Pre-built PNGs                          | When you need to show one    |
| `slides/`    | The pptx deck                           | When demo-ing live           |
| `data/`      | JSON with 5 example funds               | When tweaking the demo       |

**Open `content/` first.** Read the files in order — they're numbered
01, 02, 03, 04, 05.

---

## Step 4 — Read the materials in this order

For your own learning (do this **before** sending the DM):

1. **`content/01-page-content.md`** — the actual outreach page. Read
   it like the recipient would.
2. **`code/pseudocode.md`** — the logic walkthrough. Don't open the
   .py code first; read this instead.
3. **`content/03-interview-qa.md`** — 13 Q&A pairs. Read all of them.
4. **`content/04-mock-interview.md`** — three-round mock. Run it
   **out loud**, with a timer, the day before any call.
5. **`content/05-demo-walkthrough.md`** — only relevant if you get a
   screen-share call.

Total reading time: ~60 minutes. Mock interview practice: another
~35 minutes if you do all three rounds.

---

## Step 5 — Send the DM

1. Open `content/02-linkedin-dm.md`.
2. Pick **Version A** (the longer one).
3. Replace `[LINK]` with your published Notion page URL.
   - To publish: see **Step 6** below.
4. Replace `[your LinkedIn URL]` with your own LinkedIn profile URL.
5. Copy → paste into LinkedIn DM → send to Rossella Guainai Ricci.

**Don't send without doing Step 6 first** — the link must work.

---

## Step 6 — Publish the page (Notion route, fastest)

1. Open Notion → create a new page → "Public" → "Anyone with the
   link".
2. Open `content/01-page-content.md` in a text editor.
3. Copy everything → paste into the new Notion page (Notion
   auto-converts markdown).
4. The two `![...]` image references won't auto-resolve. Drag
   `figures/sector_matrix.png` and `figures/nav_ltv_heatmap.png`
   into the page where the references are.
5. Click "Share" → copy public link.
6. Test the link in an **incognito browser window** — confirm it
   opens without asking for login, confirm both images show up.

That URL goes into the `[LINK]` slot in the DM.

---

## Step 6½ — Launch the WebUI (recommended for live demos)

### Mac
```
$ make serve
```

### Windows
```
> python dev.py serve
```

Then open **http://localhost:8501** in any browser. The WebUI has four
tabs:

1. **Overview** — the elevator-pitch claims and dataset stats.
2. **Fund Explorer** — pick a fund, see its weights as a pie chart,
   stressed LTV at both regimes vs covenant.
3. **Compare Funds** — side-by-side bars + sortable table.
4. **Stress Lab** — **the killer demo tab**. Sliders for sub-sector
   stress assumptions and facility sizing. Live-updating heatmap.

**For tomorrow's demo, this is what you screen-share** instead of (or
in addition to) the pptx. Rossella can ask "what if EV is −50% not
−35%?" and you drag the slider live. The covenant contour shifts in
real time.

**File upload**: the sidebar has an "Upload your own" option — Rossella
could in principle paste in a fund profile in JSON and see results
on her own portfolio. Don't push this too hard; the headline is
"play with the model live", not "upload your data".

To stop the server: **Ctrl+C** in the terminal.

---

## Step 7 — Prep for a call (when it happens)

If Rossella replies and offers a call (could be 1 day later, could
be 2 weeks):

1. **Day before**: run mock interview (`content/04-mock-interview.md`).
   Out loud. With a timer.
2. **Morning of**: glance at `code/pseudocode.md §5` ("Two-minute
   explain the code script") and the Wolfspeed + Vertiv 2024-2026
   charts on Yahoo Finance.
3. **30 minutes before**: run `make demo` to refresh the demo
   talking points and have `figures/fund_comparison.png` open.
4. **5 minutes before**: water, headset, full charge.

---

## Step 8 — During the call, if she asks "can you show me the model"

Read `content/05-demo-walkthrough.md` once **the day before**.
During the call:

1. Share screen, open `figures/fund_comparison.png`.
2. Follow the 4-minute script in section "Suggested live flow".
3. If she asks to change parameters, edit `data/example_funds.json`,
   save, run `make demo` in Terminal, re-open the new PNG.

---

## Step 9 — After the call

Send the short follow-up from `content/04-mock-interview.md`
section "After the call". Within 4 hours of the call ending.

---

## Where everything fits — quick reference

| You want to…                              | Open this                                  |
|-------------------------------------------|--------------------------------------------|
| **Launch the interactive WebUI** ⭐        | `make serve`  /  `python dev.py serve`     |
| See the public page (what Rossella sees)  | `content/01-page-content.md`               |
| Read the DM                               | `content/02-linkedin-dm.md`                |
| Prep for interview Q&A                    | `content/03-interview-qa.md`               |
| Run a mock interview alone                | `content/04-mock-interview.md`             |
| Prep for the live model demo              | `content/05-demo-walkthrough.md`           |
| Understand the model logic                | `code/pseudocode.md`                       |
| Read the actual code                      | `code/nav_stress_model.py`                 |
| Tweak the demo funds                      | `data/example_funds.json`                  |
| Use boundary / edge-case funds for debug  | `data/edge_cases.json`                     |
| Run demo with custom dataset              | `python code/demo_runner.py --data path.json` |
| Use the deck for screen-share             | `slides/UniCredit-FirstLook-Deck.pptx`     |
| Regenerate everything after an edit       | `make all`  /  `python dev.py all`         |
| Run the test suite                        | `make test` /  `python dev.py test`        |
| Reset to clean state                      | `make clean` (or `make distclean`)         |

---

## Common questions

### Q. I edited a stress number / a weight — how do I see the result?

Mac / Linux:
```
$ make demo      # for the 5-fund comparison
$ make all       # for the entire deck rebuild
$ make test      # check nothing broke
```

Windows:
```
> python dev.py demo
> python dev.py all
> python dev.py test
```

**Always run `test` after editing model code**. If the test suite
fails, it likely means a documented number cited in the page or deck
no longer matches the model — fix the discrepancy before publishing.

### Q. The deck looks ugly when I open it in macOS Preview.

Preview only shows a thumbnail. Open it in Keynote (free in App
Store) or upload to Google Slides for the real rendering. The deck
is built for 16:9 wide-screen, no animations.

### Q. I want to send this folder to a friend / collaborator.

Don't send `.venv/` — it's Mac-arm64-specific and 187 MB. The
`.gitignore` already excludes it; if you zip the folder manually,
`exclude .venv` first.

On the other end, they run `./setup.sh` and `make all`. Same result.

### Q. I want this in git / GitHub.

```
$ git init
$ git add .
$ git commit -m "first look: power-electronics risk lens on NAV facilities"
$ git remote add origin git@github.com:YOUR_USER/unicredit-first-look.git
$ git push -u origin main
```

The `.gitignore` keeps the venv out automatically. Generated figures
are kept under version control so a reader of the repo can see them
without running setup.

### Q. I want to use this on Windows for tomorrow's demo.

Two options:

1. **Local Python on Windows** (recommended if you already have
   Python 3.10+ installed):
   ```
   > python dev.py setup
   > python dev.py all
   > python dev.py test
   ```
   That's it. The `dev.py` runner handles Windows-specific paths
   (`.venv\Scripts\python.exe` vs `.venv/bin/python`) automatically.

2. **Mac stays primary** (if your Windows VM doesn't have Python):
   Just present from Mac. The folder is portable — `setup.sh` on Mac,
   `dev.py setup` on Windows; both work from the same source files.

**Note on cross-platform testing**: the Mac path has been verified
end-to-end with SHA256-identical output reproducibility (see test
log). The Windows path uses the same Python code via `dev.py`, so it
**should** behave identically. If something breaks on Windows, the
first thing to check is whether `python --version` reports 3.10+.

### Q. The tests fail — what do I do?

1. Read the failing test name. It tells you what assumption broke.
2. If you intentionally changed the model (e.g. tweaked a stress
   number), update the corresponding test in
   `tests/test_model.py::TestDocumentedFindings` to match.
3. If you didn't change anything, you've found a bug — most likely
   in a recent edit. `git diff` to see what changed; revert if you
   can't fix.
4. **Never present from a folder where tests fail.** It's the
   surest sign something is silently inconsistent.

### Q. Can I delete the venv?

Yes. `make distclean` removes it. To restore: `./setup.sh`.

### Q. I screwed up some content file and want to start over.

You haven't lost anything — everything in `content/` is plain
markdown you've already read here. Re-edit by hand. The Python
generates `figures/` and `slides/`; the writing is human-authored
and not regenerable.
