"""
src/analytics/regex_ops.py
Regular-expression operations on TMDB text columns.
Uses both the re module and the pandas .str accessor.
"""
import re
import pandas as pd
import collections
import logging

logger = logging.getLogger(__name__)

# Pre-compiled patterns
_YEAR_IN_TITLE   = re.compile(r'\((\d{4})\)')
_VALID_YEAR      = re.compile(r'\b(19|20)\d{2}\b')
_GENRE_NAME      = re.compile(r'"name":\s*"([^"]+)"')
_CRIME_TERMS     = re.compile(r'\b(murder|kill|crime|detective|investigat)\b', re.IGNORECASE)
_TMDB_ID         = re.compile(r'^\d{1,7}$')


def extract_year_from_title(titles: pd.Series) -> pd.Series:
    """
    Extract four-digit year from parentheses in movie title.
    Returns a Series of matched years (or NaN if no match).
    Example: 'The Dark Knight (2008)' → '2008'
    """
    result = titles.str.extract(r'\((\d{4})\)', expand=False)
    logger.info('Titles with year in parentheses: %d', result.notna().sum())
    return result


def filter_titles_starting_with(df: pd.DataFrame, prefix: str = 'The') -> pd.DataFrame:
    """Filter movies whose title starts with prefix (case-sensitive)."""
    pattern = rf'^{re.escape(prefix)}\s'
    mask    = df['title'].str.contains(pattern, na=False)
    result  = df[mask]
    logger.info('Titles starting with "%s": %d', prefix, len(result))
    return result


def extract_number_from_title(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'title_number' column with the first digit sequence found
    in the title (e.g. '2049' from 'Blade Runner 2049').
    """
    df = df.copy()
    df['title_number'] = df['title'].str.extract(r'(\d+)', expand=False)
    count = df['title_number'].notna().sum()
    logger.info('Titles containing a number: %d', count)
    return df


def crime_overview_count(df: pd.DataFrame) -> int:
    """Count overviews that mention crime-related terms."""
    if 'overview' not in df.columns:
        return 0
    mask  = df['overview'].str.contains(_CRIME_TERMS.pattern,
                                         case=False, na=False, regex=True)
    count = int(mask.sum())
    logger.info('Crime-related overviews: %d', count)
    return count


def short_overviews(df: pd.DataFrame, max_chars: int = 20) -> pd.DataFrame:
    """Return rows where overview is shorter than max_chars characters."""
    if 'overview' not in df.columns:
        return df.iloc[0:0]
    mask   = df['overview'].str.len() < max_chars
    result = df.loc[mask, ['title', 'overview']]
    logger.info('Very short overviews (<%d chars): %d', max_chars, len(result))
    return result


def extract_genres(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse genre names from the TMDB genres JSON string column.
    Adds a 'genre_list' column with a Python list per row.
    Returns a copy of the DataFrame.
    """
    df = df.copy()
    if 'genres' not in df.columns:
        logger.warning('No genres column found')
        return df
    df['genre_list'] = df['genres'].str.findall(r'"name":\s*"([^"]+)"')
    has_genres = df['genre_list'].apply(lambda x: isinstance(x, list) and len(x) > 0)
    logger.info('Movies with extracted genres: %d', has_genres.sum())
    return df


def top_genres(df: pd.DataFrame, n: int = 15) -> list:
    """
    Flatten genre_list column and return top-n genres as
    a list of (genre_name, count) tuples.
    Requires df to have a 'genre_list' column (call extract_genres first).
    """
    if 'genre_list' not in df.columns:
        return []
    all_genres: list = []
    df['genre_list'].dropna().apply(all_genres.extend)
    return collections.Counter(all_genres).most_common(n)


def validate_tmdb_id(id_str: str) -> bool:
    """
    Return True if id_str is a valid TMDB movie ID:
    a positive integer with 1–7 digits.
    """
    return bool(_TMDB_ID.match(str(id_str))) and int(id_str) > 0

