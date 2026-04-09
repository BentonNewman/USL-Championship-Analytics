"""Execute the three USLC data notebooks in parallel and refresh all parquet files."""

import logging
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Final

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# scripts/ -> project root
PROJECT_DIR: Final[Path] = Path(__file__).parent.parent
NOTEBOOKS_DIR: Final[Path] = PROJECT_DIR / "notebooks"

# Maps each notebook to the parquet(s) it is expected to write (relative to PROJECT_DIR).
# All three run in parallel — none share output files or intermediate state.
NOTEBOOK_OUTPUTS: Final[dict[str, list[str]]] = {
    "USL_Championship_Game_Data.ipynb": ["data/games.parquet"],
    "USL_Championship_Team_Data.ipynb": ["data/team_stats.parquet"],
    "USL_Championship_Player_Data.ipynb": ["data/players.parquet", "data/gk_players.parquet"],
}


def run_notebook(notebook: str) -> tuple[str, bool, str]:
    """Execute a notebook in-place and verify expected parquet outputs were written.

    Uses sys.executable to invoke nbconvert from the active Python environment,
    avoiding PATH ambiguity when the script is run via `uv run`.

    Kernel cwd is set to NOTEBOOKS_DIR so notebook-relative paths (../data/)
    resolve identically whether run here or opened interactively in JupyterLab.

    The Game Data notebook calls both the ASA API and the Open-Meteo archive API
    for every venue; 600 s timeout reflects that worst-case load.

    Args:
        notebook: Notebook filename (no directory prefix).

    Returns:
        Tuple of (notebook, success, message) for consolidated reporting in main.
    """
    path = NOTEBOOKS_DIR / notebook
    if not path.exists():
        return notebook, False, f"notebook not found: {path}"

    # Snapshot parquet mtimes before execution so we can detect stale outputs —
    # i.e. nbconvert exited 0 but the cell that writes the parquet never ran.
    pre_mtime: dict[str, float] = {
        p: (PROJECT_DIR / p).stat().st_mtime if (PROJECT_DIR / p).exists() else 0.0
        for p in NOTEBOOK_OUTPUTS[notebook]
    }

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--inplace",
                "--ExecutePreprocessor.timeout=600",
                str(path),
            ],
            capture_output=True,
            text=True,
            cwd=NOTEBOOKS_DIR,
        )
    except OSError as exc:
        return notebook, False, f"could not launch nbconvert: {exc}"

    if result.returncode != 0:
        lines = result.stderr.strip().splitlines()
        # Show only the last 20 lines — the traceback tail has the actionable error.
        tail = "\n".join(lines[-20:]) if lines else "(no stderr output)"
        return notebook, False, f"nbconvert exit {result.returncode}:\n{tail}"

    # Verify each expected parquet exists and carries a newer mtime than before
    # execution. A stale mtime means the write cell was skipped or raised silently.
    problems: list[str] = []
    for p in NOTEBOOK_OUTPUTS[notebook]:
        full = PROJECT_DIR / p
        if not full.exists():
            problems.append(f"{p} missing")
        elif full.stat().st_mtime <= pre_mtime[p]:
            problems.append(f"{p} not updated")
    if problems:
        return notebook, False, "output check failed — " + ", ".join(problems)

    return notebook, True, ", ".join(NOTEBOOK_OUTPUTS[notebook])


def main() -> None:
    """Run all data notebooks in parallel and report results."""
    logger.info("Starting %d notebooks in parallel ...", len(NOTEBOOK_OUTPUTS))
    failures: list[str] = []

    with ThreadPoolExecutor(max_workers=len(NOTEBOOK_OUTPUTS)) as pool:
        futures = {pool.submit(run_notebook, nb): nb for nb in NOTEBOOK_OUTPUTS}
        for future in as_completed(futures):
            notebook, ok, msg = future.result()
            if ok:
                logger.info("OK  %s -> %s", notebook, msg)
            else:
                logger.error("ERR %s — %s", notebook, msg)
                failures.append(notebook)

    if failures:
        logger.error("%d notebook(s) failed: %s", len(failures), ", ".join(failures))
        sys.exit(1)
    logger.info("All notebooks complete. Parquets updated.")


if __name__ == "__main__":
    main()
