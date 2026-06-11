# -*- coding: utf-8 -*-
"""
radarPlot.py
Radar chart helper: draw two data series (X = Authority, Y = Science)
on an existing polar Axes, normalised to 0-100 %.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# ── Colour configuration ────────────────────────────────────────────────────
# Adjust these RGB tuples (0-255) to change series colours.
RGB_X = (0,   114, 189)   # blue  — Authority
RGB_Y = (50,  168,  82)   # green — Science
# ────────────────────────────────────────────────────────────────────────────

_ALPHA = 0.25


def _rgb(t):
    """Normalise an (R, G, B) tuple from 0-255 to 0-1 range."""
    return tuple(c / 255 for c in t)


def radarPlot(ax, X, Y, attributes=None, N_X=None, N_Y=None):
    """
    Draw a two-series radar chart on *ax* (must be a polar Axes).

    Parameters
    ----------
    ax         : matplotlib polar Axes
    X          : list[int | float]   Authority response counts per option
    Y          : list[int | float]   Science  response counts per option
    attributes : list[str], optional Axis labels; auto a-z if None
    N_X        : int, optional       Total Authority respondents (scale factor)
    N_Y        : int, optional       Total Science  respondents (scale factor)
    """

    n = len(X)
    assert len(Y) == n, "X and Y must have the same length"

    # --- axis labels: auto-generate a, b, c, … if not provided -------------
    if attributes is None:
        attributes = [chr(ord('a') + i) for i in range(n)]

    # --- normalise to 0-100 % -----------------------------------------------
    scale_X = N_X if (N_X and N_X > 0) else (max(X) if max(X) > 0 else 1)
    scale_Y = N_Y if (N_Y and N_Y > 0) else (max(Y) if max(Y) > 0 else 1)

    X_pct = [v / scale_X * 100 for v in X]
    Y_pct = [v / scale_Y * 100 for v in Y]

    # --- build angle array (open; n points, NOT n+1) -----------------------
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()

    # Close the loop for plotting only
    ang_closed = angles + angles[:1]
    X_closed   = X_pct  + X_pct[:1]
    Y_closed   = Y_pct  + Y_pct[:1]

    # --- draw series --------------------------------------------------------
    cx = _rgb(RGB_X)
    cy = _rgb(RGB_Y)

    ax.plot(ang_closed, X_closed, color=cx, linewidth=1.5)
    ax.fill(ang_closed, X_closed, color=cx, alpha=_ALPHA)

    ax.plot(ang_closed, Y_closed, color=cy, linewidth=1.5)
    ax.fill(ang_closed, Y_closed, color=cy, alpha=_ALPHA)

    # --- axis layout --------------------------------------------------------
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Pass the OPEN angles array so its length matches the labels list
    ax.set_thetagrids(np.degrees(angles), attributes, fontsize=9)

    # Adjust label alignment based on position in the circle
    for label, angle in zip(ax.get_xticklabels(), angles):
        if np.isclose(angle, 0) or np.isclose(angle, np.pi):
            label.set_horizontalalignment('center')
        elif 0 < angle < np.pi:
            label.set_horizontalalignment('left')
        else:
            label.set_horizontalalignment('right')

    # --- y-axis (radial) scale ----------------------------------------------
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25 %', '50 %', '75 %', '100 %'], fontsize=7)
    ax.set_rlabel_position(180 / n)

    # --- styling ------------------------------------------------------------
    ax.tick_params(colors='#222222')
    ax.grid(color='#AAAAAA')
    ax.spines['polar'].set_color('#222222')
    ax.set_facecolor('#FAFAFA')

    # --- legend with respondent counts -------------------------------------
    legend_handles = [
        Patch(facecolor=cx, alpha=0.5 + _ALPHA,
              label=f'Authority  (N = {int(scale_X)})'),
        Patch(facecolor=cy, alpha=0.5 + _ALPHA,
              label=f'Science    (N = {int(scale_Y)})'),
    ]
    ax.legend(handles=legend_handles,
              loc='upper right', bbox_to_anchor=(1.45, 1.15),
              fontsize=9, framealpha=0.8)
