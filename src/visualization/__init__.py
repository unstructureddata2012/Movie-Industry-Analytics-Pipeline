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
from .interactive_charts import (
    interactive_budget_vs_revenue,
    interactive_top_movies_bar,
    interactive_movies_per_year,
    interactive_genre_boxplot,
    interactive_multi_layout,
)

__all__ = [
    "plot_top_movies_by_revenue",
    "plot_avg_rating_over_years",
    "plot_budget_vs_revenue_scatter",
    "plot_rating_distribution",
    "plot_genre_rating_boxplot",
    "plot_correlation_heatmap",
    "plot_genre_count_bar",
    "plot_dashboard_subplots",
    "interactive_budget_vs_revenue",
    "interactive_top_movies_bar",
    "interactive_movies_per_year",
    "interactive_genre_boxplot",
    "interactive_multi_layout",
]
