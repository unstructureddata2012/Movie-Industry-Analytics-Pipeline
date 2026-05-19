"""
Static visualization module for Movie Industry Analytics Pipeline.
Uses matplotlib (object-oriented API) and seaborn for all static charts.
Lab 12 - Data Visualization
"""

import matplotlib
matplotlib.use("Agg")  # non-interactive backend so saving works outside notebooks
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Global style ──────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid")
sns.set_context("notebook")
sns.set_palette("viridis")

STATIC_OUT = Path("outputs/visualizations/static")


def _save(fig: plt.Figure, stem: str, out_dir: Path = STATIC_OUT) -> dict:
    """Save figure as PNG (300 dpi) and PDF. Returns dict of saved paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"{stem}.png"
    pdf_path = out_dir / f"{stem}.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s  (PNG + PDF)", stem)
    return {"png": str(png_path), "pdf": str(pdf_path)}


# ── 1. Bar chart – Top 10 movies by revenue ───────────────────────────────────
def plot_top_movies_by_revenue(df: pd.DataFrame, n: int = 10,
                               out_dir: Path = STATIC_OUT) -> dict:
    """Horizontal bar chart: top-n movies by box-office revenue."""
    top = (df[df["revenue_usd"] > 0]
           .nlargest(n, "revenue_usd")[["title", "revenue_usd"]]
           .sort_values("revenue_usd"))

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette("viridis", n)
    bars = ax.barh(top["title"], top["revenue_usd"] / 1e9, color=colors)

    # value labels
    for bar in bars:
        ax.text(bar.get_width() + 0.03, bar.get_y() + bar.get_height() / 2,
                f"${bar.get_width():.2f}B", va="center", fontsize=9)

    ax.set_xlabel("Box-Office Revenue (USD Billion)", fontsize=11)
    ax.set_title(f"Top {n} Movies by Revenue", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.1f}B"))
    ax.set_xlim(0, top["revenue_usd"].max() / 1e9 * 1.18)
    fig.tight_layout()

    return _save(fig, "top_movies_by_revenue", out_dir)


# ── 2. Line chart – Average rating over years ────────────────────────────────
def plot_avg_rating_over_years(df: pd.DataFrame,
                               out_dir: Path = STATIC_OUT) -> dict:
    """Line chart: mean vote_average and movie count per release year."""
    yearly = (df.groupby("release_year")
               .agg(avg_rating=("vote_average", "mean"),
                    movie_count=("title", "count"))
               .reset_index()
               .query("release_year >= 1980 and release_year <= 2025"))

    fig, ax1 = plt.subplots(figsize=(12, 5))
    color_line = "#1a6faf"
    color_bar = "#a8d5e2"

    ax1.bar(yearly["release_year"], yearly["movie_count"],
            color=color_bar, alpha=0.5, label="Movie Count")
    ax1.set_ylabel("Number of Movies", color=color_bar, fontsize=11)
    ax1.tick_params(axis="y", labelcolor=color_bar)

    ax2 = ax1.twinx()
    ax2.plot(yearly["release_year"], yearly["avg_rating"],
             color=color_line, linewidth=2.5, marker="o", markersize=5,
             label="Avg. Rating")
    ax2.set_ylabel("Average Vote Rating (0–10)", color=color_line, fontsize=11)
    ax2.tick_params(axis="y", labelcolor=color_line)
    ax2.set_ylim(0, 10)

    ax1.set_xlabel("Release Year", fontsize=11)
    ax1.set_title("Movie Releases and Average Rating Over the Years",
                  fontsize=14, fontweight="bold")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

    fig.tight_layout()
    return _save(fig, "avg_rating_over_years", out_dir)


# ── 3. Scatter plot – Budget vs Revenue ──────────────────────────────────────
def plot_budget_vs_revenue_scatter(df: pd.DataFrame,
                                   out_dir: Path = STATIC_OUT) -> dict:
    """Scatter: budget_usd vs revenue_usd, coloured by primary_genre."""
    data = df[(df["budget_usd"] > 0) & (df["revenue_usd"] > 0)].copy()
    data["budget_M"] = data["budget_usd"] / 1e6
    data["revenue_M"] = data["revenue_usd"] / 1e6

    genres = data["primary_genre"].value_counts().nlargest(6).index.tolist()
    data["genre_label"] = data["primary_genre"].where(
        data["primary_genre"].isin(genres), other="Other")

    palette = sns.color_palette("viridis", len(data["genre_label"].unique()))

    fig, ax = plt.subplots(figsize=(11, 7))
    sns.scatterplot(data=data, x="budget_M", y="revenue_M",
                    hue="genre_label", palette="viridis",
                    size="vote_average", sizes=(30, 250),
                    alpha=0.75, ax=ax)

    # break-even line
    max_val = max(data["budget_M"].max(), data["revenue_M"].max()) * 1.05
    ax.plot([0, max_val], [0, max_val], "--", color="gray",
            linewidth=1.2, label="Break-even (1:1)")

    ax.set_xlabel("Production Budget (USD Million)", fontsize=11)
    ax.set_ylabel("Box-Office Revenue (USD Million)", fontsize=11)
    ax.set_title("Budget vs Revenue – Coloured by Genre", fontsize=14, fontweight="bold")
    ax.legend(title="Genre / Size=Rating", bbox_to_anchor=(1.02, 1), loc="upper left",
              fontsize=9, title_fontsize=9)
    fig.tight_layout()

    return _save(fig, "budget_vs_revenue_scatter", out_dir)


# ── 4. Histogram – Distribution of vote_average ──────────────────────────────
def plot_rating_distribution(df: pd.DataFrame,
                             out_dir: Path = STATIC_OUT) -> dict:
    """Histogram + KDE of vote_average using seaborn displot (axes-level)."""
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(df["vote_average"].dropna(), bins=20, kde=True,
                 color="#1a6faf", edgecolor="white", ax=ax)
    ax.axvline(df["vote_average"].mean(), color="firebrick",
               linestyle="--", linewidth=1.8,
               label=f"Mean = {df['vote_average'].mean():.2f}")
    ax.axvline(df["vote_average"].median(), color="darkorange",
               linestyle="-.", linewidth=1.8,
               label=f"Median = {df['vote_average'].median():.2f}")
    ax.set_xlabel("Vote Average (0–10)", fontsize=11)
    ax.set_ylabel("Number of Movies", fontsize=11)
    ax.set_title("Distribution of Movie Ratings", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    fig.tight_layout()

    return _save(fig, "rating_distribution", out_dir)


# ── 5. Box plot – Rating by genre (seaborn) ──────────────────────────────────
def plot_genre_rating_boxplot(df: pd.DataFrame,
                              out_dir: Path = STATIC_OUT) -> dict:
    """Box-and-whisker plot: vote_average per primary_genre."""
    order = (df.groupby("primary_genre")["vote_average"]
               .median().sort_values(ascending=False).index.tolist())

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=df, x="primary_genre", y="vote_average",
                order=order, hue="primary_genre", palette="viridis",
                legend=False, ax=ax)
    ax.set_xlabel("Genre", fontsize=11)
    ax.set_ylabel("Vote Average (0–10)", fontsize=11)
    ax.set_title("Movie Rating Distribution by Genre", fontsize=14, fontweight="bold")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()

    return _save(fig, "genre_rating_boxplot", out_dir)


# ── 6. Heatmap – Correlation matrix ──────────────────────────────────────────
def plot_correlation_heatmap(df: pd.DataFrame,
                             out_dir: Path = STATIC_OUT) -> dict:
    """seaborn heatmap of numeric feature correlations."""
    numeric_cols = ["budget_usd", "revenue_usd", "vote_average",
                    "vote_count", "popularity"]
    corr_cols = [c for c in numeric_cols if c in df.columns]
    corr = df[corr_cols].corr()

    labels = {
        "budget_usd": "Budget",
        "revenue_usd": "Revenue",
        "vote_average": "Avg Rating",
        "vote_count": "Vote Count",
        "popularity": "Popularity",
    }
    corr.index = [labels.get(c, c) for c in corr.index]
    corr.columns = [labels.get(c, c) for c in corr.columns]

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                center=0, vmin=-1, vmax=1, square=True,
                linewidths=0.5, ax=ax,
                annot_kws={"size": 10})
    ax.set_title("Correlation Matrix – Budget, Revenue, Rating, Popularity",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()

    return _save(fig, "correlation_heatmap", out_dir)


# ── 7. Bar chart – Genre distribution ────────────────────────────────────────
def plot_genre_count_bar(df: pd.DataFrame,
                         out_dir: Path = STATIC_OUT) -> dict:
    """Vertical bar chart: number of movies per primary genre."""
    counts = df["primary_genre"].value_counts()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(counts.index, counts.values,
                  color=sns.color_palette("viridis", len(counts)))
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=9)

    ax.set_xlabel("Primary Genre", fontsize=11)
    ax.set_ylabel("Number of Movies", fontsize=11)
    ax.set_title("Number of Movies per Genre", fontsize=14, fontweight="bold")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()

    return _save(fig, "genre_count_bar", out_dir)


# ── 8. Subplot layout – 2×2 dashboard ────────────────────────────────────────
def plot_dashboard_subplots(df: pd.DataFrame,
                            out_dir: Path = STATIC_OUT) -> dict:
    """2×2 multi-panel matplotlib figure combining four key charts."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Movie Industry Analytics Dashboard", fontsize=16,
                 fontweight="bold", y=1.01)

    # Panel A: top 10 revenue
    top = (df[df["revenue_usd"] > 0]
           .nlargest(10, "revenue_usd")[["title", "revenue_usd"]]
           .sort_values("revenue_usd"))
    axes[0, 0].barh(top["title"], top["revenue_usd"] / 1e9,
                    color=sns.color_palette("viridis", 10))
    axes[0, 0].set_title("Top 10 Movies by Revenue", fontsize=11, fontweight="bold")
    axes[0, 0].set_xlabel("Revenue (USD Billion)")
    axes[0, 0].xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"${x:.1f}B"))

    # Panel B: rating distribution
    sns.histplot(df["vote_average"].dropna(), bins=15, kde=True,
                 color="#1a6faf", ax=axes[0, 1])
    axes[0, 1].set_title("Rating Distribution", fontsize=11, fontweight="bold")
    axes[0, 1].set_xlabel("Vote Average")
    axes[0, 1].set_ylabel("Count")

    # Panel C: genre counts
    counts = df["primary_genre"].value_counts().head(8)
    axes[1, 0].bar(counts.index, counts.values,
                   color=sns.color_palette("viridis", len(counts)))
    axes[1, 0].set_title("Movies per Genre (top 8)", fontsize=11, fontweight="bold")
    axes[1, 0].set_xlabel("Genre")
    axes[1, 0].set_ylabel("Count")
    axes[1, 0].tick_params(axis="x", rotation=30)

    # Panel D: budget vs revenue
    data = df[(df["budget_usd"] > 0) & (df["revenue_usd"] > 0)].copy()
    axes[1, 1].scatter(data["budget_usd"] / 1e6, data["revenue_usd"] / 1e6,
                       c=data["vote_average"], cmap="viridis",
                       alpha=0.65, edgecolors="none", s=40)
    max_v = max(data["budget_usd"].max(), data["revenue_usd"].max()) / 1e6 * 1.05
    axes[1, 1].plot([0, max_v], [0, max_v], "--", color="gray", linewidth=1)
    axes[1, 1].set_title("Budget vs Revenue", fontsize=11, fontweight="bold")
    axes[1, 1].set_xlabel("Budget (USD Million)")
    axes[1, 1].set_ylabel("Revenue (USD Million)")

    fig.tight_layout()
    return _save(fig, "dashboard_subplots", out_dir)
