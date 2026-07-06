"""Track a Kaggle competition leaderboard.

Every run:
  - appends the current top 50 teams and scores to top50_history.csv
  - overwrites latest_top50.csv with the current snapshot
  - if a team name is given (--team or KAGGLE_TEAM env var), appends your
    rank within the full leaderboard to rank_history.csv

Usage:
    python track_rank.py [--team "Your Team Name"] [--competition orbit-wars]

Requires: pip install kaggle, plus credentials — either ~/.kaggle/kaggle.json
or the KAGGLE_USERNAME / KAGGLE_KEY environment variables.
"""

import argparse
import csv
import io
import os
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
TOP50_HISTORY = HERE / "top50_history.csv"
LATEST_TOP50 = HERE / "latest_top50.csv"
RANK_HISTORY = HERE / "rank_history.csv"
TOP_N = 50


def download_leaderboard(competition: str) -> list[dict]:
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    with tempfile.TemporaryDirectory() as tmp:
        api.competition_leaderboard_download(competition, path=tmp)
        archive = next(Path(tmp).glob("*.zip"), None)
        if archive:
            with zipfile.ZipFile(archive) as zf:
                name = zf.namelist()[0]
                raw = zf.read(name).decode("utf-8")
        else:
            csv_file = next(Path(tmp).glob("*.csv"))
            raw = csv_file.read_text(encoding="utf-8")

    return list(csv.DictReader(io.StringIO(raw)))


def append_rows(path: Path, header: list[str], rows: list[list]) -> None:
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(header)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--competition", default="orbit-wars")
    parser.add_argument("--team", default=os.environ.get("KAGGLE_TEAM", ""),
                        help="Your team name exactly as shown on the leaderboard")
    args = parser.parse_args()

    rows = download_leaderboard(args.competition)
    if not rows:
        print("Leaderboard is empty or could not be parsed.", file=sys.stderr)
        return 1

    # The CSV is already ordered by rank; column names vary slightly across
    # kaggle package versions, so look them up case-insensitively.
    cols = {c.lower(): c for c in rows[0]}
    name_col = cols.get("teamname") or cols.get("team name")
    score_col = cols.get("score")

    total = len(rows)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    top = [(i, row[name_col], row[score_col]) for i, row in enumerate(rows[:TOP_N], start=1)]

    append_rows(TOP50_HISTORY, ["timestamp_utc", "rank", "team", "score"],
                [[now, rank, team, score] for rank, team, score in top])

    with LATEST_TOP50.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "team", "score"])
        writer.writerows(top)

    print(f"{now} UTC  |  {total} teams  |  leader: {top[0][1]} ({top[0][2]})")

    if args.team:
        mine = None
        for i, row in enumerate(rows, start=1):
            if row[name_col].strip().lower() == args.team.strip().lower():
                mine = (i, row[score_col])
                break
        if mine is None:
            print(f"Team {args.team!r} not found among {total} teams.", file=sys.stderr)
        else:
            rank, score = mine
            print(f"Your team: rank {rank}/{total}  |  score {score}")
            append_rows(RANK_HISTORY,
                        ["timestamp_utc", "competition", "rank", "total_teams", "score"],
                        [[now, args.competition, rank, total, score]])

    return 0


if __name__ == "__main__":
    sys.exit(main())
