

A few design notes worth knowing:

**Spline boundary condition** — `bc_type="natural"` sets the second derivative to zero at both endpoints, which is the standard "free" (not-a-knot) natural spline and matches the Delphi `cubicSplineFree`. If you ever need clamped endpoints (specifying derivatives), just swap in `bc_type=("clamped", (dy0, dyn))`.

**Coefficient layout** — `scipy`'s `cs.c[row, segment]` has row 0 as the cubic term and row 3 as the constant, so the mapping to Horner form is direct with no reordering needed.

**Non-uniform spacing** — `CubicSpline` handles variable knot spacing natively, exactly as the Delphi routine's comment advertises.

**Precision** — The format string `%.6f` matches your Delphi `Format('%8.6f', [...])`. You can pass a different format string as a parameter if you need more or fewer decimal places.


The `monotone` flag won't help with the **original test data** because PCHIP still faithfully follows whatever shape the data describes — and `y = [0, 1, 1.5, 0.5, 0.5, 0.5, 0.5]` genuinely has a hump in it. PCHIP just prevents *additional* overshoot that isn't in the data; it can't smooth away a peak that *is*.

The data fix from my previous message is the **primary** fix. To see the difference between the two interpolators you need data that actually has a plateau:

```python
# Hump data — BOTH interpolators will produce a hump (correct behaviour)
x = [0, 1,   2,   3,   6,   7,   8  ]
y = [0, 1,   1.5, 0.5, 0.5, 0.5, 0.5]   # ← peak at x=2, not a plateau

# Rise-then-plateau data — now the flag matters
x = [0, 1,   2,   3,   4,   6,   8  ]
y = [0, 0.5, 1.0, 1.5, 1.5, 1.5, 1.5]   # ← genuine flat region
#                            ^^^^^^^^^^^
#   CubicSpline may undershoot slightly here; PCHIP will be perfectly flat
```

So the short version:

| Problem | Fix |
|---|---|
| Hump instead of plateau | **Change the data** — the input y-values must actually be flat |
| Undershoot/overshoot in flat region | Use `monotone=True` (PCHIP) |

Both are needed together to get a clean rise-then-plateau output.

For your specific use case — **drug dosing or experimental inputs to a biochemical model** — yes, `monotone=True` should be your default. The reasoning:

- Dosing data typically has **flat baselines, step-like rises, and plateaus** — exactly the shapes PCHIP is designed to preserve
- You never want the spline to go **negative** between data points (e.g. a drug concentration dipping below zero between two positive measurements — physically meaningless)
- The C¹ vs C² smoothness difference is **irrelevant** for a forcing input; you're not differentiating it analytically
- Users entering a handful of (time, dose) points expect the curve to **behave like the data looks** — no surprise oscillations

The only case where you'd prefer `monotone=False` (natural cubic) is if the data represents something inherently smooth where the *second* derivative continuity matters — like a smoothly varying enzyme activity profile where you have dense, high-quality measurements. In that situation the extra smoothness of C² is a genuine benefit.

A practical default would be to simply make `True` the default in the function signature:

```python
def antimony_piecewise(x, y, var_name="Input", time_var="time",
                       antimony_continuation=True,
                       monotone=True):   # ← changed default
```
