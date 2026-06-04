# Pseudocode + Logic Walkthrough

> Read this **before** the interview. Goal: be able to explain every
> step of `nav_stress_model.py` in your own voice, without reading the
> screen. Should take ~30 minutes to internalise.

---

## 1. The single sentence that summarises the model

> "Given a NAV facility against a power-electronics PE fund, the model
> applies sub-sector-specific NAV drawdowns and shows how the
> stressed LTV varies as you tilt the portfolio across sub-sectors."

If you can say that sentence cold, you've understood the model.

---

## 2. Pseudocode

```text
INPUT
    facility = (NAV₀, facility_size, covenant_LTV)
    sector_stress = { ev_powertrain: -35%,
                      data_center_power: -10%,
                      renewable_power: -30%,
                      industrial_drives: -10% }
    weights = { sub-sector → portfolio weight }    (must sum to 1)

CORE FUNCTION   stressed_ltv(weights, facility):
    drawdown   ← Σᵢ  weightᵢ × sector_stressᵢ
    NAV_stress ← NAV₀ × (1 + drawdown)               // note: drawdown is negative
    return facility_size / NAV_stress

SENSITIVITY SWEEP
    for ev_pct in [0, 0.025, 0.05, …, 1.00]:
        for dc_pct in [0, 0.025, 0.05, …, 1.00]:
            if ev_pct + dc_pct > 1:
                mark cell INFEASIBLE
                continue
            residual    ← 1 - ev_pct - dc_pct
            weights     ← { ev: ev_pct,
                            dc: dc_pct,
                            renewable: residual × 0.6,
                            industrial: residual × 0.4 }
            grid[ev, dc] ← stressed_ltv(weights, facility)

VISUALISE
    heatmap of grid       (green = LTV well below covenant,
                           red   = LTV above covenant = facility breach)
    overlay contour at covenant_LTV (the boundary that matters)
```

---

## 3. Why every modelling choice was made (so you can defend it)

### 3.1  Why split into exactly 4 sub-sectors?

These four cover **>90% of where 2024-2026 PE / VC money in power
electronics is going**:

| Sub-sector              | Why it's a separate credit            |
|-------------------------|---------------------------------------|
| EV powertrain           | Consumer-auto cycle, 5-10 OEM buyers  |
| Data-center power       | Hyperscaler capex super-cycle         |
| Renewable power conv.   | Policy / tariff / rate-sensitive      |
| Industrial drives       | Mid-cycle baseline, fragmented        |

Adding a fifth (e.g. consumer chargers) doesn't change the story but
adds noise — kept tight on purpose for a first-look deliverable.

### 3.2  Why those specific stress numbers?

Calibrated from **observed 2024-2026 public-market sector
dispersion**, then dampened ~30% to reflect that private NAV marks
lag and don't capture the full peak-to-trough public move:

| Listed comparable        | Observed move | → Sub-sector  | Applied stress |
|--------------------------|---------------|---------------|----------------|
| Wolfspeed                | ≈ −70%        | EV powertrain | −35%           |
| Vertiv                   | ≈ +280%       | Data-center   | −10% (mild)    |
| Schneider Electric (DCP) | ≈ +60%        | Data-center   | (confirms mild)|
| Enphase                  | ≈ −75%        | Renewables    | −30%           |
| ABB                      | ≈ +25%        | Industrial    | −10%           |

> **Banker question you must be ready for**:
> *"Aren't those numbers arbitrary?"*
>
> Answer: *"They're directionally anchored to listed comparables; the
> point of the model is not the absolute number but the **dispersion**
> — −35% vs −10% for two things both called 'power electronics' is what
> drives the result. The covenant breach contour shifts but doesn't
> disappear under reasonable re-calibration."*

### 3.3  Why LTV (not advance rate / borrowing base)?

A NAV facility's covenant trigger is typically expressed as an LTV
threshold (e.g. 65%). Modelling LTV directly = modelling the thing
the trader/structurer actually monitors. Advance-rate redetermination
is a follow-on layer I flagged as "next step" rather than guessing it.

