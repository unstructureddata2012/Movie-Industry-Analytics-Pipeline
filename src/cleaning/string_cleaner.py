import re
import pandas as pd
import logging
logger = logging.getLogger(__name__)

# Pre-compile regex patterns for speed
# These are compiled once when the module is loaded
RE_MULTI_SPACE = re.compile(r'\s+')
RE_YEAR_PARENS = re.compile(r'\(\d{4}\)')
RE_SPECIAL_CHARS = re.compile(r'[^\w\s\-\'\"\.,!?:]')

def clean_title(df: pd.DataFrame) -> pd.DataFrame:
    if 'title' not in df.columns:
        return df
    before = df['title'].copy()
    df['title'] = (
        df['title']
        .str.strip()
        .str.replace(RE_MULTI_SPACE, ' ', regex=True)
        .str.replace(RE_YEAR_PARENS, '', regex=True)
        .str.strip()   # strip again after removing year
    )
    changed = (before != df['title']).sum()
    logger.info('clean_title: %d titles modified', changed)
    return df

def clean_language_code(df: pd.DataFrame) -> pd.DataFrame:
    col = 'original_language'
    if col not in df.columns:
        return df
    df[col] = df[col].str.strip().str.lower()
    logger.info('clean_language_code: normalised to lowercase')
    return df

def clean_overview_text(df: pd.DataFrame) -> pd.DataFrame:
    if 'overview' not in df.columns:
        return df
    # Remove any HTML tags from scraped data
    RE_HTML = re.compile(r'<[^>]+>')
    df['overview'] = (
        df['overview']
        .str.strip()
        .str.replace(RE_HTML, ' ', regex=True)
        .str.replace(RE_MULTI_SPACE, ' ', regex=True)
        .str.strip()
    )
    logger.info('clean_overview_text: overview column cleaned')
    return df

def extract_year_from_release_date(df: pd.DataFrame) -> pd.DataFrame:
    if 'release_date' not in df.columns:
        return df
    # Extract 4-digit year from the start of the date string
    df['release_year'] = (
        df['release_date']
        .str.extract(r'^(\d{4})', expand=False)  # capture group 1
        .astype('Int64', errors='ignore')          # nullable integer
    )
    valid_years = df['release_year'].notna().sum()
    logger.info('extract_year_from_release_date: extracted %d years', valid_years)
    return df

def clean_genre_string(df: pd.DataFrame, col: str = 'genres') -> pd.DataFrame:
    if col not in df.columns:
        return df
    df[col] = (
        df[col]
        .str.strip()
        .str.title()                                # Action, Adventure
        .str.replace(r'\s*,\s*', ', ', regex=True)  # normalise commas
    )
    logger.info('clean_genre_string: genres normalised')
    return df
