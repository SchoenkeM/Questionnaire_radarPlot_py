# -*- coding: utf-8 -*-
"""
importSurvey.py
Load a semicolon-delimited survey CSV and aggregate binary
Authority / Science responses per option row into df1.
"""

import re
import pandas as pd


def importSurvey(csv_path: str) -> pd.DataFrame:
    """
    Parameters
    ----------
    csv_path : str
        Path to a semicolon-delimited survey CSV file.

    Returns
    -------
    df1 : pd.DataFrame
        Columns: Sections, Question, Options,
                 Authority, Science, N_A, N_S, N
        Authority / Science hold per-row counts of positive responses.
        N_A / N_S / N hold the total number of respondents in each group
        (constant across all rows of a single CSV file).
    """

    # --- read raw data (all columns as strings to handle free-text cells) ---
    df = pd.read_csv(csv_path, sep=';', encoding='latin-1', dtype=str)

    # --- identify Authority and Science columns by pattern matching ---------
    auth_cols = [c for c in df.columns if re.search(r'Authority', c, re.IGNORECASE)]
    sci_cols  = [c for c in df.columns if re.search(r'Science',   c, re.IGNORECASE)]

    # --- convert to binary: '0' / blank / NaN → 0 ; everything else → 1 ---
    _ZERO_TOKENS = {'0', '', 'nan', 'none', 'NaN', 'None'}

    def _to_binary(val: str) -> int:
        return 0 if str(val).strip() in _ZERO_TOKENS else 1

    for col in auth_cols + sci_cols:
        df[col] = df[col].apply(_to_binary)

    # --- build df1 ----------------------------------------------------------
    df1 = df[['Sections', 'Question', 'Options']].copy()

    N_A = len(auth_cols)
    N_S = len(sci_cols)

    df1['N_A']       = N_A
    df1['N_S']       = N_S
    df1['N']         = N_A + N_S
    df1['Authority'] = df[auth_cols].sum(axis=1).astype(int)
    df1['Science']   = df[sci_cols].sum(axis=1).astype(int)

    return df1