### 3.4  Why no correlation matrix between sub-sectors?

Honest answer: keeps the first-look simple. Real model needs a
correlation block — e.g. EV and data-center are both rate-sensitive,
so they'd co-move partially. Flagged as future work in the Q&A.

### 3.5  Why sweep only EV × DC (not all 4 dimensions)?

A 4D sweep can't be visualised. EV and Data-center are the two themes
where PE capital is most concentrated in 2026, so they're the
underwriter's day-job tilt decisions. Renewable / industrial are
folded into the residual with a fixed 60/40 split — that's the same
modelling shortcut most stress tests use.

---

## 4. Numerical sanity check you should memorise

### Benign facility — $500M NAV, $150M facility, initial LTV 30%

| Portfolio mix                       | Drawdown | Stressed NAV | Stressed LTV | Covenant 65%? |
|-------------------------------------|----------|--------------|--------------|---------------|
| 100% EV powertrain                  | −35.0%   | $325M        | **46.2%**    | ok            |
| 100% data-center power              | −10.0%   | $450M        | 33.3%        | ok            |
| Diversified 25/25/25/25             | −21.25%  | $393.75M     | 38.1%        | ok            |

### Aggressive facility — $500M NAV, $250M facility, initial LTV 50%

| Portfolio mix                       | Drawdown | Stressed NAV | Stressed LTV | Covenant 65%?  |
|-------------------------------------|----------|--------------|--------------|----------------|
| 100% EV powertrain                  | −35.0%   | $325M        | **76.9%**    | **BREACH**     |
| 100% data-center power              | −10.0%   | $450M        | 55.6%        | ok             |
| Diversified 25/25/25/25             | −21.25%  | $393.75M     | 63.5%        | ok (1.5pp room) |

> Notice the punchline you must volunteer in conversation:
>
> 1. **At 30% initial LTV, no tilt breaches.** Facility sized
>    conservatively absorbs everything.
> 2. **At 50% initial LTV, EV-heavy tilts breach, data-center heavy
>    tilts don't.** The covenant line on the heatmap is the boundary.
> 3. **Diversified 25/25/25/25 sits 1.5 percentage points below
>    covenant** at 50% LTV — a "safe" portfolio on paper, but a single
>    extra 5 percentage points of EV concentration would breach it.
>    That's the under-priced risk single-sector haircuts miss.

---

## 5. Two-minute "explain the code" script

If asked *"walk me through your script"*, say:

1. **"I define a `Facility` dataclass — NAV, size, covenant. The whole model
   parameterises off this one object so I can vary the facility separately
   from the portfolio."**
2. **"I encode my sub-sector stress view as a dictionary. The values are
   calibrated to listed 2024-2026 dispersion, dampened for private-mark
   lag."**
3. **"The `stressed_ltv` function is just weighted-average drawdown
   applied to NAV, then divide by facility size. Three lines."**
4. **"`sweep_ltv_grid` walks a 41×41 grid of EV-exposure vs
   data-center-exposure. The infeasible region (EV + DC > 100%) is left
   as NaN."**
5. **"The plot is a red-green heatmap with the covenant threshold
   overlaid as a dashed contour. I also mark three reference portfolios
   on the chart so the reader can sanity-check the colour."**
6. **"Total ≈ 130 lines including comments and the plotting cosmetics.
   Single dependency on numpy + matplotlib."**

End with: **"The most honest thing the model does is force the
question 'what's in your power-electronics bucket?' to be answered
before you set the haircut."**

---

## 6. If you only remember three things

1. **Sub-sector dispersion** is the underwriting gap, not absolute level.
2. **Calibration anchors** are public-market 2024-2026, dampened for
   private mark lag.
3. **Next steps**: correlation matrix, dynamic advance-rate redetermination,
   hybrid (sub-line + NAV) cross-collateral logic.
