# -*- coding: utf-8 -*-
"""
main_RadarPlot.py
Version: v1.0.0
Date: 2024-06-17
For every CSV in ../InputData/:
  1. Import and aggregate survey data          (importSurvey)
  2. Group rows by Question (key 2)
  3. For each question group create a figure:
       Left  subplot — radar chart             (radarPlot)
       Right subplot — text list of Options
  4. Save PNG to ../Output_RadarPlot/<stem>/
"""

import os
import re
import sys
import textwrap

import matplotlib.pyplot as plt

# Make sibling modules importable when running from any working directory
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from importSurvey import importSurvey   # noqa: E402
from radarPlot    import radarPlot      # noqa: E402


# ── Directory paths (relative to this script) ───────────────────────────────
_BASE_DIR   = os.path.join(_SCRIPT_DIR, '..')
INPUT_DIR   = os.path.normpath(os.path.join(_BASE_DIR, 'InputData'))
OUTPUT_DIR  = os.path.normpath(os.path.join(_BASE_DIR, 'Output_RadarPlot'))


# ── Figure configuration ─────────────────────────────────────────────────────
# Output figure dimensions in centimetres [width, height].
FIG_SIZE_CM = [24, 22]

# Vertical spacing between rows in the answer-options list.
# 1.0 = default even distribution; >1 increases the gap, <1 tightens it.
OPTION_LINE_SPACING = 1.0
# ─────────────────────────────────────────────────────────────────────────────


# ── Filename helpers ─────────────────────────────────────────────────────────

def _sanitize(text: str) -> str:
    """Replace characters that are invalid in file names and tidy whitespace."""
    # colon (with optional space) → dash-space
    text = re.sub(r':\s*',            '- ',  text)
    # digit-period (e.g. "1. ") → digit-dash
    text = re.sub(r'(\d+)\.\s*',      r'\1- ', text)
    # opening parenthesis → dash
    text = re.sub(r'\(',              '-',   text)
    # closing parenthesis → nothing
    text = re.sub(r'\)',              '',    text)
    # commas → space
    text = re.sub(r',\s*',            ' ',   text)
    # remaining filename-illegal chars
    text = re.sub(r'[<>"/\\|?*!]',   '',    text)
    # collapse multiple spaces / trailing space-dashes
    text = re.sub(r'\s+',             ' ',   text)
    return text.strip()


def build_filename(section: str, question: str, max_len: int = 100) -> str:
    """Return a safe .png filename derived from section + question strings."""
    combined = _sanitize(section) + '_' + _sanitize(question)
    combined = combined.strip(' -_')
    if len(combined) > max_len:
        combined = combined[:max_len].rstrip(' -_')
    return combined + '.png'


# ── Options-list subplot ─────────────────────────────────────────────────────

def _draw_options_list(ax, options: list[str]) -> None:
    """Render the Options list as labelled rows on a plain Axes."""
    ax.axis('off')
    n = len(options)
    row_h = (1.0 / (n + 1)) * OPTION_LINE_SPACING
    for i, opt in enumerate(options):
        wrapped = textwrap.fill(opt, width=55)
        y_pos = 1.0 - (i + 1) * row_h
        ax.text(0.05, y_pos, wrapped,
                transform=ax.transAxes,
                fontsize=9, va='top', ha='left',
                family='monospace')

    ax.set_title('Answer options', fontsize=10, pad=8)


# ── Main loop ────────────────────────────────────────────────────────────────

def main():
    csv_files = sorted(
        f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.csv')
    )
    if not csv_files:
        print(f'No CSV files found in {INPUT_DIR}')
        return

    for csv_file in csv_files:
        csv_path  = os.path.join(INPUT_DIR, csv_file)
        file_stem = os.path.splitext(csv_file)[0]
        out_dir   = os.path.join(OUTPUT_DIR, file_stem)
        os.makedirs(out_dir, exist_ok=True)

        print(f'\nProcessing: {csv_file}')
        df1 = importSurvey(csv_path)

        N_A = int(df1['N_A'].iloc[0])
        N_S = int(df1['N_S'].iloc[0])

        # --- iterate Question groups (preserve file order) -------------------
        for (section, question), grp in df1.groupby(
                ['Sections', 'Question'], sort=False):

            X       = grp['Authority'].tolist()
            Y       = grp['Science'].tolist()
            options = grp['Options'].tolist()
            n_opts  = len(options)

            # Auto-generate single-letter labels for the radar axes
            attributes = [chr(ord('a') + i) for i in range(n_opts)]

            # --- figure layout -----------------------------------------------
            fig = plt.figure(figsize=(FIG_SIZE_CM[0] / 2.54,
                                      FIG_SIZE_CM[1] / 2.54))
            gs = fig.add_gridspec(2, 1, height_ratios=[3, 1],
                                  hspace=0.35)
            ax_radar = fig.add_subplot(gs[0], polar=True)
            ax_list  = fig.add_subplot(gs[1])

            # --- radar chart -------------------------------------------------
            radarPlot(ax_radar, X, Y, attributes, N_X=N_A, N_Y=N_S)

            # --- title (above whole figure) ----------------------------------
            sec_w  = textwrap.fill(section,  width=90)
            que_w  = textwrap.fill(question, width=90)
            fig.suptitle(f'{sec_w}\n{que_w}',
                         fontsize=10, y=1.01,
                         ha='center', va='bottom')

            # --- options list ------------------------------------------------
            _draw_options_list(ax_list, options)

            # --- save --------------------------------------------------------
            fname    = build_filename(section, question)
            out_path = os.path.join(out_dir, fname)
            fig.savefig(out_path, bbox_inches='tight', dpi=150)
            plt.close(fig)
            print(f'  Saved: {fname}')

    print('\nDone.')


if __name__ == '__main__':
    main()
