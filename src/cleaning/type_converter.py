import pandas as pd
import logging

logger = logging.getLogger(__name__)


def convert_dates(df: pd.DataFrame) -> pd.DataFrame:
    if 'release_date' not in df.columns:
        return df
    df['release_date'] = pd.to_datetime(
        df['release_date'], errors='coerce'
    )
    nat_count = df['release_date'].isna().sum()
    logger.info('convert_dates: %d rows could not be parsed (NaT)', nat_count)
    return df


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    float_cols = ['popularity', 'vote_average', 'budget', 'revenue']
    int_cols   = ['vote_count', 'runtime', 'id']

    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')
            logger.info('convert_numeric_columns: %s -> float32', col)

    for col in int_cols:
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            df[col] = numeric_col.round().astype('Int64')
            logger.info('convert_numeric_columns: %s -> Int64', col)

    return df


def convert_category_columns(df: pd.DataFrame) -> pd.DataFrame:
    cat_cols = ['original_language', 'status']
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype('category')
            logger.info('convert_category_columns: %s -> category', col)
    return df


def memory_report(df_before: pd.DataFrame, df_after: pd.DataFrame) -> None:

    mb_before = df_before.memory_usage(deep=True).sum() / 1024**2
    mb_after  = df_after.memory_usage(deep=True).sum() / 1024**2
    saved = mb_before - mb_after
    pct   = (saved / mb_before * 100) if mb_before > 0 else 0
    print(f'Memory before: {mb_before:.2f} MB')
    print(f'Memory after:  {mb_after:.2f} MB')
    print(f'Saved:         {saved:.2f} MB  ({pct:.1f}%)')
