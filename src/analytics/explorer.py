"""
src/analytics/explorer.py
Exploratory data analysis functions for the TMDB DataFrame.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')   # headless — no display server required
import matplotlib.pyplot as plt
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def inspect_shape(df: pd.DataFrame) -> dict:
    """Return shape, column names, and total cell count."""
    info = {
        'rows':    df.shape[0],
        'columns': df.shape[1],
        'cells':   df.size,
        'column_names': df.columns.tolist(),
    }
    logger.info('Shape: %d rows × %d columns', info['rows'], info['columns'])
    return info


def print_info(df: pd.DataFrame) -> None:
    """Call df.info() — shows dtypes and non-null counts."""
    df.info(memory_usage='deep')


def describe_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Return df.describe() for all numeric columns."""
    return df.describe()


def value_counts_report(df: pd.DataFrame,
                        cols: list = None,
                        top_n: int = 15) -> dict:
    """
    Return value_counts and nunique for each column in cols.
    If cols is None, uses ['original_language', 'status'].
    """
    if cols is None:
        cols = [c for c in ['original_language', 'status'] if c in df.columns]

    report = {}
    for col in cols:
        counts  = df[col].value_counts().head(top_n)
        n_unique = df[col].nunique()
        report[col] = {'counts': counts, 'nunique': n_unique}
        logger.info('%s: %d unique values', col, n_unique)
    return report


def extract_release_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse release_date and add a release_year integer column.
    Operates on a copy — original is not modified.
    """
    df = df.copy()
    if 'release_date' in df.columns:
        df['release_year'] = pd.to_datetime(
            df['release_date'], errors='coerce').dt.year
        logger.info('Extracted release_year: %d non-null',
                    df['release_year'].notna().sum())
    return df


def plot_distributions(df: pd.DataFrame, output_path: str) -> None:
    """
    Save a 2×2 chart of TMDB distributions to output_path.
    Uses Agg backend so no display is required.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('TMDB Movie Data – Distributions', fontsize=14, fontweight='bold')

    if 'vote_average' in df.columns:
        df['vote_average'].dropna().plot(
            kind='hist', bins=30, ax=axes[0, 0],
            color='steelblue', edgecolor='white')
        axes[0, 0].set_title('Vote Average Distribution')
        axes[0, 0].set_xlabel('Vote Average')

    if 'popularity' in df.columns:
        df['popularity'].dropna().plot(
            kind='hist', bins=30, ax=axes[0, 1],
            color='teal', edgecolor='white')
        axes[0, 1].set_title('Popularity Distribution (log scale)')
        axes[0, 1].set_xlabel('Popularity')
        axes[0, 1].set_yscale('log')

    if 'original_language' in df.columns:
        top_langs = df['original_language'].value_counts().head(10)
        top_langs.plot(kind='bar', ax=axes[1, 0], color='coral', edgecolor='white')
        axes[1, 0].set_title('Top 10 Languages')
        axes[1, 0].tick_params(axis='x', rotation=45)

    if 'release_year' in df.columns:
        year_counts = df['release_year'].dropna().value_counts().sort_index()
        year_counts.plot(kind='line', ax=axes[1, 1], color='purple', linewidth=2)
        axes[1, 1].set_title('Movies per Release Year')
        axes[1, 1].set_xlabel('Year')

    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches='tight')
    plt.close()
    logger.info('Saved distribution chart → %s', output_path)
