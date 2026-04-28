import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cleaning.missing_handler import (
    drop_rows_missing_title,
    fill_missing_overview,
    replace_zero_with_nan,
    fill_numeric_with_median,
)
from src.cleaning.string_cleaner import (
    clean_title,
    clean_language_code,
    extract_year_from_release_date,
)
from src.cleaning.deduplicator import (
    drop_exact_duplicates,
    drop_duplicate_ids,
    count_duplicates,
)
from src.cleaning.type_converter import convert_dates
from src.cleaning.validator import (
    validate_no_null_titles,
    validate_vote_average_range,
)

@pytest.fixture
def sample_movies():
    """
    A small DataFrame that looks like real TMDB movie data.
    Intentionally includes problems we want to test fixing.
    """
    return pd.DataFrame({
        'id':               [1, 2, 3, 4, 5],
        'title':            ['The Matrix', '  Inception  ', None, 'Se7en', ''],
        'overview':         ['A hacker discovers reality.', None,
                             'Short.', 'A detective story.', 'Another film.'],
        'vote_average':     [8.7, 8.8, None, 8.6, 7.5],
        'popularity':       [100.0, 80.0, 0.0, 90.0, 50.0],
        'budget':           [63_000_000, 160_000_000, 0, 2_000_000, 0],
        'original_language':['en', 'EN', 'fr', 'en', 'de'],
        'release_date':     ['1999-03-31', '2010-07-16',
                             '2000-10-22', 'BAD_DATE', None],
    })

def test_drop_rows_missing_title_removes_null(sample_movies):
    result = drop_rows_missing_title(sample_movies)
    assert result['title'].isna().sum() == 0

def test_drop_rows_missing_title_removes_empty_string(sample_movies):
    result = drop_rows_missing_title(sample_movies)
    assert (result['title'].str.strip() == '').sum() == 0

def test_fill_missing_overview_no_nulls_remain(sample_movies):
    result = fill_missing_overview(sample_movies)
    assert result['overview'].isna().sum() == 0

def test_fill_missing_overview_uses_placeholder(sample_movies):
    result = fill_missing_overview(sample_movies)
    filled = result.loc[sample_movies['overview'].isna(), 'overview']
    assert filled.str.contains('available', case=False).all()

def test_replace_zero_with_nan_on_budget(sample_movies):
    result = replace_zero_with_nan(sample_movies, columns=['budget'])
    zero_count = (result['budget'] == 0).sum()
    assert zero_count == 0

def test_clean_title_strips_whitespace(sample_movies):
    result = clean_title(sample_movies.dropna(subset=['title']))
    assert not result['title'].str.startswith(' ').any()
    assert not result['title'].str.endswith(' ').any()

def test_clean_language_code_lowercases(sample_movies):
    result = clean_language_code(sample_movies)
    assert result['original_language'].str.islower().all()

def test_extract_year_creates_column(sample_movies):
    result = extract_year_from_release_date(sample_movies)
    assert 'release_year' in result.columns

def test_extract_year_correct_values(sample_movies):
    result = extract_year_from_release_date(sample_movies)
    assert result.loc[0, 'release_year'] == 1999
    assert result.loc[1, 'release_year'] == 2010

def test_drop_exact_duplicates_removes_copies():
    df = pd.DataFrame({'id': [1, 1, 2], 'title': ['Matrix', 'Matrix', 'Inception']
    })
    result = drop_exact_duplicates(df)
    assert len(result) == 2

def test_drop_duplicate_ids_keeps_first():
    df = pd.DataFrame({ 'id':    [10, 10, 20], 'title': ['Version A', 'Version B', 'Other']})
    result = drop_duplicate_ids(df, id_col='id')
    assert len(result) == 2
    assert result.loc[result['id'] == 10, 'title'].values[0] == 'Version A'

def test_count_duplicates_returns_correct_number():
    df = pd.DataFrame({'id': [1, 1, 1, 2, 3]})
    assert count_duplicates(df, col='id') == 2

def test_convert_dates_produces_datetime_type(sample_movies):
    result = convert_dates(sample_movies)
    assert pd.api.types.is_datetime64_any_dtype(result['release_date'])

def test_convert_dates_bad_values_become_nat(sample_movies):
    result = convert_dates(sample_movies)
    # 'BAD_DATE' and None should both be NaT
    nat_count = result['release_date'].isna().sum()
    assert nat_count >= 2

def test_validate_no_null_titles_passes_on_clean_data():
    df = pd.DataFrame({'title': ['Matrix', 'Inception']})
    validate_no_null_titles(df)   # should not raise

def test_validate_no_null_titles_fails_on_null():
    df = pd.DataFrame({'title': ['Matrix', None]})
    with pytest.raises(AssertionError):
        validate_no_null_titles(df)

def test_validate_vote_average_fails_on_out_of_range():
    df = pd.DataFrame({'vote_average': [8.5, 11.0]})
    with pytest.raises(AssertionError):
        validate_vote_average_range(df)
