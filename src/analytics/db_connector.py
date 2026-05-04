import pymysql
import pandas as pd
import logging
 
logger = logging.getLogger(__name__)
#movie_analytics
 
def get_connection(host='localhost', user='root', password='', database='movies'):
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4'
    )
    logger.info('Connected to MySQL database: %s', database)
    return conn
 
 
def populate_financials(conn, df):

    required = ['id', 'title', 'budget_usd', 'revenue_usd', 'release_year', 'genre']
    available = [c for c in required if c in df.columns]
    data = df[available].dropna(subset=['id']).copy()
 
    # Fill missing numeric columns with 0
    for col in ['budget_usd', 'revenue_usd']:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)
 
    cursor = conn.cursor()
    inserted = 0
    skipped = 0
 
    for _, row in data.iterrows():
        try:
            cursor.execute(
                """
                INSERT IGNORE INTO movie_financials
                    (id, title, budget_usd, revenue_usd, release_year, genre)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    int(row.get('id', 0)),
                    str(row.get('title', '')),
                    int(row.get('budget_usd', 0)),
                    int(row.get('revenue_usd', 0)),
                    int(row['release_year']) if pd.notna(row['release_year']) else None,
                    str(row.get('genre', ''))
                )
            )
            inserted += 1
        except Exception as e:
            logger.warning('Skipped row id=%s: %s', row.get('id'), e)
            skipped += 1
 
    conn.commit()
    cursor.close()
    logger.info('Inserted %d rows, skipped %d rows', inserted, skipped)
    return inserted, skipped
 
 
def query_financials(conn, sql=None):
    if sql is None:
        sql = 'SELECT * FROM movie_financials'
    df = pd.read_sql(sql, conn)
    logger.info('Queried %d rows from MySQL', len(df))
    return df
