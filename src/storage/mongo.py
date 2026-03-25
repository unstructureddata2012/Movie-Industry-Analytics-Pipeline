from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["movie_pipeline"]
collection = db["raw_movies"]

def save_to_mongo(data, source, extra_metadata=None):
    document = {
        "data": data,
        "source": source,
        "fetched_at": datetime.utcnow(),
        "version": 1
    }

    # additional metadata for documents
    if extra_metadata:
        document.update(extra_metadata)

    collection.insert_one(document)

    print("Inserted document:", document)