import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from utils.logger import logging  
from storage.mongo import save_to_mongo, build_scraped_record, build_ocr_record, save_transcript, get_db
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

from audio_processing.loader      import inspect_audio, load_audio
from audio_processing.processor   import trim_audio, apply_fades, export_audio
from audio_processing.transcriber import (
    transcribe_audio, save_transcript_json,
    save_transcript_txt, save_transcript_srt
)
from video_processing.loader       import inspect_video, extract_audio_from_video
from video_processing.frame_extractor import extract_keyframes
import pandas as pd
from pathlib import Path
import logging
import numpy as np
from analytics import (
    demonstrate_array_creation, vectorized_operations,
    load_from_mongodb, save_to_csv,
    chunked_stats, optimise_dtypes, memory_comparison,
    inspect_shape, extract_release_year, plot_distributions,
    loc_filter, boolean_filter,
    extract_genres, top_genres, crime_overview_count,
    full_quality_report, outlier_report, save_missing_heatmap,
)

logger = logging.getLogger(__name__)

from cleaning.clean_pipeline import run_cleaning_pipeline
from analytics.data_loader import load_from_csv  

def run_analytics():

    PROCESSED_DIR = Path("data/processed/analytics")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    CSV_PATH = str(PROCESSED_DIR / "tmdb_movies.csv")
    OPT_CSV_PATH = str(PROCESSED_DIR / "tmdb_movies_optimised.csv")

    # ── Part A: NumPy ─────────────────────────
    arrays = demonstrate_array_creation()
    logger.info("NumPy arrays created: %s", list(arrays.keys()))

    vote_avg = np.array([7.8, 6.4, 8.1, 5.9, 7.2, 6.0, 8.5, 7.1])
    vote_count = np.array([2100, 890, 4500, 320, 1750, 540, 6200, 980])

    results = vectorized_operations(vote_avg, vote_count)
    logger.info(
        "Vectorized ops: mean=%.2f high_rated=%d",
        results["stats"]["mean"],
        results["high_rated"].sum()
    )
    df_movies = load_from_mongodb()

    if df_movies is None or df_movies.empty:
        logging.warning("MongoDB returned empty dataset — skipping Lab 8 analytics")
        return

    if 'data' in df_movies.columns:
        import pandas as pd
        df_movies = pd.json_normalize(df_movies['data'])
    save_to_csv(df_movies, CSV_PATH)

    # safety check BEFORE chunked read
    if not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
        raise ValueError(f"CSV file is empty or missing: {CSV_PATH}")

    chunk_results = chunked_stats(CSV_PATH)
   
    logger.info(
        "Chunked mean vote_avg: %.4f over %d rows",
        chunk_results["global_mean"],
        chunk_results["total_rows"]
    )

    df_opt = optimise_dtypes(df_movies)
    mem = memory_comparison(df_movies, df_opt)
    logger.info("Memory reduction: %.1f%%", mem["reduction_pct"])

    save_to_csv(df_opt, OPT_CSV_PATH)

    # ── Part C: Explore ───────────────────────
    shape_info = inspect_shape(df_movies)
    logger.info("Dataset shape: %dx%d", shape_info["rows"], shape_info["columns"])

    df_movies = extract_release_year(df_movies)
    plot_distributions(df_movies, str(PROCESSED_DIR / "distributions.png"))

    acclaimed = loc_filter(df_movies, min_vote_avg=8.0)
    logger.info("Acclaimed movies: %d", len(acclaimed))

    quality_popular = boolean_filter(df_movies)
    logger.info("Quality+popular: %d movies", len(quality_popular))

    # ── Part D: Regex & Quality ───────────────
    df_genres = extract_genres(df_movies)

    logger.info("Top genres: %s", top_genres(df_genres, n=10))
    logger.info("Crime overviews: %d", crime_overview_count(df_movies))

    quality_df = full_quality_report(df_movies)
    quality_df.to_csv(str(PROCESSED_DIR / "data_quality_report.csv"), index=False)

    save_missing_heatmap(df_movies, str(PROCESSED_DIR / "missing_heatmap.png"))

    outliers = outlier_report(df_movies)
    logger.info("Outlier report columns: %d", len(outliers))

    logger.info("COMPLETED")
    
