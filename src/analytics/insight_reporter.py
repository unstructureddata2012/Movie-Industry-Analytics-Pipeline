import pandas as pd
import logging
 
logger = logging.getLogger(__name__)
 
 
def q1_top_genres_by_revenue(df, genre_col='primary_genre', revenue_col='revenue_usd', top_n=10):
    """
    Question 1: Which genres generate the highest average revenue?
 
    Returns a DataFrame with genre and avg_revenue, sorted descending.
    """
    if genre_col not in df.columns or revenue_col not in df.columns:
        logger.warning('q1: required columns missing')
        return pd.DataFrame()
 
    result = (
        df[df[revenue_col] > 0]
          .groupby(genre_col)[revenue_col]
          .mean()
          .nlargest(top_n)
          .reset_index()
          .rename(columns={revenue_col: 'avg_revenue'})
    )
    logger.info('Q1 top genres by revenue: %d rows', len(result))
    return result
 
 
def q2_roi_by_genre(df, genre_col='primary_genre', revenue_col='revenue_usd', budget_col='budget_usd'):
    """
    Question 2: Which genres have the best return on investment?
 
    ROI is calculated as revenue / budget (only where budget > 0).
 
    Returns a DataFrame with genre and roi, sorted descending.
    """
    required = [genre_col, revenue_col, budget_col]
    if not all(c in df.columns for c in required):
        logger.warning('q2: required columns missing')
        return pd.DataFrame()
 
    df_roi = df[(df[budget_col] > 0) & (df[revenue_col] > 0)].copy()
    df_roi['roi'] = df_roi[revenue_col] / df_roi[budget_col]
 
    result = (
        df_roi.groupby(genre_col)['roi']
              .mean()
              .sort_values(ascending=False)
              .reset_index()
    )
    logger.info('Q2 ROI by genre: %d genres', len(result))
    return result
 
 
def q3_yearly_volume(df, year_col='release_year'):
    """
    Question 3: How has the number of movies released changed over time?
 
    Returns a DataFrame with release_year and movie_count, sorted ascending.
    """
    if year_col not in df.columns:
        logger.warning('q3: year_col "%s" missing', year_col)
        return pd.DataFrame()
 
    result = (
        df[pd.to_numeric(df[year_col], errors='coerce').fillna(0) > 1900]
          .groupby(year_col)
          .size()
          .reset_index(name='movie_count')
          .sort_values(year_col)
    )
    logger.info('Q3 yearly volume: %d years', len(result))
    return result
 
 
def q4_language_distribution(df, lang_col='original_language', top_n=10):
    """
    Question 4: What is the distribution of movies by original language?
 
    Returns a DataFrame with original_language and count for the top N languages.
    """
    if lang_col not in df.columns:
        logger.warning('q4: lang_col "%s" missing', lang_col)
        return pd.DataFrame()
 
    result = (
        df[lang_col]
          .value_counts()
          .head(top_n)
          .reset_index()
          .rename(columns={lang_col: 'original_language', 'count': 'count'})
    )
    logger.info('Q4 language distribution: %d languages', len(result))
    return result
 
 
def run_all_questions(df):
    """
    Run all four analytical questions and print a formatted summary.
 
    Parameters
    ----------
    df : DataFrame - the merged/cleaned analytical DataFrame
 
    Returns a dict with keys: top_genres, roi_by_genre, yearly_volume,
    language_distribution.
    """
    results = {}
 
    print('\n===========================')
    print('ANALYTICAL FINDINGS SUMMARY')
    print('===========================\n')
 
    # Q1
    top_genres = q1_top_genres_by_revenue(df)
    results['top_genres'] = top_genres
    if not top_genres.empty:
        best = top_genres.iloc[0]
        print(f'Q1 - Top Genre by Revenue: {best["primary_genre"]} '
              f'(avg ${best["avg_revenue"]:,.0f})')
    else:
        print('Q1 - Top Genre by Revenue: no data')
 
    # Q2
    roi = q2_roi_by_genre(df)
    results['roi_by_genre'] = roi
    if not roi.empty:
        best_roi = roi.iloc[0]
        print(f'Q2 - Best ROI Genre: {best_roi["primary_genre"]} '
              f'({best_roi["roi"]:.1f}x average return)')
    else:
        print('Q2 - Best ROI Genre: no data')
 
    # Q3
    yearly = q3_yearly_volume(df)
    results['yearly_volume'] = yearly
    if not yearly.empty:
        peak = yearly.loc[yearly['movie_count'].idxmax()]
        print(f'Q3 - Peak Release Year: {int(peak["release_year"])} '
              f'({int(peak["movie_count"])} movies)')
    else:
        print('Q3 - Peak Release Year: no data')
 
    # Q4
    langs = q4_language_distribution(df)
    results['language_distribution'] = langs
    if not langs.empty:
        top_lang = langs.iloc[0]
        pct = top_lang['count'] / len(df) * 100
        print(f'Q4 - Dominant Language: {top_lang["original_language"]} '
              f'({top_lang["count"]} movies, {pct:.1f}% of dataset)')
    else:
        print('Q4 - Dominant Language: no data')
 
    print('\n===========================')
    return results
