# Run Analyser — Private Tools

Personal running dashboard that lives at `alireza12t.github.io/misfit/` (password-protected).

## What's here

| File | Purpose |
|------|---------|
| `analyse_runs.py` | Fetches 90 days of Strava data, runs marathon analysis, patches `index.html` with new data |
| `index.html` | Dashboard template — tabs: Long Run / Marathon / Race History |
| `strava_oauth.py` | One-time local OAuth flow to get a refresh token (copy from Run Analyser dir) |
| `race_data.json` | Last fetched data (gitignored — regenerated each run) |

## How it works

1. **CI (GitHub Actions)** — runs daily at 6 AM ET via `.github/workflows/update-running-dashboard.yml`
   - Uses secrets `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`
   - Runs `analyse_runs.py`, copies output to `../misfit/index.html`, commits + pushes

2. **Local refresh** — run manually anytime:
   ```bash
   cd .run-tools
   python analyse_runs.py
   ```
   Reads credentials from `~/.strava/token.json` (created by `strava_oauth.py`).

## GitHub Secrets required

Add these in **Settings → Secrets → Actions** of this repo:

| Secret | Where to find |
|--------|--------------|
| `STRAVA_CLIENT_ID` | Strava API app page |
| `STRAVA_CLIENT_SECRET` | Strava API app page |
| `STRAVA_REFRESH_TOKEN` | From `~/.strava/token.json` after running `strava_oauth.py` |

## Dashboard URL

`https://alireza12t.github.io/misfit/` — password protected (check project memory).
