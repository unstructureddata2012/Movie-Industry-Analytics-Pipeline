import logging
logging.basicConfig(level=logging.INFO)
from downloader import fetch_popular_movies, download_movie_posters

# Fetch 20 popular movies
movies = fetch_popular_movies(pages=1)
print(f'Fetched {len(movies)} movies')

# Download posters for the first 5 movies
results = download_movie_posters(movies[:5], dest_dir='data/raw/images')

if results:  
    for r in results:
        print(r['title'], '->', r['local_path'])
else:
    print("No posters were downloaded.")


