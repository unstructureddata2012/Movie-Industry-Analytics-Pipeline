import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Domain constants for TMDB movie data
MIN_RELEASE_YEAR = 1888   # first known film
MAX_RELEASE_YEAR = 2030   # allow near-future releases
MIN_VOTE_AVERAGE = 0.0
MAX_VOTE_AVERAGE = 10.0
MIN_RUNTIME_MINUTES = 1
MAX_RUNTIME_MINUTES = 1000
VALID_STATUSES = { 'Released', 'In Production', 'Post Production', 'Planned', 'Rumored', 'Canceled' }


def validate_no_null_titles(df: pd.DataFrame) -> None:
    assert df['title'].notna().all(), \
        f'Found {df["title"].isna().sum()} null titles'
    assert (df['title'].str.strip() != '').all(), \
        'Found rows with empty string titles'
    logger.info('validate_no_null_titles: PASSED')

def validate_vote_average_range(df: pd.DataFrame) -> None:
    if 'vote_average' not in df.columns:
        return
    non_null = df['vote_average'].dropna()
    assert non_null.between(MIN_VOTE_AVERAGE, MAX_VOTE_AVERAGE).all(), \
        f'vote_average out of range [{MIN_VOTE_AVERAGE}, {MAX_VOTE_AVERAGE}]'
    logger.info('validate_vote_average_range: PASSED')


def validate_release_year_range(df: pd.DataFrame) -> None:
    if 'release_year' not in df.columns:
        return
    non_null = df['release_year'].dropna()
    assert non_null.between(MIN_RELEASE_YEAR, MAX_RELEASE_YEAR).all(), \
        f'release_year out of range [{MIN_RELEASE_YEAR}, {MAX_RELEASE_YEAR}]'
    logger.info('validate_release_year_range: PASSED')


def validate_no_duplicate_ids(df: pd.DataFrame, id_col: str = 'id') -> None:
    if id_col not in df.columns:
        return
    dup_count = df.duplicated(subset=[id_col]).sum()
    assert dup_count == 0, \
        f'Found {dup_count} duplicate values in column {id_col}'
    logger.info('validate_no_duplicate_ids (%s): PASSED', id_col)

def validate_language_codes(df: pd.DataFrame) -> None:
    if 'original_language' not in df.columns:
        return
    non_null = df['original_language'].dropna().astype(str)
    valid = non_null.str.match(r'^[a-z]{2}$')
    assert valid.all(), \
        f'Found {(~valid).sum()} invalid language codes'
    logger.info('validate_language_codes: PASSED')


def run_all_validations(df: pd.DataFrame) -> None:
    checks = [
        validate_no_null_titles,
        validate_vote_average_range,
        validate_release_year_range,
        validate_no_duplicate_ids,
        validate_language_codes,
    ]
    passed = 0
    failed = 0
    for check in checks:
        try:
            check(df)
            print(f'  PASSED: {check.__name__}')
            passed += 1
        except AssertionError as e:
            print(f'  FAILED: {check.__name__} -> {e}')
            failed += 1
    print(f'\nValidation complete: {passed} passed, {failed} failed')
