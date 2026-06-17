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

from ast import If
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
# Set True to render only the first question group (quick output check).
PLOT_FIRST_ONLY = False

# Output figure dimensions in centimetres [width, height].
FIG_SIZE_CM = [14, 18]
FIG_RESOLUTION_DPI = 150

# FontSize
FONTSIZE_ANSWERS_TITLE = 18
FONTSIZE_ANSWERS_TEXT = 18
FONTSIZE_FIGURE_TITLE = 18

# Max characters per line for the question title; breaks only at word boundaries.
QUESTION_WRAP_WIDTH = 40

FIG_NAME_WRAP_LENGTH = 100

OPTION_WRAP_WIDTH = 40

# Option to enable or disable the legend (labels for radar axes)
PRINT_LEGEND = False

# Output file format: 'png' or 'svg'.
FIG_FORMAT = 'png'

# ANSWERS ALIGNMENT
# Vertical spacing between rows in the answer-options list.
# 1.0 = default even distribution; >1 increases the gap, <1 tightens it.
OPTION_LINE_SPACING = 2
OPTIONAL_TEXT_ALIGNMENT_X = -0.1
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


def build_filename(section: str, question: str, max_len: int = FIG_NAME_WRAP_LENGTH,
                   fmt: str = 'png') -> str:
    """Return a safe filename derived from section + question strings."""
    combined = _sanitize(section) + '_' + _sanitize(question)
    combined = combined.strip(' -_')
    if len(combined) > max_len:
        combined = combined[:max_len].rstrip(' -_')
    return f'{combined}.{fmt}'


# ── Options-list subplot ─────────────────────────────────────────────────────

def _draw_options_list(ax, options: list[str]) -> None:
    """Render the Options list as labelled rows on a plain Axes."""
    ax.axis('off')

    wrapped_lines = [textwrap.fill(opt, width=OPTION_WRAP_WIDTH) for opt in options]
    # Number of physical lines each wrapped option occupies (>=1).
    line_counts   = [w.count('\n') + 1 for w in wrapped_lines]
    total_lines   = sum(line_counts)

    # Height of a single text line, scaled by the spacing setting. Rows that
    # wrap onto multiple lines simply consume that many line-heights, so the
    # next row's start position is pushed down accordingly instead of
    # overlapping it.
    row_h = (1 / (total_lines + 1)) * OPTION_LINE_SPACING
    y_pos = 1.5 - row_h
    for wrapped, lc in zip(wrapped_lines, line_counts):
        ax.text(OPTIONAL_TEXT_ALIGNMENT_X, y_pos, wrapped,
                transform=ax.transAxes,
                fontsize=FONTSIZE_ANSWERS_TEXT, va='top', ha='left',
                multialignment='center', family='monospace',
                fontweight='bold')
        y_pos -= row_h * lc

    #ax.set_title('Answer options', fontsize=FONTSIZE_ANSWERS_TITLE, pad=8)


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
            radarPlot(ax_radar, X, Y, attributes, N_X=N_A, N_Y=N_S, disp_legend=PRINT_LEGEND)

            # --- title (above whole figure) ----------------------------------
            sec_w  = textwrap.fill(section,  width=90)
            que_w  = textwrap.fill(question, width=QUESTION_WRAP_WIDTH,
                                   break_long_words=False)
            # fig.suptitle(f'{sec_w}\n{que_w}',
            #              fontsize=FONTSIZE_FIGURE_TITLE, y=1.01,
            #              ha='center', va='bottom', fontweight='bold')

            fig.suptitle(f'{que_w}',
                         fontsize=FONTSIZE_FIGURE_TITLE, y=1.01,
                         ha='center', va='bottom', fontweight='bold')

            # --- options list ------------------------------------------------
            _draw_options_list(ax_list, options)

            # --- save --------------------------------------------------------
            fname    = build_filename(section, question, fmt=FIG_FORMAT)
            out_path = os.path.join(out_dir, fname)
            fig.savefig(out_path, bbox_inches='tight', dpi=FIG_RESOLUTION_DPI,
                        transparent=(FIG_FORMAT == 'svg'))
            plt.close(fig)
            print(f'  Saved: {fname}')

            if PLOT_FIRST_ONLY:
                break

    print('\nDone.')


if __name__ == '__main__':
    main()