def run_audio_video_stage():
    logging.info('=== Audio/Video Processing Stage ===')
    db = get_db()

    # AUDIO
    for audio_file in Path('data/raw/audio').glob('*.mp3'):
        try:
            logging.info(f'Processing audio: {audio_file.name}')

            audio = load_audio(str(audio_file))
            trimmed = trim_audio(audio, 0, min(30000, len(audio)))
            faded = apply_fades(trimmed)

            export_audio(
                faded,
                f'data/processed/audio/{audio_file.stem}_clip.mp3'
            )

            result = transcribe_audio(str(audio_file))

            j = f'data/processed/transcripts/{audio_file.stem}.json'
            t = f'data/processed/transcripts/{audio_file.stem}.txt'
            s = f'data/processed/transcripts/{audio_file.stem}.srt'

            save_transcript_json(result, j)
            save_transcript_txt(result, t)
            save_transcript_srt(result, s)

            save_transcript(db, result, str(audio_file), 'audio',
                            json_path=j, txt_path=t, srt_path=s)

        except Exception as e:
            logging.error(f'Audio error: {e}')

    # VIDEO
    for video_file in Path('data/raw/video').glob('*.mp4'):
        try:
            logging.info(f'Processing video: {video_file.name}')

            extract_keyframes(
                str(video_file),
                f'data/processed/frames/{video_file.stem}/'
            )

            audio_out = f'data/processed/audio/{video_file.stem}.mp3'
            extract_audio_from_video(str(video_file), audio_out)

            result = transcribe_audio(audio_out)

            j = f'data/processed/transcripts/{video_file.stem}.json'
            t = f'data/processed/transcripts/{video_file.stem}.txt'
            s = f'data/processed/transcripts/{video_file.stem}.srt'

            save_transcript_json(result, j)
            save_transcript_txt(result, t)
            save_transcript_srt(result, s)

            save_transcript(db, result, str(video_file), 'video',
                            json_path=j, txt_path=t, srt_path=s)

        except Exception as e:
            logging.error(f'Video error: {e}')

    logging.info('=== Audio/Video Processing Stage Complete ===')


def run_cleaning():
   
    logging.info('=== Lab 9: Data Cleaning ===')

    # Load the raw CSV that was exported in Lab 8
    raw_csv = Path('data/processed/analytics/tmdb_movies.csv')
    if not raw_csv.exists():
        logging.warning('tmdb_movies.csv not found')
        return None

    df_raw = pd.read_csv(raw_csv, low_memory=False)
    logging.info('Loaded %d rows from %s', len(df_raw), raw_csv)

    # Run the cleaning pipeline
    df_clean = run_cleaning_pipeline(df_raw, save=True)
    logging.info('Cleaning complete: %d rows saved to processed/cleaned/', len(df_clean))
    return df_clean

