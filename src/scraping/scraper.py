import requests
from bs4 import BeautifulSoup
import time
import os
import json

HEADERS = {
    "User-Agent": "ResearchBot/1.0 (student-lab@ibu.edu.ba)"
}
RAW_HTML_DIR = "../../data/raw/html"
SCRAPED_JSON_DIR = "../../data/raw/scraped"

os.makedirs(RAW_HTML_DIR, exist_ok=True)
os.makedirs(SCRAPED_JSON_DIR, exist_ok=True)
def scrape_single_page(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    save_html("single_page.html", response.text)
    
    soup = BeautifulSoup(response.text, "lxml")
    
    rows = soup.select("tr.team")
    
    results = []
    for row in rows:
        record = {
            "name":   row.select_one("td.name").get_text(strip=True)   if row.select_one("td.name")   else "",
            "year":   row.select_one("td.year").get_text(strip=True)   if row.select_one("td.year")   else "",
            "wins":   row.select_one("td.wins").get_text(strip=True)   if row.select_one("td.wins")   else "",
            "losses": row.select_one("td.losses").get_text(strip=True) if row.select_one("td.losses") else "",
        }
        results.append(record)
    
    return results

def scrape_multiple_pages(base_url, max_pages=3):
    all_results = []
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}?page_num={page}"
        print(f"Scraping page {page}: {url}")
        
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        save_html(f"teams_page_{page}.html", response.text)
        
        soup = BeautifulSoup(response.text, "lxml")
        rows = soup.select("tr.team")
        
        for row in rows:
            record = {
                "name":        row.select_one("td.name").get_text(strip=True)        if row.select_one("td.name")        else "",
                "year":        row.select_one("td.year").get_text(strip=True)        if row.select_one("td.year")        else "",
                "wins":        row.select_one("td.wins").get_text(strip=True)        if row.select_one("td.wins")        else "",
                "losses":      row.select_one("td.losses").get_text(strip=True)      if row.select_one("td.losses")      else "",
                "win_pct":     row.select_one("td.pct").get_text(strip=True)         if row.select_one("td.pct")         else "",
                "goals_for":   row.select_one("td.gf").get_text(strip=True)          if row.select_one("td.gf")          else "",
                "goals_against": row.select_one("td.ga").get_text(strip=True)        if row.select_one("td.ga")          else "",
                "page_scraped": page
            }
            all_results.append(record)
        
        time.sleep(1.5) 
    
    print(f"In total there is: {len(all_results)} teams scraped")
    save_json("teams_multiple_pages.json", all_results)
    return all_results

def scrape_oscar_films(years=None):
    """Scraping Oscar movies using JSON API endpoint."""
    if years is None:
        years = list(range(2010, 2016))
    
    base_url = "https://www.scrapethissite.com/pages/ajax-javascript/"
    all_films = []
    
    for year in years:
        url = f"{base_url}?ajax=true&year={year}"
        print(f"Fetching movies for: {year}...")
        
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        films = response.json()  
        
        for film in films:
            film["year_scraped"] = year
            all_films.append(film)
        
        time.sleep(1)
    
    print(f"In total there is: {len(all_films)} movies")
    save_json("oscar_films.json", all_films)
    return all_films
def save_html(filename, html_text):
    path = os.path.join(RAW_HTML_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_text)

def save_json(filename, data):
    path = os.path.join(SCRAPED_JSON_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    # url = "https://www.scrapethissite.com/pages/forms/"
    # data = scrape_single_page(url)
    # for item in data:
    #     print(item)
    # films = scrape_oscar_films(years=[2010, 2011, 2012])
    # for f in films[:3]:
    #     print(f)
    base_url = "https://www.scrapethissite.com/pages/forms/"
    scraped_data = scrape_multiple_pages(base_url, max_pages=3)
    # Print first few entries to verify
    for item in scraped_data[:5]:
        print(item)
