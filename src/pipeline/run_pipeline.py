import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from utils.logger import logging  
from storage.mongo import save_to_mongo, build_scraped_record, build_ocr_record  
from api.client import fetch_movies
from parsing.parsers import (
    extract_movie_fields,
    extract_text_from_pdf,
    extract_text_from_two_column_pdf,
    extract_text_from_word,
    extract_data_from_excel,
    extract_summary_from_excel,
    
)

from scraping.scraper import scrape_oscar_films, scrape_multiple_pages 
from ocr.ocr_utils import ocr_scanned_pdf, compare_ocr 


def run_pipeline():
    # movies = fetch_movies(3)

    # for movie in movies:
    #     parsed = extract_movie_fields(movie)

    #     save_to_mongo(parsed, "tmdb_api")

    pdf_standard = "../../data/raw/pdf/film_standard.pdf"
    pdf_two_column = "../../data/raw/pdf/film_two_column.pdf"

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

    word_standard = "../../data/raw/word/film_standard.docx"
    word_two_column = "../../data/raw/word/film_two_column.docx"

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


    excel_path = "../../data/raw/excel/movies_excel.xlsx"
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
    try:
        logging.info("Pocinjem web scraping Oscar filmova...")
        films = scrape_oscar_films(years=[2010, 2011, 2012])
        for film in films:
            record = build_scraped_record(film, "scrapethissite.com/oscar")
            save_to_mongo(record["data"], record["source"], {
                "type": record["type"],
                "extracted_at": record["extracted_at"]
            })
        logging.info(f"Web scraping finished. Scraped {len(films)} movies.")
    except Exception as e:
        logging.error(f"Web scraping error: {e}")

    logging.info("Pipeline finished successfully")
    try:
        logging.info("Pocinjem OCR slike...")
        raw_text, processed_text = compare_ocr("../../data/raw/images/test.png")

        save_to_mongo(
            {
                "raw_text": raw_text,
                "processed_text": processed_text
            },
            "OCR Image Source",
            {
                "file_name": "test.png",
                "type": "image_ocr"
            }
        )

        logging.info("OCR slike zavrsen.")
    except Exception as e:
        logging.error(f"OCR slike greska: {e}")
    # try:
    #         logging.info("Pocinjem OCR skeniranog PDF-a...")
    #         pdf_texts = ocr_scanned_pdf("data/raw/scanned/sample.pdf")
    #         for page_key, text in pdf_texts.items():
    #             record = build_ocr_record(text, "sample.pdf", page_number=page_key)
    #             save_to_mongo(record["data"], record["source"], {
    #                 "type": record["type"],
    #                 "page_number": record["page_number"],
    #                 "extracted_at": record["extracted_at"]
    #             })
    #         logging.info(f"OCR zavrsen. Obradeno {len(pdf_texts)} stranica.")
    # except Exception as e:
    #     logging.error(f"OCR greska: {e}")

    #     logging.info("Pipeline finished successfully")
    try:
        logging.info("Pocinjem OCR skeniranog PDF-a...")
        pdf_texts = ocr_scanned_pdf("../../data/raw/scanned/sample.pdf")
        for page_key, text in pdf_texts.items():
            record = build_ocr_record(text, "sample.pdf", page_number=page_key)
            save_to_mongo(
                record["data"],
                record["source"],
                {
                    "type": record["type"],
                    "page_number": record["page_number"],
                    "extracted_at": record["extracted_at"]
                }
            )
        logging.info(f"OCR zavrsen. Obradeno {len(pdf_texts)} stranica.")
    except Exception as e:
        logging.error(f"OCR greska: {e}")
    try:
        logging.info("Pocinjem multi-page scraping timova...")
        teams = scrape_multiple_pages("https://www.scrapethissite.com/pages/forms/", max_pages=3)

        for team in teams:
            record = build_scraped_record(team, "scrapethissite.com/forms")
            save_to_mongo(
                record["data"],
                record["source"],
                {
                    "type": record["type"],
                    "extracted_at": record["extracted_at"]
                }
            )

        logging.info(f"Multi-page scraping zavrsen. Scraped {len(teams)} teams.")
    except Exception as e:
        logging.error(f"Multi-page scraping error: {e}")
if __name__ == "__main__":
    run_pipeline()