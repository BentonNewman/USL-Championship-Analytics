# USL Championship Analytics

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Data: ASA](https://img.shields.io/badge/data-American%20Soccer%20Analysis-orange.svg)](https://americansocceranalysis.com)

Python notebooks that expand USL Championship data from the [American Soccer Analysis](https://americansocceranalysis.com) public API into analysis-ready DataFrames. Each notebook is a self-contained data pipeline designed to serve as a template for further statistical work, visualization, or modeling.

---

## Table of Contents

- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Data Source](#data-source)
- [Data Coverage](#data-coverage)
- [Project Structure](#project-structure)
- [Notebooks](#notebooks)
  - [Game Data](#usl_championship_game_dataipynb--games)
  - [Player Data](#usl_championship_player_dataipynb--players-gk_players)
  - [Team Data](#usl_championship_team_dataipynb--team_stats)
  - [Visualizations](#usl_championship_visualizationsipynb--team_view)
- [Setup](#setup)
- [Using These as Templates](#using-these-as-templates)
- [Adapting to Other Leagues](#adapting-to-other-leagues)
- [Key Metrics](#key-metrics)
- [Notes & Limitations](#notes--limitations)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Fetch all data and build the parquet cache (runs all three pipelines in parallel)
python scripts/update_parquets.py

# 3. Open the analysis notebook and start exploring
jupyter notebook notebooks/USL_Championship_Visualizations.ipynb
```

Step 2 is the only step that requires an internet connection. Once `data/` is populated, the Visualizations notebook runs entirely from local parquet files — no API calls, fast iteration.

To refresh data (new matches, updated metrics), re-run step 2.

---

## How It Works

This project is structured in two tiers: a **data pipeline** that fetches and enriches raw API data, and an **analysis layer** that reads the results and builds on them.

```
┌─────────────────────────────────────────────────────────────┐
│  DATA PIPELINE  (run once, or to refresh)                   │
│                                                             │
│  ASA API (itscalledsoccer)                                  │
│      │                                                      │
│      ├── Game Data notebook   ──→  data/games.parquet       │
│      ├── Player Data notebook ──→  data/players.parquet     │
│      │                             data/gk_players.parquet  │
│      └── Team Data notebook   ──→  data/team_stats.parquet  │
│                                                             │
│  scripts/update_parquets.py runs all three in parallel.     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼  (parquet files are the boundary)
┌─────────────────────────────────────────────────────────────┐
│  ANALYSIS LAYER  (iterate freely, no API needed)            │
│                                                             │
│  USL_Championship_Visualizations.ipynb                      │
│      Reads all four parquets, builds team_view, produces    │
│      tables and visuals scoped to a single TEAM constant.   │
│                                                             │
│  scripts/utils.py                                           │
│      Shared helpers imported by any notebook:               │
│        render_table()    — styled matplotlib table          │
│        resolve_team()    — team_id → abbreviation           │
│        flatten_goals_added() — unnest Goals Added data      │
│        assign_result()   — derive W/D/L from scores         │
└─────────────────────────────────────────────────────────────┘
```

**The parquet files in `data/` are the handoff point.** The three pipeline notebooks write them; the Visualizations notebook reads them. This separation means:

- You can explore and build visuals without waiting for API calls on every run.
- Refreshing data is a single command (`update_parquets.py`) with no changes to the analysis notebook.
- The pipeline notebooks can be re-run independently if only one data source needs updating.

**Changing focus team:** Set `TEAM` at the top of `USL_Championship_Visualizations.ipynb` to any team abbreviation (e.g. `"PHX"`, `"SA"`, `"CIN"`) and re-run the notebook. No pipeline re-run needed. Team abbreviations follow ASA convention — see [Using These as Templates](#using-these-as-templates) for how to look them up.

---

## Data Source

All data is sourced from **[American Soccer Analysis](https://americansocceranalysis.com)** via their open-source Python client:

> **[itscalledsoccer](https://github.com/American-Soccer-Analysis/itscalledsoccer)** — a Python (and R) wrapper for the ASA public API, providing access to xG, xPass, Goals Added, and other advanced metrics across multiple professional soccer leagues.

This project does not collect, store, or redistribute any data independently. Every data fetch runs live against the ASA API at notebook execution time. All advanced metrics — xG, xPass, and Goals Added — are the methodology and intellectual property of American Soccer Analysis.

---

## Data Coverage

| League | Code | Seasons Available |
|--------|------|-------------------|
| USL Championship | `uslc` | 2017 – present |

These notebooks target `uslc` by default. The `itscalledsoccer` package supports additional leagues — see [Adapting to Other Leagues](#adapting-to-other-leagues) below.

---

## Project Structure

```
notebooks/
  USL_Championship_Game_Data.ipynb         Match results, xG, xPoints, weather, travel
  USL_Championship_Player_Data.ipynb       Outfield and goalkeeper player-season metrics
  USL_Championship_Team_Data.ipynb         Team-season aggregates and advanced metrics
  USL_Championship_Visualizations.ipynb    Team-focused analysis layer built on the above
scripts/
  update_parquets.py                       Runs all three data notebooks in parallel
  utils.py                                 Shared helpers (render_table, resolve_team, etc.)
data/                                      Parquet outputs (gitignored, generated on run)
```

The notebooks import shared functions from `scripts/utils.py` rather than redefining them inline. Any notebook can use these helpers:

```python
import sys
sys.path.insert(0, "../scripts")
from utils import render_table, resolve_team, flatten_goals_added, assign_result
```

---

## Notebooks

### `USL_Championship_Game_Data.ipynb` → `games`

Match-level pipeline covering every completed USL Championship regular season game.

- Resolves team, manager, referee, and stadium IDs to readable names
- Derives per-team cumulative stats within each season: season points, points per game, game number, and days rest between matches
- Merges per-game xG and xPoints from the ASA xGoals endpoint
- Computes away travel distance in miles (geodesic) via ZIP code lookup using `pgeocode` and `geopy`
- Enriches completed matches with venue weather from the [Open-Meteo](https://open-meteo.com) archive API: high/low temperature (°F), precipitation (in), and snowfall (in), resolved to the correct local timezone per venue

**Sample output columns** (full frame contains ~45 columns): `game_id`, `season_name`, `matchday`, `date`, `home_team`, `away_team`, `home_score`, `away_score`, `result`, `home_pts`, `away_pts`, `home_season_pts`, `home_ppg`, `home_days_rest`, `home_team_xgoals`, `away_team_xgoals`, `xresult`, `home_xpoints`, `away_xpoints`, `away_travel_distance`, `temp_max_f`, `temp_min_f`, `precip_in`, `snowfall_in`.

---

### `USL_Championship_Player_Data.ipynb` → `players`, `gk_players`

Player-season pipeline split into outfield and goalkeeper frames. All data is Regular Season only.

**Outfield (`players`)** — no minimum minutes threshold:

- Shooting volume and efficiency: rate stats per minute and per shot
- Per-90 normalization for goals, assists, shots, key passes, and Goals Added
- Goals Added broken out by action type — dribbling, fouling, interrupting, passing, receiving, and shooting — with raw value, above-average value, and action count columns for each
- Player attributes: age at season, multi-team flag for mid-season transfers, and broad position group (Defender / Midfielder / Attacker / Goalkeeper)
- Within-position, within-season percentile ranks for 12 key metrics

**Goalkeepers (`gk_players`)** — minimum 100 minutes played and at least one shot faced:

- Save percentage, shots/goals/saves per 90, and xG-based overperformance metrics
- Goals Added broken out by action type — claiming, fielding, handling, passing, shotstopping, and sweeping
- Estimated games played derived from minutes played
- Within-season percentile ranks for six key metrics, with higher-better and lower-better metrics ranked correctly

**Sample output columns** (outfield frame contains ~85 columns; GK frame ~50): `player_name`, `age`, `nationality`, `HEIGHT`, `team_name`, `season_name`, `general_position`, `position_group`, `is_multi_team`, `minutes_played`, `goals`, `xgoals`, `G_p90`, `xG_p90`, `ga_raw_total`, `ga_raw_p90`, `G_p90_pct`, `xG_p90_pct`.

---

### `USL_Championship_Team_Data.ipynb` → `team_stats`

Team-season pipeline aggregating xGoals, xPass, and Goals Added into a single frame. Covers all USL Championship teams from 2017 to present.

- Per-game rates for shots, goals, xG, points, and passes
- Finishing overperformance (goals vs xG) and defensive overperformance (xGA vs goals conceded)
- Shot quality: xG per shot for and against
- Pass share as a possession proxy (team pass volume / total passes in match)
- Goals Added flattened from the nested API format into per-action-type columns (7 action types) with for, against, and net difference splits, plus per-96-minute normalized versions
- Season-over-season deltas for seven key rate metrics
- Within-season percentile ranks for twelve metrics, with defensive metrics ranked correctly

The `FOCUS_TEAM` constant at the top of the notebook (default: `LOU`) isolates all seasons for a single team in a dedicated section at the bottom.

**Sample output columns** (full frame contains ~110 columns): `team_name`, `season_name`, `count_games`, `pts_per_game`, `xpts_per_game`, `goals_per_game`, `xg_per_game`, `xg_per_shot_for`, `pass_share`, `ga_for_total`, `ga_difference`, `pts_per_game_pct`, `pts_per_game_yoy`.

---

### `USL_Championship_Visualizations.ipynb` → `team_view`

Team-focused analysis notebook that reads the parquet files produced by the three template notebooks and builds on them. Run the template notebooks at least once to populate `data/` before using this notebook.

- `TEAM` constant (default: `LOU`) controls which team all frames and views are scoped to — change it once at the top and re-run
- Derives `team_games` from the full `games` frame — all matches involving the selected team
- Builds `team_view`: a flattened, team-perspective DataFrame that resolves every home/away column pair into a single team-neutral value — goals for/against, xGF/xGA, W/D/L result, points, season points, PPG, xPoints, game number, days rest, and travel distance
- Serves as the starting point for further analysis: YoY comparisons, form tables, rolling averages, visualizations

**`team_view` columns**: `is_home`, `opponent`, `manager`, `opponent_manager`, `referee`, `venue`, `venue_city`, `venue_state`, `gf`, `ga`, `goal_diff`, `result` (W/D/L), `pts`, `season_pts`, `ppg`, `xgf`, `xga`, `xg_diff`, `xresult`, `xpts`, `game_number`, `days_rest`, `travel_distance`, plus weather columns where available.

---

## Setup

### Requirements

- Python 3.10+
- Internet access (all data is fetched live from the ASA API at runtime)

### Install dependencies

Clone the repository:

```bash
git clone https://github.com/BentonNewman/USL-Championship-Analytics.git
cd USL-Championship-Analytics
```

**With pip (works in any virtual environment):**

```bash
pip install -r requirements.txt
```

**With [uv](https://github.com/astral-sh/uv) (recommended for speed):**

```bash
uv pip install -r requirements.txt
```

Dependencies are listed in [`requirements.txt`](requirements.txt) and are intentionally unpinned to support a range of recent versions. [`requirements-lock.txt`](requirements-lock.txt) provides a fully pinned snapshot for exact reproducibility.

### Configure notebook git filter

This repo uses [`nbstripout`](https://github.com/kynan/nbstripout) to strip notebook outputs automatically before each commit, keeping diffs readable. After installing dependencies, run once per clone:

```bash
nbstripout --install
```

This writes the filter into your local `.git/config` and does not affect notebook files themselves.

### Run a notebook

Open interactively:

```bash
jupyter notebook notebooks/USL_Championship_Game_Data.ipynb
```

Or execute all three data notebooks headlessly in parallel (recommended):

```bash
python scripts/update_parquets.py
```

Or execute a single notebook headlessly:

```bash
jupyter nbconvert --to notebook --execute notebooks/USL_Championship_Game_Data.ipynb \
  --output notebooks/USL_Championship_Game_Data.ipynb
```

---

## Using These as Templates

The three template notebooks produce clean, enriched DataFrames and end with a `display(df.head())` call. `USL_Championship_Visualizations.ipynb` is the provided downstream analysis layer — built on top of those outputs and scoped to a single team via the `TEAM` constant.

**Suggested workflow:**

1. Run the three template notebooks to populate `data/` with parquet files
2. Open `USL_Championship_Visualizations.ipynb`, set `TEAM` to the desired team abbreviation, and run
3. Add analysis cells below `team_view` — the flattened team-perspective DataFrame is the primary building block
4. To change focus teams, update `TEAM` and re-run from that cell down — no need to re-run the data pipeline
5. Change `FOCUS_TEAM` in `USL_Championship_Team_Data.ipynb` to repoint the league-wide team comparison section

**Example — top teams by points per game:**

```python
top = (
    team_stats.query("count_games >= 20")
    .sort_values("pts_per_game", ascending=False)
    .head(10)[["team_name", "season_name", "count_games", "pts_per_game", "xpts_per_game"]]
)
display(top)
```

**Example — outfield players with the highest xG per 90 in a given season:**

```python
display(
    players.query("season_name == 2025 and minutes_played >= 500")
    .nlargest(20, "xG_p90")[["player_name", "team_name", "general_position", "minutes_played", "xG_p90", "xG_p90_pct"]]
)
```

Team abbreviations follow the ASA convention (e.g. `LOU`, `PHX`, `SA`). To get a full list:

```python
from itscalledsoccer.client import AmericanSoccerAnalysis
asa_client = AmericanSoccerAnalysis()
teams = asa_client.get_teams(leagues=["uslc"])
print(teams[["team_abbreviation", "team_name"]].sort_values("team_abbreviation"))
```

---

## Adapting to Other Leagues

These notebooks target `uslc` via a `LEAGUE` constant defined in the first code cell of each notebook. Changing that constant to any supported league code will repoint all ASA API calls.

| League | Code | Division |
|--------|------|----------|
| USL Championship | `uslc` | Men's Div II |
| MLS | `mls` | Men's Div I |
| MLS Next Pro | `mlsnp` | Men's Div II |
| USL League One | `usl1` | Men's Div III |
| NWSL | `nwsl` | Women's Div I |
| USL Super League | `usls` | Women's Div I |

**Caveats when adapting:**

- Available seasons, team counts, and data completeness vary by league. See the [itscalledsoccer documentation](https://github.com/American-Soccer-Analysis/itscalledsoccer) for coverage details.
- The Game Data notebook uses `pgeocode.Nominatim("us")`, which only resolves US ZIP codes. Travel distance and weather features will return `NaN` for non-US teams (e.g. Canadian MLS clubs). To support other countries, change the country code or use a multi-country lookup.
- Weather is fetched from Open-Meteo using US state-to-timezone mappings. Non-US venues will fall back to `America/New_York` for daily boundaries unless you extend the `_STATE_TIMEZONE` dictionary.

---

## Key Metrics

| Metric | Description |
|--------|-------------|
| **xG** | Expected goals — probability a shot results in a goal based on location, body part, and context |
| **xPass** | Expected pass completion — evaluates pass difficulty relative to execution |
| **Goals Added (g+)** | ASA's all-in-one contribution metric — every on-ball action quantified in goal units, summable across action types |
| **xPoints** | Expected points from a match based on xG, accounting for all possible scorelines |

Full metric documentation: [americansocceranalysis.com](https://americansocceranalysis.com)

---

## Notes & Limitations

- **Live API calls**: Every notebook execution makes fresh API requests. There is no local cache. Weather fetches in particular can take 30+ seconds for the full season range.
- **API rate limits**: Be considerate with the ASA API. Avoid running the notebooks repeatedly in tight loops.
- **Open-Meteo dependency**: The Game Data notebook depends on the [Open-Meteo](https://open-meteo.com) archive API for weather data. This is a separate free public service. Weather fetches gracefully degrade to `NaN` if the request fails.
- **Future games**: The Game Data notebook filters to `status == "FullTime"`, so unplayed fixtures are excluded. Weather is only fetched for past dates.
- **Notebook outputs**: This repo uses [`nbstripout`](https://github.com/kynan/nbstripout) — outputs are stripped automatically on commit. Re-execute the notebooks locally (or run `python scripts/update_parquets.py`) to populate `data/` and see results.
- **Downstream analysis**: The three template notebooks are data-prep pipelines by design — they produce clean DataFrames and write parquet files. `USL_Championship_Visualizations.ipynb` is the provided analysis layer built on top of them. Add your own analysis cells there or create additional notebooks that read from `data/`.

---

## Acknowledgements

This project is built entirely on top of the work of **[American Soccer Analysis](https://americansocceranalysis.com)** and their open-source [`itscalledsoccer`](https://github.com/American-Soccer-Analysis/itscalledsoccer) package. All advanced metrics (xG, xPass, Goals Added) are their methodology and intellectual property. Please refer to their site and documentation for full details.

---

## License

This project is licensed under the [MIT License](LICENSE). You are free to use, modify, and distribute these notebooks for any purpose, including commercial use, with attribution.

Note that data returned by the ASA API is subject to American Soccer Analysis's own terms of use.
