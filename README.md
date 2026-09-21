# Kaggriculture Agent

Agent for Kaggle's [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) simulation competition —
a two-player, 30-day (720-turn) farming-economy game where the goal is to finish with the highest bank balance.

## Layout
- `agents/` — agent code (`main.py` is the submission entry point)
- `scripts/` — local match runner and submission helper
- `notebooks/` — analysis of environment rules, prices, and replays

## Setup
```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```
Put your Kaggle API token in `.env` (`KAGGLE_API_TOKEN=...`); it is git-ignored.
