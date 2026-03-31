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


def build_scraped_record(data, source_url, page_number=None):
    return {
        "data": data,
        "source": source_url,
        "page_number": page_number,
        "extracted_at": datetime.utcnow(),
        "type": "web_scraping"
    }

def build_ocr_record(text, source_file, page_number=None):
    return {
        "data": {"text": text},
        "source": source_file,
        "page_number": page_number,
        "extracted_at": datetime.utcnow(),
        "type": "ocr"
    }