# ============================================================
#  results_processor.py
#  Load and clean BehaviorSpace output CSV files
# ============================================================

import pandas as pd
from pathlib import Path


def load_results(results_path: Path) -> pd.DataFrame:
    """
    Load a BehaviorSpace output CSV and normalise column names.
    BehaviorSpace adds 6 header lines before the data rows.
    Column names like [metabolism-rate] become metabolism_rate.
    """
    try:
        df = pd.read_csv(results_path, skiprows=6)
    except Exception:
        # Some BehaviorSpace versions use fewer header rows
        df = pd.read_csv(results_path)

    # Normalise: strip brackets, spaces → underscores, lowercase
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r"[\[\]]", "", regex=True)
        .str.replace(r"\s+", "_", regex=True)
        .str.lower()
    )

    # Drop unnamed index columns that BehaviorSpace sometimes adds
    df = df.loc[:, ~df.columns.str.startswith("unnamed")]

    return df