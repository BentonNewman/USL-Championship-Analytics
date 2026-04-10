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

    for (row_idx, _), cell in tbl.get_celld().items():
        cell.set_text_props(ha="center")
        if row_idx == 0:
            cell.set_facecolor(_PURPLE)
            cell.set_text_props(color="white", fontweight="bold", ha="center")

    fig.suptitle(title, fontsize=13, fontweight="bold", color=_PURPLE, y=0.98)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.84, bottom=0.08)

    today = datetime.date.today().strftime("%Y-%m-%d")
    fig.text(0.01, 0.025, "VamosMorados.com", ha="left", fontsize=8, color="gray")
    fig.text(0.99, 0.025, f"Generated on {today}", ha="right", fontsize=8, color="gray")

    return fig
