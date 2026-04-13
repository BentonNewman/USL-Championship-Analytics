"""Shared utilities for ASA Soccer Data notebooks."""

from __future__ import annotations

import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_PURPLE: str = "#400077"
_GOLD: str = "#b28350"
_ROW_EVEN: str = "#f5f0fa"
_ROW_ODD: str = "#ffffff"
_MEDAL_GOLD: str = "#FFD700"
_MEDAL_SILVER: str = "#C0C0C0"
_MEDAL_BRONZE: str = "#CD7F32"


def resolve_team(val: str | list[str], team_map: dict[str, str]) -> str | float:
    """Map a team_id (or list of team_ids) to its abbreviation(s).

    Players who transferred mid-season arrive with a list of team_ids;
    those are joined with '/' (e.g. 'LOU/IND'). Unknown IDs fall back to
    the raw ID string. NaN/None values pass through unchanged.
    """
    if isinstance(val, list):
        return "/".join(team_map.get(v, v) for v in val)
    return team_map.get(val, val)


def flatten_goals_added(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten an ASA goals-added frame's nested `data` column into wide form.

    The API returns one row per (player, season) with `data` holding a list
    of dicts — one per action_type. This explodes to long form, normalizes
    the dicts, then pivots to one column per (metric, action_type). Also
    adds total ga_raw / ga_aboveavg sums across all action types.
    """
    long = df.explode("data", ignore_index=True)
    long = long.join(pd.json_normalize(long.pop("data")))
    long["action_type"] = long["action_type"].str.lower()
    wide = long.pivot(
        index=["player_id", "season_name"],
        columns="action_type",
        values=["goals_added_raw", "goals_added_above_avg", "count_actions"],
    )
    metric_map = {
        "goals_added_raw": "ga_raw",
        "goals_added_above_avg": "ga_aboveavg",
        "count_actions": "ga_actions",
    }
    wide.columns = [f"{metric_map[m]}_{a}" for m, a in wide.columns]
    wide = wide.reset_index()
    raw_cols = [c for c in wide.columns if c.startswith("ga_raw_")]
    aboveavg_cols = [c for c in wide.columns if c.startswith("ga_aboveavg_")]
    wide["ga_raw_total"] = wide[raw_cols].sum(axis=1)
    wide["ga_aboveavg_total"] = wide[aboveavg_cols].sum(axis=1)
    ga_value_cols = [
        c for c in wide.columns if c.startswith(("ga_raw_", "ga_aboveavg_"))
    ]
    wide[ga_value_cols] = wide[ga_value_cols].round(3)
    return wide


def assign_result(
    df: pd.DataFrame, home_col: str, away_col: str, new_col: str = "result"
) -> pd.DataFrame:
    """Return df with a new column: home team name, away team name, or 'DRAW'."""
    result = np.select(
        [df[home_col] > df[away_col], df[home_col] < df[away_col]],
        [df["home_team"], df["away_team"]],
        default="DRAW",
    )
    return df.assign(**{new_col: result})


def render_table(
    df: pd.DataFrame,
    title: str,
    col_formats: dict[str, str] | None = None,
    figsize: tuple[float, float] | None = None,
    accent_color: str = _PURPLE,
    rank_cols: dict[str, str] | None = None,
) -> plt.Figure:
    """Render a DataFrame as a styled matplotlib table.

    Args:
        df: Data to display. Index is not shown.
        title: Text displayed above the table.
        col_formats: Optional map of column name → Python format spec
            (e.g. ``{"xgf": ".2f", "pts": "d"}``). Unspecified columns
            use default string conversion.
        figsize: Figure size in inches. Derived from table dimensions
            if None.
        accent_color: Hex color for the header row and title. Defaults to
            Louisville City purple. Pass ``"#b28350"`` for league-wide /
            non-LOU visuals.
        rank_cols: Optional map of column name → ``"high"`` or ``"low"``,
            indicating which direction is best. The top 3 rows per column
            receive gold / silver / bronze cell highlights. Ties share the
            same medal (``rank(method="min")``). Columns absent from the
            DataFrame are silently skipped.

    Returns:
        A matplotlib Figure ready for display or saving.
    """

    if col_formats is None:
        col_formats = {}

    cell_text: list[list[str]] = []
    for _, row in df.iterrows():
        formatted: list[str] = []
        for col in df.columns:
            val = row[col]
            fmt = col_formats.get(str(col))
            is_null = (
                val is None
                or val is pd.NA
                or (isinstance(val, float) and np.isnan(val))
            )
            if fmt is not None and not is_null:
                try:
                    formatted.append(format(val, fmt))
                except (TypeError, ValueError):
                    formatted.append(str(val))
            else:
                formatted.append("" if is_null else str(val))
        cell_text.append(formatted)

    n_rows, n_cols = len(df), len(df.columns)
    if figsize is None:
        figsize = (max(6.0, n_cols * 1.4), max(1.5, n_rows * 0.42 + 0.6))

    # Build medal lookup: (tbl_row_idx, col_idx) -> color.
    # tbl_row_idx is 1-based because matplotlib reserves row 0 for headers.
    # df must have a contiguous RangeIndex (reset_index(drop=True)) for the
    # +1 offset to map correctly.
    _medal_map: dict[int, str] = {1: _MEDAL_GOLD, 2: _MEDAL_SILVER, 3: _MEDAL_BRONZE}
    medal_cells: dict[tuple[int, int], str] = {}
    if rank_cols:
        col_names = list(df.columns)
        for col_name, direction in rank_cols.items():
            if col_name not in col_names:
                continue
            col_idx = col_names.index(col_name)
            ascending = direction == "low"
            ranks = df[col_name].rank(
                method="min", ascending=ascending, na_option="bottom"
            )
            for df_row_idx, rank_val in enumerate(ranks):
                rank_int = int(rank_val)
                if rank_int in _medal_map:
                    medal_cells[(df_row_idx + 1, col_idx)] = _medal_map[rank_int]

    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")

    row_colors = [
        [_ROW_EVEN if i % 2 == 0 else _ROW_ODD] * n_cols for i in range(n_rows)
    ]

    tbl = ax.table(
        cellText=cell_text,
        colLabels=list(df.columns),
        cellColours=row_colors,
        bbox=[0, 0, 1, 1],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)

    for (row_idx, col_idx), cell in tbl.get_celld().items():
        cell.set_text_props(ha="center")
        if row_idx == 0:
            cell.set_facecolor(accent_color)
            cell.set_text_props(color="white", fontweight="bold", ha="center")
        elif (row_idx, col_idx) in medal_cells:
            cell.set_facecolor(medal_cells[(row_idx, col_idx)])

    fig.suptitle(title, fontsize=13, fontweight="bold", color=accent_color, y=0.98)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.04)

    today = datetime.date.today().strftime("%Y-%m-%d")
    fig.text(0.01, 0.025, "VamosMorados.com", ha="left", fontsize=8, color="gray")
    fig.text(0.99, 0.025, f"Generated on {today}", ha="right", fontsize=8, color="gray")

    return fig
