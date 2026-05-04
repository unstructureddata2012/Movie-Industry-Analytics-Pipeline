import pandas as pd
import logging
 
logger = logging.getLogger(__name__)
 
 
def genre_summary(df, genre_col='primary_genre', rating_col='vote_average', revenue_col='revenue_usd', budget_col='budget_usd'):
    required = [c for c in [genre_col, rating_col, revenue_col, budget_col] if c in df.columns]
    if genre_col not in df.columns:
        logger.warning('genre_col "%s" not found in DataFrame', genre_col)
        return pd.DataFrame()
 
    agg_dict = {}
    if rating_col in df.columns:
        agg_dict['avg_rating']    = (rating_col, 'mean')
        agg_dict['median_rating'] = (rating_col, 'median')
        agg_dict['movie_count']   = (rating_col, 'count')
    if revenue_col in df.columns:
        agg_dict['total_revenue'] = (revenue_col, 'sum')
    if budget_col in df.columns:
        agg_dict['total_budget']  = (budget_col, 'sum')
 
    summary = df.groupby(genre_col).agg(**agg_dict).reset_index()
    summary = summary.sort_values('movie_count', ascending=False)
    logger.info('Genre summary: %d genres', len(summary))
    return summary
 
 
def yearly_trends(df, year_col='release_year', revenue_col='revenue_usd',budget_col='budget_usd', rating_col='vote_average'):

    if year_col not in df.columns:
        logger.warning('year_col "%s" not found in DataFrame', year_col)
        return pd.DataFrame()
 
    df = df[pd.to_numeric(df[year_col], errors='coerce').fillna(0) > 1900].copy()
 
    agg_dict = {'movie_count': (year_col, 'count')}
    if revenue_col in df.columns:
        agg_dict['total_revenue'] = (revenue_col, 'sum')
    if budget_col in df.columns:
        agg_dict['total_budget'] = (budget_col, 'sum')
    if rating_col in df.columns:
        agg_dict['avg_rating'] = (rating_col, 'mean')
 
    trends = df.groupby(year_col).agg(**agg_dict).reset_index()
    trends = trends.sort_values(year_col)
    logger.info('Yearly trends: %d years', len(trends))
    return trends
 
 
def top_n_per_group(df, group_col, sort_col, n=5, ascending=False):
    result = (
        df.groupby(group_col, group_keys=False)
          .apply(lambda x: x.nlargest(n, sort_col) if not ascending
                 else x.nsmallest(n, sort_col))
    )
    logger.info('top_n_per_group: group=%s sort=%s n=%d -> %d rows', group_col, sort_col, n, len(result))
    return result
