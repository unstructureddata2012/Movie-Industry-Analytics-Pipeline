import os
import time
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv  

load_dotenv()
logger = logging.getLogger(__name__)

TMDB_BASE_URL = os.getenv('TMDB_BASE_URL')
IMAGE_BASE_URL = os.getenv('IMAGE_BASE_URL')
API_TOKEN = os.getenv('API_TOKEN')

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "accept": "application/json"
}
 
def fetch_popular_movies(pages=3):
    movies = []
    for page in range(1, pages + 1):
        url = f'{TMDB_BASE_URL}/movie/popular?page={page}'
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        movies.extend(data.get('results', []))
        logger.info(f'Fetched page {page}, total so far: {len(movies)}')
        time.sleep(0.5)  
    return movies
 
def download_poster(file_path, dest_dir, size='w342'):
    if not file_path:
        return None
    filename = file_path.lstrip('/')
    dest = Path(dest_dir) / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        logger.debug(f'Already exists: {dest}')
        return str(dest)
    url = f'{IMAGE_BASE_URL}/{size}{file_path}'
    resp = requests.get(url, stream=True, timeout=15)
    resp.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info(f'Downloaded: {dest}')
    return str(dest)
 
def download_movie_posters(movies, dest_dir='data/raw/images', size='w342'):
    downloaded = []  
    for movie in movies:
        poster_path = movie.get('poster_path')  
        if poster_path: 
            local = download_poster(poster_path, dest_dir, size)  
            print(f"Saving images to: {os.path.abspath(dest_dir)}")
            if local:
                downloaded.append({
                    'movie_id': movie['id'],
                    'title': movie['title'],
                    'local_path': local,
                    'poster_path': poster_path
                })
        time.sleep(0.1)  

    logger.info(f"Downloaded {len(downloaded)} posters.")
    return downloaded