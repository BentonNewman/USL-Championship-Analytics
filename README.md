# USL Championship Analytics

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Data: ASA](https://img.shields.io/badge/data-American%20Soccer%20Analysis-orange.svg)](https://americansocceranalysis.com)

Python notebooks that expand USL Championship data from the [American Soccer Analysis](https://americansocceranalysis.com) public API into analysis-ready DataFrames. Each notebook is a self-contained data pipeline designed to serve as a template for further statistical work, visualization, or modeling.

---

## Table of Contents

- [Data Source](#data-source)
- [Data Coverage](#data-coverage)
- [Project Structure](#project-structure)
- [Notebooks](#notebooks)
  - [Game Data](#usl_championship_game_dataipynb--games)
  - [Player Data](#usl_championship_player_dataipynb--players-gk_players)
  - [Team Data](#usl_championship_team_dataipynb--team_stats)
- [Setup](#setup)
- [Using These as Templates](#using-these-as-templates)
- [Adapting to Other Leagues](#adapting-to-other-leagues)
- [Key Metrics](#key-metrics)
- [Notes & Limitations](#notes--limitations)
- [Acknowledgements](#acknowledgements)
- [License](#license)

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
USL_Championship_Game_Data.ipynb     Match results, xG, xPoints, weather, travel
USL_Championship_Player_Data.ipynb   Outfield and goalkeeper player-season metrics
USL_Championship_Team_Data.ipynb     Team-season aggregates and advanced metrics
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

Dependencies are listed in [`requirements.txt`](requirements.txt) and are intentionally unpinned to support a range of recent versions. Pin them yourself if you need a fully reproducible environment.

### Run a notebook

Open interactively:

```bash
jupyter notebook USL_Championship_Game_Data.ipynb
```

Or execute headlessly and write outputs back to the file:

```bash
jupyter nbconvert --to notebook --execute USL_Championship_Game_Data.ipynb \
  --output USL_Championship_Game_Data.ipynb
```

---

## Using These as Templates

Each notebook ends with a `display(df.head())` call and is intentionally left without an analysis section. The pipelines produce clean, enriched DataFrames — everything after that is yours to build.

**Suggested workflow:**

1. Run the notebook to build the canonical DataFrame
2. Add analysis cells below — filtering, grouping, aggregating, visualizing, or exporting
3. Change the `FOCUS_TEAM` constant in `USL_Championship_Team_Data.ipynb` to any team abbreviation to repoint the focus section

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
- **Notebook outputs are committed**: The `.ipynb` files include their last-executed output cells so the data is visible directly on GitHub without running anything. Re-execute locally to refresh against the latest API data.
- **No analysis layer**: These are data-prep templates by design. They produce clean DataFrames and stop. Visualization, modeling, and reporting are intentionally left to downstream notebooks.

---

## Acknowledgements

This project is built entirely on top of the work of **[American Soccer Analysis](https://americansocceranalysis.com)** and their open-source [`itscalledsoccer`](https://github.com/American-Soccer-Analysis/itscalledsoccer) package. All advanced metrics (xG, xPass, Goals Added) are their methodology and intellectual property. Please refer to their site and documentation for full details.

---

## License

This project is licensed under the [MIT License](LICENSE). You are free to use, modify, and distribute these notebooks for any purpose, including commercial use, with attribution.

Note that data returned by the ASA API is subject to American Soccer Analysis's own terms of use.
