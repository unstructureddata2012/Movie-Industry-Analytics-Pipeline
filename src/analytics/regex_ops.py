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
RE_TMDB_ID = re.compile(r'^\d+$')           
RE_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')  
RE_LANG = re.compile(r'^[a-z]{2}$')         

def extract_year_from_title(titles: pd.Series) -> pd.Series:
    result = titles.str.extract(r'\((\d{4})\)', expand=False)
    logger.info('Titles with year in parentheses: %d', result.notna().sum())
    return result


def filter_titles_starting_with(df: pd.DataFrame, prefix: str = 'The') -> pd.DataFrame:
    pattern = rf'^{re.escape(prefix)}\s'
    mask    = df['title'].str.contains(pattern, na=False)
    result  = df[mask]
    logger.info('Titles starting with "%s": %d', prefix, len(result))
    return result

def extract_number_from_title(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['title_number'] = df['title'].str.extract(r'(\d+)', expand=False)
    count = df['title_number'].notna().sum()
    logger.info('Titles containing a number: %d', count)
    return df

def crime_overview_count(df: pd.DataFrame) -> int:
    if 'overview' not in df.columns:
        return 0
    mask  = df['overview'].str.contains(_CRIME_TERMS.pattern, case=False, na=False, regex=True)
    count = int(mask.sum())
    logger.info('Crime-related overviews: %d', count)
    return count

def short_overviews(df: pd.DataFrame, max_chars: int = 20) -> pd.DataFrame:
    if 'overview' not in df.columns:
        return df.iloc[0:0]
    mask   = df['overview'].str.len() < max_chars
    result = df.loc[mask, ['title', 'overview']]
    logger.info('Very short overviews (<%d chars): %d', max_chars, len(result))
    return result

def extract_genres(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'genres' not in df.columns:
        logger.warning('No genres column found')
        return df
    df['genre_list'] = df['genres'].str.findall(r'"name":\s*"([^"]+)"')
    has_genres = df['genre_list'].apply(lambda x: isinstance(x, list) and len(x) > 0)
    logger.info('Movies with extracted genres: %d', has_genres.sum())
    return df

def top_genres(df: pd.DataFrame, n: int = 15) -> list:
    if 'genre_list' not in df.columns:
        return []
    all_genres: list = []
    df['genre_list'].dropna().apply(all_genres.extend)
    return collections.Counter(all_genres).most_common(n)

def validate_tmdb_id(id_str: str) -> bool:
    return bool(_TMDB_ID.match(str(id_str))) and int(id_str) > 0

def find_invalid_dates(df: pd.DataFrame, col: str = 'release_date') -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    # notna() excludes NaN rows from the check
    has_value = df[col].notna()
    wrong_format = has_value & ~df[col].astype(str).str.match(
        r'^\d{4}-\d{2}-\d{2}$', na=False
    )
    count = wrong_format.sum()
    print(f'find_invalid_dates: {count} dates have wrong format in {col}')
    return wrong_format

def find_invalid_language_codes(df: pd.DataFrame, col: str = 'original_language') -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    invalid = df[col].notna() & ~df[col].str.match(r'^[a-z]{2}$', na=False)
    print(f'find_invalid_language_codes: {invalid.sum()} invalid codes')
    return invalid

def extract_number_from_string(series: pd.Series) -> pd.Series:
    return series.str.extract(r'(\d+\.?\d*)', expand=False).astype(float)

def flag_short_overviews(df: pd.DataFrame, min_words: int = 5) -> pd.Series:
    if 'overview' not in df.columns:
        return pd.Series(False, index=df.index)
    word_count = df['overview'].str.split().str.len().fillna(0)
    short = word_count < min_words
    print(f'flag_short_overviews: {short.sum()} overviews have fewer than {min_words} words')
    return short