def run_pipeline():
    # movies = fetch_movies(3)

    # for movie in movies:
    #     parsed = extract_movie_fields(movie)

    #     save_to_mongo(parsed, "tmdb_api")

    # pdf_standard = "../../data/raw/pdf/film_standard.pdf"
    # pdf_two_column = "../../data/raw/pdf/film_two_column.pdf"

    # text_standard = extract_text_from_pdf(pdf_standard)
    # save_to_mongo(
    #     {"text": text_standard},
    #     "PDF Source",
    #     {"file_name": "film_standard.pdf", "type": "pdf"}
    # )

    # text_two_column = extract_text_from_two_column_pdf(pdf_two_column)
    # save_to_mongo(
    #     {"text": text_two_column},
    #     "PDF Source",
    #     {"file_name": "film_two_column.pdf", "type": "pdf"}
    # )

    # logging.info("PDF data processed")

    # word_standard = "../../data/raw/word/film_standard.docx"
    # word_two_column = "../../data/raw/word/film_two_column.docx"

    # text_word = extract_text_from_word(word_standard)
    # save_to_mongo(
    #     {"text": text_word},
    #     "Word Source",
    #     {"file_name": "film_standard.docx", "type": "word"}
    # )

    # text_word_2 = extract_text_from_word(word_two_column)
    # save_to_mongo(
    #     {"text": text_word_2},
    #     "Word Source",
    #     {"file_name": "film_two_column.docx", "type": "word"}
    # )

    # logging.info("Word data processed")


    # excel_path = "../../data/raw/excel/movies_excel.xlsx"
    # movies_excel = extract_data_from_excel(excel_path)

    # for movie in movies_excel:
    #     save_to_mongo(
    #         movie,
    #         "Excel Source",
    #         {"file_name": "movies_excel.xlsx", "type": "excel"}
    #     )

    # summary = extract_summary_from_excel(excel_path)
    # save_to_mongo(
    #     summary,
    #     "Excel Summary",
    #     {"file_name": "movies_excel.xlsx", "type": "excel_summary"}
    # )

    # logging.info("Excel data processed")
    # try:
    #     logging.info("Pocinjem web scraping Oscar filmova...")
    #     films = scrape_oscar_films(years=[2010, 2011, 2012])
    #     for film in films:
    #         record = build_scraped_record(film, "scrapethissite.com/oscar")
    #         save_to_mongo(record["data"], record["source"], {
    #             "type": record["type"],
    #             "extracted_at": record["extracted_at"]
    #         })
    #     logging.info(f"Web scraping finished. Scraped {len(films)} movies.")
    # except Exception as e:
    #     logging.error(f"Web scraping error: {e}")


    # try:
    #     logging.info("Pocinjem OCR slike...")
    #     raw_text, processed_text = compare_ocr("../../data/raw/images/test.png")

    #     save_to_mongo(
    #         {
    #             "raw_text": raw_text,
    #             "processed_text": processed_text
    #         },
    #         "OCR Image Source",
    #         {
    #             "file_name": "test.png",
    #             "type": "image_ocr"
    #         }
    #     )

    #     logging.info("OCR slike zavrsen.")
    # except Exception as e:
    #     logging.error(f"OCR slike greska: {e}")
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
    # try:
    #     logging.info("Pocinjem OCR skeniranog PDF-a...")
    #     pdf_texts = ocr_scanned_pdf("../../data/raw/scanned/sample.pdf")
    #     for page_key, text in pdf_texts.items():
    #         record = build_ocr_record(text, "sample.pdf", page_number=page_key)
    #         save_to_mongo(
    #             record["data"],
    #             record["source"],
    #             {
    #                 "type": record["type"],
    #                 "page_number": record["page_number"],
    #                 "extracted_at": record["extracted_at"]
    #             }
    #         )
    #     logging.info(f"OCR zavrsen. Obradeno {len(pdf_texts)} stranica.")
    # except Exception as e:
    #     logging.error(f"OCR greska: {e}")
    # try:
    #     logging.info("Pocinjem multi-page scraping timova...")
    #     teams = scrape_multiple_pages("https://www.scrapethissite.com/pages/forms/", max_pages=3)

    #     for team in teams:
    #         record = build_scraped_record(team, "scrapethissite.com/forms")
    #         save_to_mongo(
    #             record["data"],
    #             record["source"],
    #             {
    #                 "type": record["type"],
    #                 "extracted_at": record["extracted_at"]
    #             }
    #         )

    #     logging.info(f"Multi-page scraping zavrsen. Scraped {len(teams)} teams.")
    # except Exception as e:
    #     logging.error(f"Multi-page scraping error: {e}")
    # run_audio_video_stage()
    # run_analytics()
    logging.basicConfig(
        filename='pipeline.log',
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    run_cleaning()

    logging.info("Pipeline finished successfully")
    
if __name__ == "__main__":
    run_pipeline()