"""
Interactive visualization module for Movie Industry Analytics Pipeline.
Uses Plotly Express (and Graph Objects for the multi-layout chart).
Lab 12 - Data Visualization
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

INTERACTIVE_OUT = Path("outputs/visualizations/interactive")
TEMPLATE = "plotly_white"


def _save_html(fig: go.Figure, stem: str,
               out_dir: Path = INTERACTIVE_OUT) -> str:
    """Write an interactive HTML file. Returns the file path as string."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.html"
    fig.write_html(str(path))
    logger.info("Saved interactive chart: %s", path)
    return str(path)


# ── 1. Scatter – Budget vs Revenue (interactive) ─────────────────────────────
def interactive_budget_vs_revenue(df: pd.DataFrame,
                                  out_dir: Path = INTERACTIVE_OUT) -> str:
    """Interactive scatter: production budget vs box-office revenue."""
    data = df[(df["budget_usd"] > 0) & (df["revenue_usd"] > 0)].copy()
    data["budget_M"] = (data["budget_usd"] / 1e6).round(1)
    data["revenue_M"] = (data["revenue_usd"] / 1e6).round(1)
    data["roi"] = ((data["revenue_usd"] - data["budget_usd"]) /
                   data["budget_usd"] * 100).round(1)

    fig = px.scatter(
        data,
        x="budget_M",
        y="revenue_M",
        color="primary_genre",
        size="vote_count",
        hover_name="title",
        hover_data={
            "release_year": True,
            "vote_average": ":.2f",
            "roi": ":.1f",
            "budget_M": ":.1f",
            "revenue_M": ":.1f",
        },
        labels={"budget_M": "Budget (USD M)", "revenue_M": "Revenue (USD M)"},
        title="Budget vs Box-Office Revenue – Interactive Explorer",
        template=TEMPLATE,
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )

    # break-even reference line
    max_v = max(data["budget_M"].max(), data["revenue_M"].max()) * 1.05
    fig.add_trace(go.Scatter(
        x=[0, max_v], y=[0, max_v],
        mode="lines",
        line=dict(dash="dash", color="gray", width=1),
        name="Break-even",
        hoverinfo="skip",
    ))

    fig.update_layout(
        legend_title="Genre",
        font=dict(family="Inter", size=13),
        height=580,
    )
    return _save_html(fig, "budget_vs_revenue_interactive", out_dir)


