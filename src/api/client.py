import requests
import os
import time
from dotenv import load_dotenv
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from utils.logger import logging  

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")

# Base URL for API
url = "https://api.themoviedb.org/3/movie/popular"

def fetch_movies(pages=3):
    all_movies = []

    for page in range(1, pages + 1):
        params = {
            "api_key": API_KEY,
            "page": page
        }
        
        # Make the API request
        response = safe_request(url, params)
        
        if response:
            data = response.json()
            all_movies.extend(data["results"])  # Append movies from this page
        else:
            print(f"Error occurred on page {page}. Skipping.")
            continue

    return all_movies

def save_raw_data(data, page_num):
    
    folder_path = "../../data/raw/api/"
    os.makedirs(folder_path, exist_ok=True)
    
    # Define the file path to store the data for each page
    filename = f"movies_page_{page_num}.json"
    file_path = os.path.join(folder_path, filename)
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"Raw data saved to {file_path}")

# def safe_request(url, params, retries=3):
#     for i in range(retries):
#         try:
#             response = requests.get(url, params=params)
#             response.raise_for_status()  
#             return response
#         except requests.exceptions.RequestException as e:
#             logging.error(f"Error on attempt {i+1}: {e}")
#             time.sleep(2 ** i)

#     logging.error(f"Failed to fetch data after {retries} attempts.")
#     return None

# def safe_request(url, params, retries=3):
#     for i in range(retries):
#         try:
#             response = requests.get(url, params=params)
#             response.raise_for_status()  # Will raise an HTTPError for bad responses
            
#             # Log the successful API request
#             logging.info(f"Successfully fetched data from {url} (Page {params['page']})")
            
#             return response
            
#         except requests.exceptions.RequestException as e:
#             logging.error(f"Error on attempt {i + 1}: {e}")
#             logging.error(f"Response: {response.text}")  # Log the full response if an error occurs
            
#             time.sleep(2 ** i)  # Exponential backoff for retries

#     logging.error(f"Failed after {retries} attempts.")
#     return None
def safe_request(url, params, retries=3):
    for i in range(retries):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            
            # Log successful API request
            logging.info(f"Successfully fetched data from {url} (Page {params['page']})")
            return response

        except requests.exceptions.RequestException as e:
            # Log error details for the first failed request attempt
            logging.error(f"Error on attempt {i + 1}: {e}")
            
            if response:
                logging.error(f"Response status code: {response.status_code}")
                logging.error(f"Response content: {response.text}")  # Log the full response

            time.sleep(2 ** i)  # Exponential backoff for retries

    logging.error(f"Failed after {retries} attempts.")
    return None
# Example of how to fetch movies 
# movies = fetch_movies(pages=3)
# print(movies) 

if __name__ == "__main__":
    movies = fetch_movies(pages=3)  
    print(f"Fetched {len(movies)} movies.")
    if movies:
        print("Here are some movie titles:")
        for movie in movies[:5]:  
            print(movie["title"])
    

# if __name__ == "__main__":
#     movies = fetch_movies(pages=3) 
#     for page_num, movie_data in enumerate(movies, start=1):
#         save_raw_data(movie_data, page_num)  