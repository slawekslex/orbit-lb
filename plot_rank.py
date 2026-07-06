"""Plot rank over time from the tracker's CSV history.

Usage:
    python plot_rank.py                          # your team + current top 5
    python plot_rank.py --teams "Team A" "Team B"  # your team + named competitors
    python plot_rank.py --metric score           # plot scores instead of ranks

Reads top50_history.csv (all top-50 teams) and rank_history.csv (your team,
even when outside the top 50). Saves rank_plot.png and opens a window.

Tip: run `git pull` first so the CSVs include the latest data collected
by the GitHub Action.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
MY_TEAM = "Slawek Biel"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teams", nargs="*", default=None,
                        help="Competitor team names (default: current top 5)")
    parser.add_argument("--metric", choices=["rank", "score"], default="rank")
    parser.add_argument("--out", default=str(HERE / "rank_plot.png"))
    args = parser.parse_args()

    top50 = pd.read_csv(HERE / "top50_history.csv", parse_dates=["timestamp_utc"])
    top50["score"] = pd.to_numeric(top50["score"], errors="coerce")

    if args.teams:
        competitors = args.teams
    else:
        latest_ts = top50["timestamp_utc"].max()
        latest = top50[top50["timestamp_utc"] == latest_ts].sort_values("rank")
        competitors = [t for t in latest["team"].head(5) if t != MY_TEAM]

    fig, ax = plt.subplots(figsize=(11, 6))

    for team in competitors:
        series = top50[top50["team"] == team].sort_values("timestamp_utc")
        if series.empty:
            print(f"warning: no data for {team!r} (never in top 50 so far)")
            continue
        ax.plot(series["timestamp_utc"], series[args.metric],
                marker="o", markersize=3, linewidth=1.2, alpha=0.7, label=team)

    # Own team: prefer rank_history.csv, which covers ranks beyond the top 50.
    mine = None
    rank_file = HERE / "rank_history.csv"
    if rank_file.exists():
        mine = pd.read_csv(rank_file, parse_dates=["timestamp_utc"])
        mine["score"] = pd.to_numeric(mine["score"], errors="coerce")
    if mine is None or mine.empty:
        mine = top50[top50["team"] == MY_TEAM]
    mine = mine.sort_values("timestamp_utc")
    if not mine.empty:
        ax.plot(mine["timestamp_utc"], mine[args.metric],
                marker="o", markersize=4, linewidth=2.5, color="crimson", label=f"{MY_TEAM} (me)")

    if args.metric == "rank":
        ax.invert_yaxis()  # rank 1 at the top
        ax.set_ylabel("Rank")
    else:
        ax.set_ylabel("Score")
    ax.set_xlabel("Time (UTC)")
    ax.set_title("Kaggle orbit-wars leaderboard over time")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(args.out, dpi=150)
    print(f"saved {args.out}")
    plt.show()


if __name__ == "__main__":
    main()
