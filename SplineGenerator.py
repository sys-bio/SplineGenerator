# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 16:59:34 2026

@author: hsauro
"""

import tellurium as te
import roadrunner

import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator


def antimony_piecewise(x: list[float], y: list[float],
                       var_name: str = "Input",
                       time_var: str = "time",
                       antimony_continuation: bool = True,
                       monotone: bool = True) -> str:
    """
    Parameters
    ----------
    monotone : bool
        If True, use PchipInterpolator (shape-preserving, no overshoot).
        If False, use natural CubicSpline (smoother but can overshoot).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if x.size != y.size:
        raise ValueError("x and y must have the same length.")
    if x.size < 3:
        raise ValueError(
            "At least 3 data points are required to generate a cubic spline."
        )
    if np.any(np.diff(x) <= 0):
        raise ValueError("x values must be strictly increasing.")

    if monotone:
        cs = PchipInterpolator(x, y)
    else:
        cs = CubicSpline(x, y, bc_type="natural")

    n_segments = len(x) - 1
    sep = ",\\ \n" if antimony_continuation else ",\n"
    segments = []

    for k in range(n_segments):
        xk  = x[k]
        xk1 = x[k + 1]
        c3  = cs.c[0, k]   # cubic
        c2  = cs.c[1, k]   # quadratic
        c1  = cs.c[2, k]   # linear
        c0  = cs.c[3, k]   # constant

        def fmt(v: float) -> str:
            return f"{v:+.6f}" if v < 0 else f"+{v:.6f}"

        delay = f"({time_var}-{xk:.6f})"
        expr = (
            f"(({c3:.6f}*{delay}"
            f"{fmt(c2)})*{delay}"
            f"{fmt(c1)})*{delay}"
            f"{fmt(c0)}"
        )
        condition = f"({time_var} >={xk:.6f}) && ({time_var} <= {xk1:.6f})"
        segments.append(f"{expr}, {condition}")

    body = sep.join(segments)
    return f"{var_name} := piecewise ({body})"


# ── demo: rise then plateau ───────────────────────────────────────────────────
x = [0,   1,   2,   3,   4,   6,   8  ]
y = [0.0, 0.5, 1.0, 1.5, 0.5, 0.5, 1.5]

print("--- Natural cubic spline ---")
print(antimony_piecewise(x, y, monotone=False))

print("\n--- PCHIP (shape-preserving) ---")
print(antimony_piecewise(x, y, monotone=True))


r = te.loada("""
Input := piecewise (((-0.031143*(time-0.000000)-0.000000)*(time-0.000000)+0.531143)*(time-0.000000)+0.000000, (time >=0.000000) && (time <= 1.000000),\ 
((0.155717*(time-1.000000)-0.093430)*(time-1.000000)+0.437713)*(time-1.000000)+0.500000, (time >=1.000000) && (time <= 2.000000),\ 
((-0.591724*(time-2.000000)+0.373720)*(time-2.000000)+0.718003)*(time-2.000000)+1.000000, (time >=2.000000) && (time <= 3.000000),\ 
((0.711177*(time-3.000000)-1.401451)*(time-3.000000)-0.309727)*(time-3.000000)+1.500000, (time >=3.000000) && (time <= 4.000000),\ 
((-0.121267*(time-4.000000)+0.732082)*(time-4.000000)-0.979096)*(time-4.000000)+0.500000, (time >=4.000000) && (time <= 6.000000),\ 
((-0.000747*(time-6.000000)+0.004480)*(time-6.000000)+0.494027)*(time-6.000000)+0.500000, (time >=6.000000) && (time <= 8.000000))
""")

m = r.simulate (0, 8, 200, ['time', 'Input'])
r.plot()

r = te.loada("""
Input := piecewise (((0.000000*(time-0.000000)+0.000000)*(time-0.000000)+0.500000)*(time-0.000000)+0.000000, (time >=0.000000) && (time <= 1.000000),\ 
((0.000000*(time-1.000000)+0.000000)*(time-1.000000)+0.500000)*(time-1.000000)+0.500000, (time >=1.000000) && (time <= 2.000000),\ 
((-0.500000*(time-2.000000)+0.500000)*(time-2.000000)+0.500000)*(time-2.000000)+1.000000, (time >=2.000000) && (time <= 3.000000),\ 
((2.000000*(time-3.000000)-3.000000)*(time-3.000000)+0.000000)*(time-3.000000)+1.500000, (time >=3.000000) && (time <= 4.000000),\ 
((0.000000*(time-4.000000)+0.000000)*(time-4.000000)+0.000000)*(time-4.000000)+0.500000, (time >=4.000000) && (time <= 6.000000),\ 
((-0.062500*(time-6.000000)+0.375000)*(time-6.000000)+0.000000)*(time-6.000000)+0.500000, (time >=6.000000) && (time <= 8.000000))
""")

m = r.simulate (0, 8, 200, ['time', 'Input'])
r.plot()