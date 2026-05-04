import pandas as pd
import logging
 
logger = logging.getLogger(__name__)
 
 
def build_genre_pipeline(min_vote_count=50, top_n=10):
    pipeline = [
        # Stage 1: filter low-vote movies
        {
            '$match': {
                'vote_count': {'$gte': min_vote_count},
                'genre':      {'$exists': True, '$ne': ''}
            }
        },
        # Stage 2: split comma-separated genre string into array items
        {
            '$addFields': {
                'genre_array': {
                    '$split': ['$genre', ',']
                }
            }
        },
        # Stage 3: one document per genre tag
        {
            '$unwind': '$genre_array'
        },
        # Stage 4: group by trimmed genre
        {
            '$group': {
                '_id':           {'$trim': {'input': '$genre_array'}},
                'avg_rating':    {'$avg': '$vote_average'},
                'total_revenue': {'$sum': '$revenue_usd'},
                'total_budget':  {'$sum': '$budget_usd'},
                'movie_count':   {'$sum': 1}
            }
        },
        # Stage 5: sort by average rating descending
        {
            '$sort': {'avg_rating': -1}
        },
        # Stage 6: limit to top N
        {
            '$limit': top_n
        },
        # Stage 7: reshape output fields
        {
            '$project': {
                '_id':           0,
                'genre':         '$_id',
                'avg_rating':    {'$round': ['$avg_rating', 2]},
                'total_revenue': 1,
                'total_budget':  1,
                'movie_count':   1
            }
        }
    ]
    logger.info('Built genre pipeline: min_vote_count=%d, top_n=%d', min_vote_count, top_n)
    return pipeline
 
 
def run_pipeline(collection, pipeline):
    cursor = collection.aggregate(pipeline)
    results = list(cursor)
    df = pd.DataFrame(results)
    logger.info('Pipeline returned %d documents', len(df))
    return df
 
 
def build_yearly_pipeline(start_year=2000):
    pipeline = [
        {
            '$match': {
                'release_year': {'$gte': start_year},
                'revenue_usd':  {'$gt': 0}
            }
        },
        {
            '$group': {
                '_id':           '$release_year',
                'total_revenue': {'$sum': '$revenue_usd'},
                'total_budget':  {'$sum': '$budget_usd'},
                'movie_count':   {'$sum': 1},
                'avg_rating':    {'$avg': '$vote_average'}
            }
        },
        {
            '$sort': {'_id': 1}
        },
        {
            '$project': {
                '_id':           0,
                'release_year':  '$_id',
                'total_revenue': 1,
                'total_budget':  1,
                'movie_count':   1,
                'avg_rating':    {'$round': ['$avg_rating', 2]}
            }
        }
    ]
    logger.info('Built yearly pipeline: start_year=%d', start_year)
    return pipeline
