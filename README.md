# Movie Recommendation System

Desktop movie discovery app built with Python and PySide6. It searches TMDB, stores watchlists and ratings locally, and builds personalized recommendations.

## Run from source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Set `TMDB_ACCESS_TOKEN` or `TMDB_API_KEY` in `.env`, then:

```powershell
python main.py
```

User data, SQLite, image cache, and logs live in a writable app-data directory:

- Windows: `%LOCALAPPDATA%\MovieRecommendationSystem`
- Override: set `MVRS_DATA_DIR`

Do not keep the database inside a packaged bundle path. Relative `DATABASE_URL` values such as `sqlite:///movie_recommendation.db` resolve to that app-data folder.

## Package for Windows

PyInstaller builds a single-file desktop executable:

```powershell
.\.venv\Scripts\python.exe scripts\generate_assets.py
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm MovieRecommendationSystem.spec
```

Output:

```text
dist\MovieRecommendationSystem.exe
```

The spec includes:

- `app/ui/theme/theme.qss`
- `assets/icons`, `assets/images`, `assets/placeholders`
- Qt platform plugins discovered by PyInstaller
- runtime packages used by the recommendation engine

`.env` is never bundled. After building, either:

1. Copy `.env` next to `MovieRecommendationSystem.exe`, or
2. Copy `.env` into `%LOCALAPPDATA%\MovieRecommendationSystem`

The executable reads those locations on startup.

## Test a packaged build

```powershell
$env:MVRS_DATA_DIR = "$env:TEMP\mvrs-smoke"
$env:TMDB_ACCESS_TOKEN = "<your token>"
.\dist\MovieRecommendationSystem.exe --smoke-test
```

The smoke test checks first-run database creation, register/login, watchlist persistence, recommendation ranking, TMDB search, and poster download. A successful run writes `smoke_ok.txt` in `MVRS_DATA_DIR` and exits `0`.

Launch the GUI normally with:

```powershell
.\dist\MovieRecommendationSystem.exe
```

Persistence is verified by quitting and opening the app again; the same SQLite file in app data is reused.
