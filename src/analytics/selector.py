
"""
src/analytics/selector.py
Selection and filtering helpers for the TMDB DataFrame.
Covers: column selection, loc, iloc, boolean masks, isin, between.
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def select_columns(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Return a DataFrame with only the columns that exist in df."""
    existing = [c for c in cols if c in df.columns]
    logger.info('Selecting %d/%d columns', len(existing), len(cols))
    return df[existing]


def loc_filter(df: pd.DataFrame,
               min_vote_avg: float = 8.0,
               result_cols: list = None) -> pd.DataFrame:
    """
    Use df.loc with a boolean mask to select acclaimed movies.
    Returns only result_cols columns (or a default set).
    """
    if result_cols is None:
        result_cols = ['title', 'vote_average', 'vote_count', 'popularity']
    result_cols = [c for c in result_cols if c in df.columns]
    mask   = df['vote_average'] >= min_vote_avg
    result = df.loc[mask, result_cols]
    logger.info('loc filter (vote_avg >= %.1f): %d rows', min_vote_avg, len(result))
    return result


def iloc_sample(df: pd.DataFrame, step: int = 100) -> pd.DataFrame:
    """
    Use df.iloc with a step to sample every N-th row.
    Useful for quick inspection without random_state dependency.
    """
    result = df.iloc[::step]
    logger.info('iloc sample (step=%d): %d rows', step, len(result))
    return result


def boolean_filter(df: pd.DataFrame,
                   min_vote_avg: float = 7.0,
                   min_vote_count: int = 500,
                   min_popularity: float = 20.0) -> pd.DataFrame:
    """
    Combined boolean filter: quality AND popular movies.
    All conditions must be wrapped in parentheses — & has higher
    precedence than comparison operators in Python/pandas.
    """
    mask = (
        (df['vote_average'] > min_vote_avg)  &
        (df['vote_count']   > min_vote_count) &
        (df['popularity']   > min_popularity)
    )
    result = df[mask]
    logger.info('boolean_filter: %d rows match', len(result))
    return result


def isin_filter(df: pd.DataFrame,
                languages: list = None,
                exclude: bool = False) -> pd.DataFrame:
    """
    Filter by original_language using isin.
    If exclude=True, returns rows NOT in languages list.
    """
    if languages is None:
        languages = ['en', 'fr', 'de', 'es', 'ja', 'ko', 'hi']
    mask = df['original_language'].isin(languages)
    if exclude:
        mask = ~mask
    result = df[mask]
    logger.info('isin_filter (exclude=%s): %d rows', exclude, len(result))
    return result


def between_filter(df: pd.DataFrame,
                   col: str = 'vote_average',
                   low: float = 6.0,
                   high: float = 7.5) -> pd.DataFrame:
    """Select rows where col is between low and high (inclusive)."""
    result = df[df[col].between(low, high)]
    logger.info('between_filter %s [%.1f, %.1f]: %d rows', col, low, high, len(result))
    return result

