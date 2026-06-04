# UniCredit Fund Financing — Application Package

> **What this is.** A self-contained deliverable for a cold-outreach
> LinkedIn DM to UniCredit HR about a fund-financing-focused trader
> seat. Positions the applicant — an EE M.Sc. student at Politecnico
> di Milano — as the *one engineer* who can decompose power-electronics
> exposures at the depth a 2026 NAV-facility desk needs.
>
> **What this is not.** A production model, a credit memo, or an
> investment recommendation. Numbers are illustrative.

---

## How to use this package — in order

1. **Read** `content/01-page-content.md` — this is the page that
   becomes the public deliverable (Notion / GitHub Pages).
2. **Run the code** (see "Reproducing the figures" below). Confirm the
   two PNGs match the ones already committed in `figures/`.
3. **Internalise** `code/pseudocode.md` — read it twice. Goal: be
   able to describe the model architecture in 90 seconds without
   looking at the screen.
4. **Drill** `content/03-interview-qa.md` — 13 Q&A pairs covering
   the model, your background, and curveballs. Prepare answers in
   your own voice.
5. **Pressure-test** with `content/04-mock-interview.md` — run
   yourself through it out loud, with a timer, ideally the day
   *before* the real call. Don't skip the out-loud rule.
6. **Publish** the page (see "Publishing" below) and capture the URL.
7. **Send** the LinkedIn DM from `content/02-linkedin-dm.md`
   (already addressed to Rossella Guainai Ricci), with the URL and
   your LinkedIn profile substituted in.

---

## File map

```
.
├── README.md                          ← you are here
├── USAGE.md                           ← step-by-step how-to
├── setup.sh                           ← Mac/Linux bootstrap script
├── Makefile                           ← Mac/Linux task runner (`make all`)
├── dev.py                             ← cross-platform task runner (Win/Mac/Linux)
├── dev.cmd                            ← Windows convenience wrapper for dev.py
├── .gitignore                         ← keeps venv / cache out of version control
├── .venv/                             ← local Python env (gitignored, recreated by setup)
├── app.py                             ← ⭐ Streamlit WebUI (interactive demo)
├── code/
│   ├── nav_stress_model.py            ← Section 3 model (runnable)
│   ├── sector_matrix.py               ← Section 2 figure script
│   ├── build_deck.py                  ← pptx generator
│   ├── demo_runner.py                 ← 5-fund demo runner (--data flag for swap)
│   ├── pseudocode.md                  ← logic walkthrough + defence notes
│   └── requirements.txt
├── data/
│   ├── example_funds.json             ← 5 hypothetical PE fund profiles for demo
│   └── edge_cases.json                ← 8 boundary-condition funds for debug
├── tests/
│   ├── test_model.py                  ← 26 pytest sanity + regression checks
│   └── conftest.py                    ← pytest configuration
├── content/
│   ├── 01-page-content.md             ← full page markdown — paste to Notion / GH Pages
│   ├── 02-linkedin-dm.md              ← cold DM (to Rossella) + design notes + reply protocols
│   ├── 03-interview-qa.md             ← 13 anticipated questions, answers, tactics
│   ├── 04-mock-interview.md           ← 3-round self-administered pressure test
│   └── 05-demo-walkthrough.md         ← live screen-share demo script (5-fund walkthrough)
├── figures/
│   ├── nav_ltv_heatmap.png            ← Section 3 main visual (dual-panel)
│   ├── sector_matrix.png              ← Section 2 main visual
│   └── fund_comparison.png            ← 5-fund demo chart
└── slides/
    └── UniCredit-FirstLook-Deck.pptx  ← 12-slide presentation (16:9)
```

---

## Reproducing the artefacts

On any machine with Python 3.10+, from this directory:

**Mac / Linux**:
```bash
./setup.sh          # one-time: creates .venv and installs deps
make all            # regenerate figures + demo + deck
make test           # 29 sanity tests — should all pass
make serve          # ⭐ launch the WebUI on localhost:8501
```

**Windows** (or any OS — universal path):
```cmd
python dev.py setup
python dev.py all
python dev.py test
python dev.py serve
```

Both paths produce bit-identical outputs (verified via SHA256 in
clean-room reproduction on Mac; Windows path uses the same Python
code via `dev.py`, so it should behave identically — see USAGE.md
for the Win quick-test).

### Granular targets

```bash
make figures    # PNGs only (sector_matrix + nav_ltv_heatmap)
make deck       # pptx (depends on figures)
make clean      # remove generated outputs, keep the venv
make distclean  # also remove the venv
```

`make` is idempotent and dependency-aware: editing `nav_stress_model.py`
will rebuild only the heatmap (not the matrix) and trigger a deck
rebuild because the deck depends on the figure.

### Live tweaking for an interview

If a banker asks "what if EV stress is −50% instead of −35%?":

1. Edit `SECTOR_STRESS` in `code/nav_stress_model.py` (~line 80).
2. `make all`
3. Open the regenerated heatmap or pptx — covenant contour visibly shifts.

End-to-end re-run < 5 seconds.

### Portability test

Tested clean on a fresh `mktemp -d` copy:
`./setup.sh` → `make all` produces identical artefacts. If you move
this folder to another Mac, those two commands are all you need.

---

## Publishing

### Presentation deck

`slides/UniCredit-FirstLook-Deck.pptx` is a 12-slide widescreen
(16:9) banking-style deck covering the same argument as the page,
in presentation form. Use it for:

