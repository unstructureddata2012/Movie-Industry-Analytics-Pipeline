import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from utils.logger import logging  
from storage.mongo import save_to_mongo 
from api.client import fetch_movies
from parsing.parsers import (
    extract_movie_fields,
    extract_text_from_pdf,
    extract_text_from_two_column_pdf,
    extract_text_from_word,
    extract_data_from_excel,
    extract_summary_from_excel
)
def run_pipeline():
    # movies = fetch_movies(3)

    # for movie in movies:
    #     parsed = extract_movie_fields(movie)

    #     save_to_mongo(parsed, "tmdb_api")

    pdf_standard = "data/raw/pdf/film_standard.pdf"
    pdf_two_column = "data/raw/pdf/film_two_column.pdf"

    text_standard = extract_text_from_pdf(pdf_standard)
    save_to_mongo(
        {"text": text_standard},
        "PDF Source",
        {"file_name": "film_standard.pdf", "type": "pdf"}
    )

    text_two_column = extract_text_from_two_column_pdf(pdf_two_column)
    save_to_mongo(
        {"text": text_two_column},
        "PDF Source",
        {"file_name": "film_two_column.pdf", "type": "pdf"}
    )

    logging.info("PDF data processed")

    word_standard = "data/raw/word/film_standard.docx"
    word_two_column = "data/raw/word/film_two_column.docx"

    text_word = extract_text_from_word(word_standard)
    save_to_mongo(
        {"text": text_word},
        "Word Source",
        {"file_name": "film_standard.docx", "type": "word"}
    )

    text_word_2 = extract_text_from_word(word_two_column)
    save_to_mongo(
        {"text": text_word_2},
        "Word Source",
        {"file_name": "film_two_column.docx", "type": "word"}
    )

    logging.info("Word data processed")


    excel_path = "data/raw/excel/movies_excel.xlsx"
    movies_excel = extract_data_from_excel(excel_path)

    for movie in movies_excel:
        save_to_mongo(
            movie,
            "Excel Source",
            {"file_name": "movies_excel.xlsx", "type": "excel"}
        )

    summary = extract_summary_from_excel(excel_path)
    save_to_mongo(
        summary,
        "Excel Summary",
        {"file_name": "movies_excel.xlsx", "type": "excel_summary"}
    )

    logging.info("Excel data processed")

    logging.info("Pipeline finished successfully")

if __name__ == "__main__":
    run_pipeline()