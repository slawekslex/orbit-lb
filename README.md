# orbit-wars leaderboard tracker

Tracks the [orbit-wars](https://www.kaggle.com/competitions/orbit-wars/leaderboard) Kaggle
competition leaderboard every 15 minutes via GitHub Actions.

**Live chart: https://slawekslex.github.io/orbit-lb/**

- `top50_history.csv` — timestamped top-50 snapshots
- `latest_top50.csv` — current top 50
- `rank_history.csv` — my rank over time
- `track_rank.py` — fetches the leaderboard (Kaggle API)
- `plot_rank.py` — local matplotlib chart
- `index.html` — the GitHub Pages chart
