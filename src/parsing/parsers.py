import csv
import xml.etree.ElementTree as ET
import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from storage.mongo import save_to_mongo 

def extract_movie_fields(movie):
    return {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "release_date": movie.get("release_date"),
        "popularity": movie.get("popularity")
    }

def parse_csv_file(file_path):
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)  
        for row in reader:
            # print(f"ID: {row['id']}, Title: {row['title']}, Release Date: {row['release_date']}, Popularity: {row['popularity']}")
            movie_fields = extract_movie_fields(row)  
            print(f"Saving to MongoDB: {movie_fields}")
            save_to_mongo(movie_fields, "CSV Source")
            

def parse_xml_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    for item in root.findall("movie"):
        movie = {
            "id": item.find("id").text,
            "title": item.find("title").text,
            "release_date": item.find("release_date").text,
            "popularity": item.find("popularity").text
        }
        # print(f"ID: {movie['id']}, Title: {movie['title']}, Release Date: {movie['release_date']}, Popularity: {movie['popularity']}")
        movie_fields = extract_movie_fields(movie) 
        print(f"Saving to MongoDB: {movie_fields}")
        save_to_mongo(movie_fields, "XML Source")

def parse_json_files():
    folder_path = "../../data/raw/api/"

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"): 
            file_path = os.path.join(folder_path, filename)

            with open(file_path, "r") as f:
                movie_data = json.load(f)

            if isinstance(movie_data, dict):  # If movie_data is a dictionary (single movie)
                movie_fields = extract_movie_fields(movie_data)
                # print(movie_fields)
                print(f"Saving to MongoDB: {movie_fields}")
                save_to_mongo(movie_fields, filename)
            else:
                print(f"Unexpected structure in {filename}: {movie_data}")

if __name__ == "__main__":
    parse_json_files()
    # parse_csv_file("../../data/raw/csv/sample.csv")
    # parse_xml_file("../../data/raw/xml/sample.xml")