# ── 2. Bar – Top 10 movies by popularity ─────────────────────────────────────
def interactive_top_movies_bar(df: pd.DataFrame, n: int = 10,
                               out_dir: Path = INTERACTIVE_OUT) -> str:
    """Interactive grouped bar: top-n movies by popularity and revenue."""
    top = df.nlargest(n, "popularity")[
        ["title", "popularity", "revenue_usd", "vote_average",
         "release_year", "primary_genre"]
    ].copy()
    top["revenue_M"] = (top["revenue_usd"] / 1e6).round(1)

    fig = px.bar(
        top.sort_values("popularity", ascending=True),
        x="popularity",
        y="title",
        orientation="h",
        color="primary_genre",
        hover_name="title",
        hover_data={
            "release_year": True,
            "vote_average": ":.2f",
            "revenue_M": ":.1f",
            "popularity": ":.2f",
        },
        labels={"popularity": "TMDB Popularity Score", "title": "Movie"},
        title=f"Top {n} Movies by TMDB Popularity Score",
        template=TEMPLATE,
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig.update_layout(
        legend_title="Genre",
        font=dict(family="Inter", size=13),
        height=500,
    )
    return _save_html(fig, "top_movies_popularity_bar", out_dir)


# ── 3. Line – Movies released per year ────────────────────────────────────────
def interactive_movies_per_year(df: pd.DataFrame,
                                out_dir: Path = INTERACTIVE_OUT) -> str:
    """Interactive line: number of movies released per year (1980–2025)."""
    yearly = (df.query("release_year >= 1980 and release_year <= 2025")
               .groupby("release_year")
               .agg(
                   movie_count=("title", "count"),
                   avg_rating=("vote_average", "mean"),
                   total_revenue_B=("revenue_usd", lambda s: (s.sum() / 1e9).round(2)),
               )
               .reset_index())

    fig = px.line(
        yearly,
        x="release_year",
        y="movie_count",
        markers=True,
        hover_data={
            "avg_rating": ":.2f",
            "total_revenue_B": ":.2f",
            "movie_count": True,
        },
        labels={"release_year": "Year", "movie_count": "Number of Movies"},
        title="Movies Released per Year (1980–2025)",
        template=TEMPLATE,
    )
    fig.update_traces(line_color="#1a6faf", line_width=2.5,
                      marker=dict(size=7))
    fig.update_layout(font=dict(family="Inter", size=13), height=450)
    return _save_html(fig, "movies_per_year_line", out_dir)


# ── 4. Box – Vote average by genre (interactive) ─────────────────────────────
def interactive_genre_boxplot(df: pd.DataFrame,
                              out_dir: Path = INTERACTIVE_OUT) -> str:
    """Interactive box plot: vote_average distribution per primary_genre."""
    order = (df.groupby("primary_genre")["vote_average"]
               .median().sort_values(ascending=False).index.tolist())

    fig = px.box(
        df,
        x="primary_genre",
        y="vote_average",
        category_orders={"primary_genre": order},
        color="primary_genre",
        hover_name="title",
        hover_data={"release_year": True, "vote_average": ":.2f"},
        labels={"primary_genre": "Genre", "vote_average": "Vote Average (0–10)"},
        title="Movie Rating Distribution by Genre",
        template=TEMPLATE,
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig.update_layout(
        showlegend=False,
        font=dict(family="Inter", size=13),
        height=500,
    )
    return _save_html(fig, "genre_rating_boxplot_interactive", out_dir)


# ── 5. Multi-layout – 2×2 interactive dashboard ──────────────────────────────
def interactive_multi_layout(df: pd.DataFrame,
                              out_dir: Path = INTERACTIVE_OUT) -> str:
    """2×2 Plotly subplot combining revenue, ratings, genre, and timeline."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Top 10 Movies by Revenue",
            "Rating Distribution",
            "Movies per Genre",
            "Budget vs Revenue",
        ),
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    # Panel 1 – top 10 revenue bar
    top10 = (df[df["revenue_usd"] > 0]
             .nlargest(10, "revenue_usd")
             .sort_values("revenue_usd"))
    fig.add_trace(
        go.Bar(x=top10["revenue_usd"] / 1e9, y=top10["title"],
               orientation="h",
               marker_color="#1a6faf",
               name="Revenue (B)",
               hovertemplate="%{y}<br>$%{x:.2f}B<extra></extra>"),
        row=1, col=1,
    )

    # Panel 2 – rating histogram
    fig.add_trace(
        go.Histogram(x=df["vote_average"].dropna(), nbinsx=20,
                     marker_color="#2ca02c", name="Ratings",
                     hovertemplate="Rating: %{x}<br>Count: %{y}<extra></extra>"),
        row=1, col=2,
    )

    # Panel 3 – genre count bar
    counts = df["primary_genre"].value_counts()
    fig.add_trace(
        go.Bar(x=counts.index, y=counts.values,
               marker_color="#ff7f0e", name="Genre count",
               hovertemplate="%{x}: %{y} movies<extra></extra>"),
        row=2, col=1,
    )

    # Panel 4 – budget vs revenue scatter
    scatter_data = df[(df["budget_usd"] > 0) & (df["revenue_usd"] > 0)]
    fig.add_trace(
        go.Scatter(
            x=scatter_data["budget_usd"] / 1e6,
            y=scatter_data["revenue_usd"] / 1e6,
            mode="markers",
            marker=dict(
                color=scatter_data["vote_average"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Rating", x=1.02, len=0.45, y=0.12),
                size=8, opacity=0.7,
            ),
            text=scatter_data["title"],
            name="Movies",
            hovertemplate="%{text}<br>Budget: $%{x:.0f}M<br>Revenue: $%{y:.0f}M<extra></extra>",
        ),
        row=2, col=2,
    )

    fig.update_layout(
        title_text="Movie Industry Analytics Dashboard",
        title_font=dict(size=18),
        template=TEMPLATE,
        height=700,
        width=1100,
        showlegend=False,
        font=dict(family="Inter", size=11),
    )
    # axis labels
    fig.update_xaxes(title_text="Revenue (USD B)", row=1, col=1)
    fig.update_xaxes(title_text="Vote Average", row=1, col=2)
    fig.update_xaxes(title_text="Genre", row=2, col=1)
    fig.update_xaxes(title_text="Budget (USD M)", row=2, col=2)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    fig.update_yaxes(title_text="Revenue (USD M)", row=2, col=2)

    return _save_html(fig, "interactive_dashboard", out_dir)
