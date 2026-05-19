"""
Automated chart generation module – Lab 12.
Loads the cleaned movie dataset and generates all static and interactive charts.
"""

import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATA_PATH = Path("data/processed/cleaned/movies_clean.csv")
STATIC_OUT = Path("outputs/visualizations/static")
INTERACTIVE_OUT = Path("outputs/visualizations/interactive")


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and lightly prepare the cleaned movie dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at '{path}'. "
            "Run the cleaning pipeline first (Lab 9)."
        )
    df = pd.read_csv(path, low_memory=False)
    required = ["title", "release_year", "primary_genre",
                "budget_usd", "revenue_usd", "vote_average",
                "vote_count", "popularity"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")
    logger.info("Loaded %d movies from %s", len(df), path)
    return df


def run_static_charts(df: pd.DataFrame) -> dict:
    """Generate and save all matplotlib / seaborn charts."""
    from .static_charts import (
        plot_top_movies_by_revenue,
        plot_avg_rating_over_years,
        plot_budget_vs_revenue_scatter,
        plot_rating_distribution,
        plot_genre_rating_boxplot,
        plot_correlation_heatmap,
        plot_genre_count_bar,
        plot_dashboard_subplots,
    )

    STATIC_OUT.mkdir(parents=True, exist_ok=True)
    results = {}

    charts = [
        ("top_movies_revenue",    plot_top_movies_by_revenue),
        ("avg_rating_over_years", plot_avg_rating_over_years),
        ("budget_vs_revenue",     plot_budget_vs_revenue_scatter),
        ("rating_distribution",   plot_rating_distribution),
        ("genre_rating_boxplot",  plot_genre_rating_boxplot),
        ("correlation_heatmap",   plot_correlation_heatmap),
        ("genre_count_bar",       plot_genre_count_bar),
        ("dashboard_subplots",    plot_dashboard_subplots),
    ]

    for name, fn in charts:
        try:
            paths = fn(df, out_dir=STATIC_OUT)
            results[name] = paths
            print(f"  [static]  {name}")
            print(f"            PNG → {paths['png']}")
            print(f"            PDF → {paths['pdf']}")
        except Exception as exc:
            logger.error("Failed to generate '%s': %s", name, exc)
            print(f"  [static]  {name}  FAILED: {exc}")

    return results


def run_interactive_charts(df: pd.DataFrame) -> dict:
    """Generate and save all Plotly interactive charts."""
    from .interactive_charts import (
        interactive_budget_vs_revenue,
        interactive_top_movies_bar,
        interactive_movies_per_year,
        interactive_genre_boxplot,
        interactive_multi_layout,
    )

    INTERACTIVE_OUT.mkdir(parents=True, exist_ok=True)
    results = {}

    charts = [
        ("budget_vs_revenue",     interactive_budget_vs_revenue),
        ("top_movies_bar",        interactive_top_movies_bar),
        ("movies_per_year",       interactive_movies_per_year),
        ("genre_boxplot",         interactive_genre_boxplot),
        ("multi_layout",          interactive_multi_layout),
    ]

    for name, fn in charts:
        try:
            html_path = fn(df, out_dir=INTERACTIVE_OUT)
            results[name] = html_path
            print(f"  [interactive]  {name}")
            print(f"                 HTML → {html_path}")
        except Exception as exc:
            logger.error("Failed to generate '%s': %s", name, exc)
            print(f"  [interactive]  {name}  FAILED: {exc}")

    return results


def generate_all(data_path: Path = DATA_PATH) -> dict:
    """Full pipeline: load data → static charts → interactive charts."""
    print("\n========================================")
    print("  Lab 12 – Data Visualization Generator")
    print("========================================\n")

    df = load_data(data_path)
    print(f"Dataset: {len(df)} movies, {len(df.columns)} columns\n")

    print("── Static charts (matplotlib / seaborn) ──")
    static = run_static_charts(df)

    print("\n── Interactive charts (Plotly Express) ──")
    interactive = run_interactive_charts(df)

    print("\n========================================")
    print(f"  Done!  {len(static)} static + {len(interactive)} interactive")
    print(f"  Static  → {STATIC_OUT}")
    print(f"  Interactive → {INTERACTIVE_OUT}")
    print("========================================\n")

    return {"static": static, "interactive": interactive}
