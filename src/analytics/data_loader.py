import pandas as pd
import numpy as np
import logging
from pathlib import Path
from pymongo import MongoClient
from typing import Optional

logger = logging.getLogger(__name__)

MONGO_URI = 'mongodb://localhost:27017/'
DB_NAME   = 'movie_pipeline'
COLLECTION = 'raw_movies'


def load_from_mongodb(uri: str = MONGO_URI, db: str = DB_NAME, collection: str = COLLECTION, limit: int = 0) -> pd.DataFrame:
    logger.info('Connecting to MongoDB: %s / %s', db, collection)
    client = MongoClient(uri)
    try:
        coll = client[db][collection]
        cursor = coll.find({}, {'_id': 0})
        if limit:
            cursor = cursor.limit(limit)
        df = pd.DataFrame(list(cursor))
        logger.info('Loaded %d rows from MongoDB', len(df))
        return df
    finally:
        client.close()


def save_to_csv(df: pd.DataFrame, path: str) -> None:
    """Export a DataFrame to CSV and log the action."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding='utf-8')
    logger.info('Saved %d rows → %s', len(df), path)


def load_from_csv(path: str, dtype: Optional[dict] = None, parse_dates: Optional[list] = None) -> pd.DataFrame:
    logger.info('Loading CSV: %s', path)
    df = pd.read_csv(
        path,
        dtype=dtype or {'id': 'int32', 'vote_count': 'int32'},
        parse_dates=parse_dates or ['release_date'],
        na_values=['', 'None', 'null', 'N/A'],
        encoding='utf-8',
    )
    logger.info('CSV loaded: shape=%s', df.shape)
    return df


# def chunked_stats(path: str, chunk_size: int = 200) -> dict:
#     logger.info('Chunked stats: path=%s chunk_size=%d', path, chunk_size)
#     chunk_stats    = []
#     lang_accum     = {}
#     total_rows     = 0

#     for chunk in pd.read_csv(path, chunksize=chunk_size,
#                               dtype={'vote_average': 'float32',
#                                      'vote_count':   'int32'}):
#         total_rows += len(chunk)

#         # Global mean accumulator
#         chunk_stats.append(pd.DataFrame({
#             'sum_vote_avg':   [chunk['vote_average'].sum()],
#             'count_vote_avg': [chunk['vote_average'].count()],
#         }))

#         # Per-language accumulator
#         if 'original_language' in chunk.columns:
#             clean = chunk.dropna(subset=['original_language', 'vote_average'])
#             grouped = clean.groupby('original_language')['vote_average'].agg(['sum', 'count'])
#             for lang, row in grouped.iterrows():
#                 if lang not in lang_accum:
#                     lang_accum[lang] = {'sum': 0.0, 'count': 0}
#                 lang_accum[lang]['sum']   += row['sum']
#                 lang_accum[lang]['count'] += row['count']

#     combined     = pd.concat(chunk_stats, ignore_index=True)
#     global_mean  = combined['sum_vote_avg'].sum() / combined['count_vote_avg'].sum()

#     lang_df = pd.DataFrame([
#         {'language': l, 'mean_vote': d['sum']/d['count'], 'movie_count': d['count']}
#         for l, d in lang_accum.items()
#     ]).sort_values('movie_count', ascending=False).reset_index(drop=True)

#     logger.info('Chunked stats complete: total_rows=%d global_mean=%.4f', total_rows, global_mean)
#     return {'global_mean': float(global_mean), 'total_rows': total_rows, 'lang_df': lang_df}

def chunked_stats(path: str, chunk_size: int = 200) -> dict:
    """
    Compute global mean vote_average and per-language stats
    by iterating the CSV in chunks — memory-safe for large files.
    """
    logger.info('Chunked stats: path=%s chunk_size=%d', path, chunk_size)

    chunk_stats = []
    lang_accum = {}
    total_rows = 0

    for chunk in pd.read_csv(
        path,
        chunksize=chunk_size,
        na_values=['', 'None', 'null', 'N/A']
    ):
        total_rows += len(chunk)

        if 'vote_average' not in chunk.columns:
            raise ValueError(f"Missing required column: vote_average. Columns: {list(chunk.columns)}")

        if 'vote_count' not in chunk.columns:
            raise ValueError(f"Missing required column: vote_count. Columns: {list(chunk.columns)}")

        # safe numeric conversion
        chunk['vote_average'] = pd.to_numeric(chunk['vote_average'], errors='coerce')
        chunk['vote_count'] = pd.to_numeric(chunk['vote_count'], errors='coerce')

        # drop rows where vote_average is invalid
        valid_votes = chunk.dropna(subset=['vote_average'])

        chunk_stats.append(pd.DataFrame({
            'sum_vote_avg': [valid_votes['vote_average'].sum()],
            'count_vote_avg': [valid_votes['vote_average'].count()],
        }))

        if 'original_language' in chunk.columns:
            clean = chunk.dropna(subset=['original_language', 'vote_average'])
            grouped = clean.groupby('original_language')['vote_average'].agg(['sum', 'count'])

            for lang, row in grouped.iterrows():
                if lang not in lang_accum:
                    lang_accum[lang] = {'sum': 0.0, 'count': 0}
                lang_accum[lang]['sum'] += row['sum']
                lang_accum[lang]['count'] += row['count']

    if not chunk_stats:
        raise ValueError("No valid chunks found while processing CSV.")

    combined = pd.concat(chunk_stats, ignore_index=True)
    total_count = combined['count_vote_avg'].sum()

    if total_count == 0:
        global_mean = 0.0
    else:
        global_mean = combined['sum_vote_avg'].sum() / total_count

    lang_rows = [
        {
            'language': l,
            'mean_vote': d['sum'] / d['count'],
            'movie_count': d['count']
        }
        for l, d in lang_accum.items() if d['count'] > 0
    ]

    lang_df = pd.DataFrame(lang_rows)

    if not lang_df.empty:
        lang_df = lang_df.sort_values('movie_count', ascending=False).reset_index(drop=True)

    logger.info('Chunked stats complete: total_rows=%d global_mean=%.4f', total_rows, global_mean)
    return {
        'global_mean': float(global_mean),
        'total_rows': total_rows,
        'lang_df': lang_df
    }

def optimise_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df_opt = df.copy()

    for col in ['id', 'vote_count', 'runtime']:
        if col in df_opt.columns:
            df_opt[col] = pd.to_numeric(df_opt[col], downcast='integer', errors='coerce')
            logger.debug('Downcast int: %s → %s', col, df_opt[col].dtype)

    for col in ['vote_average', 'popularity']:
        if col in df_opt.columns:
            df_opt[col] = pd.to_numeric(df_opt[col], downcast='float', errors='coerce')
            logger.debug('Downcast float: %s → %s', col, df_opt[col].dtype)

    for col in ['original_language', 'status']:
        if col in df_opt.columns:
            cardinality = df_opt[col].nunique() / len(df_opt)
            if cardinality < 0.50:
                df_opt[col] = df_opt[col].astype('category')
                logger.debug('Converted to category: %s (cardinality=%.1f%%)',
                             col, cardinality * 100)

    return df_opt


def memory_comparison(df_before: pd.DataFrame, df_after: pd.DataFrame) -> dict:
    before_mb = df_before.memory_usage(deep=True).sum() / 1024**2
    after_mb  = df_after.memory_usage(deep=True).sum()  / 1024**2
    pct       = (1 - after_mb / before_mb) * 100 if before_mb else 0
    logger.info('Memory: %.2f MB → %.2f MB (reduction %.1f%%)', before_mb, after_mb, pct)
    return {'before_mb': before_mb, 'after_mb': after_mb, 'reduction_pct': pct}