1. **Self-study**: open it and click through to internalise the
   narrative arc before the call. Slides 1→12 are the exact order
   you'd walk a banker through the model.
2. **Screen-share in a follow-up call** if Rossella escalates you
   to a 30-minute conversation. Don't send it unsolicited in the
   first DM — the page link is plenty for the cold contact.

To regenerate after editing text or stress numbers:
```bash
cd code && ../.venv/bin/python build_deck.py
```

Slide map:

| # | Title                                              | Purpose            |
|---|----------------------------------------------------|--------------------|
| 1 | Title — "A power-electronics risk lens on NAV facilities" | Open |
| 2 | Executive summary — three claims                   | One-page elevator pitch |
| 3 | The 2026 setup — NAV moves mainstream              | Industry framing   |
| 4 | Sub-sector thesis table                            | The core argument  |
| 5 | Sub-sector risk matrix (figure)                    | Visual punch       |
| 6 | Empirical reality check — listed comparables       | The 350-point spread |
| 7 | Model setup — two facility regimes + stress table  | Methodology        |
| 8 | Heatmap results (dual-panel figure)                | The visual proof   |
| 9 | Punchline — reference portfolios + three callouts  | Numerical takeaway |
| 10| Honest limits + roadmap                            | Self-awareness     |
| 11| About me                                           | Positioning        |
| 12| Close — "happy to walk through, or step back honestly" | CTA           |

### Recommended: Notion (fastest)

1. Create a new public Notion page.
2. Paste the contents of `content/01-page-content.md`.
3. Upload both PNGs from `figures/`, replace the `![...]` image
   references with Notion-uploaded versions.
4. Share → "Anyone with the link can view".
5. Copy URL → paste into the DM.

### Alternative: GitHub Pages (more credible to a quant)

1. `git init && git add . && git commit -m "first look"` inside
   this folder.
2. Push to a public GitHub repo named e.g. `unicredit-first-look`.
3. Enable Pages in repo settings (source: `main`, root, Jekyll off).
4. The page renders directly from `content/01-page-content.md` if you
   add a tiny `index.md` redirect or just link to that file's raw URL.

GitHub Pages signals "I can also use git", which is a small bonus.

---

## Pre-send checklist

- [ ] Replace `[LINK]` in the DM with the published page URL.
- [ ] Replace `[your LinkedIn URL]` with your actual LinkedIn profile URL.
- [ ] Open the published page on a phone and a desktop — confirm both figures load.
- [ ] Re-read `code/pseudocode.md §5` ("Two-minute explain the code script") once more.
- [ ] Glance at Wolfspeed (WOLF) and Vertiv (VRT) charts on Yahoo Finance — you should be able to quote rough 2024-2026 returns without checking.
- [ ] **Check your Italian permesso di soggiorno status** — see "Visa / work authorisation" section below.

---

## Post-send protocol

* **Day 0**: DM sent.
* **Day 1–3**: silence is normal — do not double-message.
* **Day 5 working**: if no reply, identify one senior person on the
  desk (UniCredit CIB Markets / Global Financing & Advisory) via
  LinkedIn and send the short version (Version B in the DM file)
  directly, mentioning you reached out to HR but understand they're
  busy.
* **If they reply asking for CV**: send CV + the line from
  `content/02-linkedin-dm.md` ("After they reply" section).
* **If they reply offering a call**: pre-call checklist is in
  `content/03-interview-qa.md`.

---

## Visa / work authorisation — what to know before the call

UniCredit is an Italian employer hiring in Italy. They will ask, in
some form: **"Are you authorised to work in Italy, and if so, under
what conditions?"** Wrong or vague answers kill the file. Don't
improvise.

For a non-EU Master's student at Politecnico di Milano, the relevant
facts are:

1. **Now (during the M.Sc.)**: your *permesso di soggiorno per studio*
   allows **part-time work up to 20 hrs/week** during term and full
   hours during holiday periods. Internships through Polimi (a
   *tirocinio curriculare*) typically don't count against this limit.
2. **After graduation**: you can convert the *permesso per studio* to
   a *permesso per attesa occupazione* (job-seeking permit, valid up
   to 12 months) and then to a *permesso per lavoro subordinato*
   once UniCredit issues a contract. The bank handles the *nulla
   osta* paperwork — most large Italian employers, especially banks
   with Graduate Programmes, do this routinely.
3. **Italy's "quota system"** (decreto flussi) for non-EU work
   permits has carve-outs for highly skilled / Master's-degree
   holders, so for a Polimi M.Sc. graduate into a banking role the
   process is administrative, not lottery-based.

**What to say on the call** (adapt only if your status differs):

> "I'm on a *permesso di soggiorno per studio* through Polimi. Upon
> graduation, that converts into job-seeking and then work permits —
> straightforward administratively for an Italian employer. Happy
> to share my *permesso* and *codice fiscale* whenever the process
> reaches HR onboarding."

**Verify before the call** by checking:
- Your physical *permesso di soggiorno* card — expiry date and type.
- Polimi's International Students Office (*Servizi agli studenti
  internazionali*) — they confirm exactly what your card permits and
  what the post-graduation conversion timeline is for your nationality.

> If your status is **different** from the above (e.g. you already
> hold a work permesso, you're an EU citizen with Italian-equivalent
> rights, you're on a permit that doesn't allow conversion), then
> the above wording must change. Verify before sending the DM —
> the wrong answer here is the easiest way to lose the seat.

---

*Built 2026-06. Honest about scope, deliberate about depth.*
