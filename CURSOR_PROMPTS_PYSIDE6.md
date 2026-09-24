# Cursor Build Prompts — PySide6 Movie Recommendation System

Use these prompts sequentially.

Before each phase:
- Read `MASTER_PYSIDE6.md`
- Inspect the current codebase
- Preserve working features
- Follow the architecture exactly
- Run relevant tests before finishing

---

# Phase 1 — Project Foundation

```text
Read MASTER_PYSIDE6.md completely before writing code.

Create the initial project foundation for the desktop Movie Recommendation System.

Stack:
- Python 3.12+
- PySide6
- Qt Widgets
- SQLAlchemy 2.x
- SQLite
- Alembic
- TMDB API
- HTTPX
- Pydantic
- scikit-learn
- NumPy
- pandas
- bcrypt
- python-dotenv
- pytest
- pytest-qt
- PyInstaller

Tasks:

1. Create the folder structure defined in MASTER_PYSIDE6.md.
2. Add __init__.py files where appropriate.
3. Create main.py.
4. Create requirements.txt.
5. Create .env.example.
6. Create app/config/settings.py.
7. Create app/utils/logging_config.py.
8. Create app/ui/app_window.py.
9. Create one QApplication and one QMainWindow.
10. Add a minimal QStackedWidget with a temporary welcome page.
11. Ensure the app launches using:
    python main.py
12. Do not implement business features yet.
13. Do not hard-code secrets.

At the end:
- verify imports
- launch the app
- report created files
- fix startup errors
```

---

# Phase 2 — Database Foundation

```text
Read MASTER_PYSIDE6.md first.

Build the database layer using SQLAlchemy 2.x + SQLite.

Create:
- database/base.py
- database/session.py
- database/init_db.py

Create models:
- User
- Movie
- Genre
- MovieGenre
- UserPreference
- Rating
- Watchlist
- WatchHistory
- Interaction

Requirements:
- modern SQLAlchemy 2.x typed mappings
- unique email
- unique tmdb_id
- unique user/movie watchlist pair
- unique user/movie rating pair
- appropriate indexes
- timestamps
- proper foreign keys
- relationships
- onboarding_completed boolean for User

Configure Alembic.

Database must initialize on first run.

Keep all SQLAlchemy logic outside PySide6 UI.

At the end:
- initialize database
- verify tables
- resolve circular imports
- summarize schema
```

---

# Phase 3 — Repositories and Authentication

```text
Read MASTER_PYSIDE6.md.

Implement:
- UserRepository
- AuthService
- auth schemas/validation
- AppState

Registration:
- name
- email
- password
- confirm password

Validation:
- required
- valid email
- minimum 8-character password
- matching passwords
- duplicate email prevention

Security:
- bcrypt hashing
- never store plaintext passwords

Login:
- email/password
- verify credentials
- return User on success
- clear failure errors

AppState should hold current_user and basic navigation state.

Add pytest tests for:
- successful registration
- duplicate email
- invalid email
- short password
- valid login
- invalid login

Do not build UI yet.

Run tests and fix failures.
```

---

# Phase 4 — Theme and Design System

```text
Read MASTER_PYSIDE6.md.

Create the UI theme foundation before building many pages.

Create:
- ui/theme/theme.qss
- ui/theme/colors.py
- ui/theme/fonts.py
- ui/theme/spacing.py

Requirements:
- dark cinematic default theme
- centralized QSS
- primary, secondary, danger, muted states
- reusable typography hierarchy
- consistent spacing
- rounded buttons/cards
- hover/pressed/focus states
- line edit styling
- scrollbar styling
- dialog styling
- sidebar styling

Do not put giant stylesheet strings inside every widget.

Load the QSS globally from the QApplication or MainWindow startup flow.

Create a small visual test page showing:
- buttons
- inputs
- labels
- cards

Make sure the design remains clean, not flashy.
```

---

# Phase 5 — Welcome, Login, Register UI

```text
Read MASTER_PYSIDE6.md.

Create:
- WelcomePage
- LoginPage
- RegisterPage

Use QStackedWidget navigation.

Requirements:

Welcome:
- app title
- short description
- Login
- Register
- Browse as Guest

Login:
- email
- password
- show/hide password
- login button
- register link
- validation/error area

Register:
- name
- email
- password
- confirm password
- register button
- back/login link

Use:
- layouts, not absolute positioning
- centralized theme
- signals/slots
- AuthService

On successful login:
- set AppState.current_user
- navigate to temporary dashboard

On successful registration:
- set current user
- navigate to onboarding placeholder

Do not query database directly from pages.

Add basic pytest-qt tests for critical navigation.
```

---

# Phase 6 — Main Window and Navigation Shell

```text
Read MASTER_PYSIDE6.md.

Build the authenticated main shell.

MainWindow:
- left Sidebar
- TopBar
- central QStackedWidget

Sidebar items:
- Home
- Discover
- Recommendations
- Watchlist
- History
- Insights
- Profile
- Logout

Requirements:
- reusable Sidebar widget
- reusable TopBar widget
- selected nav state
- smooth page switching
- window resize support
- no new QMainWindow per page
- no separate QApplication instances
- clean screen registry/navigation API
- logout confirmation
- logout clears AppState.current_user
- return to WelcomePage

Create placeholder pages for each destination.
```

---

# Phase 7 — Reusable Qt Worker Infrastructure

```text
Read MASTER_PYSIDE6.md.

Create reusable background worker infrastructure.

Use:
- QRunnable
- QThreadPool
- QObject signals

Create a reusable worker capable of:
- executing a callable
- emitting result
- emitting error
- emitting finished
- optionally emitting progress

Requirements:
- no UI updates from worker threads
- UI receives data via signals
- worker exceptions are caught and logged
- easy reuse for API, image, and recommendation jobs

Add a small internal demo/test proving the UI remains responsive during a simulated slow task.

Do not duplicate worker boilerplate across pages.
```

---

# Phase 8 — TMDB Integration

```text
Read MASTER_PYSIDE6.md.

Implement TMDB integration using HTTPX.

Create:
- api/tmdb_client.py
- MovieService
- movie schemas

Configuration from .env:
- TMDB_API_KEY
- TMDB_ACCESS_TOKEN

Implement:
- search_movies(query, page=1)
- get_movie_details(movie_id)
- get_popular_movies(page=1)
- get_trending_movies()
- get_genres()
- get_movie_credits(movie_id)
- get_similar_movies(movie_id)
- discover_movies(filters)

Requirements:
- timeouts
- connection error handling
- API error handling
- meaningful exceptions
- Pydantic/DTO conversion
- logging
- no direct TMDB calls from UI pages

Add mocked tests.

Never commit API credentials.
```

---

# Phase 9 — Local Movie Cache

```text
Read MASTER_PYSIDE6.md.

Implement MovieRepository and local metadata caching.

Cache:
- tmdb_id
- title
- original_title
- overview
- poster_path
- backdrop_path
- release_date
- runtime
- vote_average
- vote_count
- popularity
- original_language
- genres

Requirements:
- upsert movies
- prevent duplicates
- maintain genre relationships
- handle incomplete TMDB data
- update stale local metadata when fresh API data arrives

MovieService should coordinate API data and repository caching.

UI must remain unaware of cache implementation.
```

---

# Phase 10 — Image Loading and Movie Card

```text
Read MASTER_PYSIDE6.md.

Create:
- image client/cache helper
- background image loader
- MovieCard widget
- poster placeholder

MovieCard should show:
- poster
- title
- release year
- rating

Requirements:
- QPixmap/QImage
- preserve aspect ratio
- local image cache if useful
- background download
- placeholder on failure
- click signal
- hover state
- reusable fixed poster ratio
- no frozen UI

Use signals to update a card when an image finishes loading.

Test a grid of many movie cards.
```

---

# Phase 11 — Discover Page

```text
Read MASTER_PYSIDE6.md.

Build DiscoverPage.

Features:
- search
- genre filter
- rating filter
- release year
- language
- sort by popularity
- sort by rating
- sort by release date

Requirements:
- MovieService only
- background worker for network calls
- loading state
- empty state
- error state
- reusable MovieCards
- pagination
- responsive grid / FlowLayout
- QScrollArea
- no absolute positioning
- click card -> MovieDetailsPage

Prevent empty/whitespace-only search.

Keep UI responsive during every request.
```

---

# Phase 12 — Movie Details Page

```text
Read MASTER_PYSIDE6.md.

Build MovieDetailsPage.

Display:
- backdrop where useful
- poster
- title
- year
- runtime
- genres
- TMDB rating
- overview
- language
- cast
- director
- similar movies

Actions:
- add/remove Watchlist
- Mark Watched
- Rate Movie
- Like
- Dislike
- Not Interested

Requirements:
- all persistent actions through services
- background loading
- loading/error states
- back navigation
- similar movie cards open details
- no extra top-level windows for normal navigation
```

---

# Phase 13 — Watchlist, History, Ratings, Interactions

```text
Read MASTER_PYSIDE6.md.

Implement:

Repositories/services:
- Watchlist
- History
- Rating
- Interaction

WatchlistPage:
- show saved movies
- remove
- open details
- mark watched

HistoryPage:
- watched date
- rating if available
- open details

Rating:
- 1–5 stars
- insert/update

Interactions:
- Like
- Dislike
- Not Interested

Rules:
- no duplicate watchlist entries
- one rating per user/movie
- interaction state can update
- persistence in SQLite
- friendly error handling

Add tests.
```

---

# Phase 14 — Rating Widget and Dialogs

```text
Read MASTER_PYSIDE6.md.

Create polished reusable widgets/dialogs:

- RatingWidget
- RatingDialog
- ConfirmDialog
- EditProfileDialog

RatingWidget:
- 5 clickable stars
- hover feedback
- selected state
- emits ratingChanged(int)

Use dialogs only for focused interactions.

Keep styling centralized through QSS.

Do not create large unrelated workflows inside dialogs.
```

---

# Phase 15 — Onboarding

```text
Read MASTER_PYSIDE6.md.

Build OnboardingPage.

Allow:
- favorite genre selection
- favorite movie selection/search
- preferred language
- preferred release period
- preferred minimum rating
- optional interests

Requirements:
- genres from TMDB
- movie search in background
- selected items visually clear
- save via UserService
- store structured preferences
- mark onboarding_completed
- existing users should skip onboarding on future login
- editable later from Profile

Keep onboarding concise and visually clean.
```

---

# Phase 16 — Recommendation Engine

```text
Read MASTER_PYSIDE6.md carefully.

Implement recommendation modules:
- recommendation/engine.py
- recommendation/content_based.py
- recommendation/scoring.py
- recommendation/feature_builder.py

Use:
- pandas
- NumPy
- scikit-learn
- TfidfVectorizer
- cosine_similarity

Signals:
- favorite genres
- favorite movies
- ratings
- likes
- dislikes
- watch history
- not interested

Workflow:
1. build feature strings
2. TF-IDF vectors
3. build user vector
4. cosine similarity
5. weighted preference score
6. negative-signal penalties
7. exclude Not Interested
8. optionally reduce watched movie priority
9. rank
10. return recommendations + explanation metadata

No Qt code inside recommendation modules.

Add deterministic unit tests.
```

---

# Phase 17 — RecommendationService and Recommendations Page

```text
Read MASTER_PYSIDE6.md.

Implement RecommendationService and RecommendationsPage.

Requirements:
- run recommendation generation in background worker
- display Recommended For You
- use MovieCards
- show short explanation reason
- no raw cosine values in production UI
- click -> MovieDetailsPage

Recommendations should respond to:
- ratings
- likes/dislikes
- watch history
- preference edits

Cold start:
- genres
- favorite movies
- language/era
- popular/high-rated fallback

Add refresh functionality.
```

---

# Phase 18 — Dashboard

```text
Read MASTER_PYSIDE6.md.

Build real DashboardPage.

Sections:
- Recommended For You
- Trending
- Popular
- Recently Released
- Continue Exploring

Requirements:
- background workers
- independent failure handling per section
- reuse MovieCard
- horizontal movie rows or compact grids
- View All where useful
- no UI freeze
- clean visual hierarchy

The dashboard should still render if one API section fails.
```

---

# Phase 19 — Profile and Insights

```text
Read MASTER_PYSIDE6.md.

Build ProfilePage and InsightsPage.

Profile:
- name
- email
- edit name
- edit preferences
- optional theme preference

Insights:
- watched count
- watchlist count
- average rating
- favorite genres
- most-watched genre
- highest-rated movies
- recent activity

Requirements:
- service layer only
- no direct SQLAlchemy in UI
- modern card layout
- avoid unnecessary charts
```

---

# Phase 20 — Guest Mode

```text
Read MASTER_PYSIDE6.md.

Implement guest browsing.

Guests can:
- view dashboard-style public content
- search
- filter
- view details

Guests cannot persist:
- watchlist
- history
- ratings
- likes/dislikes
- personalized recommendations

Protected action behavior:
- show sign-in prompt
- allow user to cancel and keep browsing
- no crash

Do not create fake persistent guest accounts.
```

---

# Phase 21 — Threading and Responsiveness Audit

```text
Read MASTER_PYSIDE6.md.

Audit all expensive work:
- HTTP requests
- poster downloads
- recommendation calculations
- large DB operations

Ensure:
- no blocking on Qt main thread
- reusable QThreadPool workers
- all UI updates via signals
- duplicate requests prevented where practical
- loading state shown
- worker errors surfaced cleanly

Test:
- slow internet
- offline mode
- many images
- recommendation generation
- rapid page changes

Fix race conditions and stale-result rendering.
```

---

# Phase 22 — UX Polish

```text
Read MASTER_PYSIDE6.md.

Perform UI/UX polish.

Improve:
- spacing
- typography
- card sizing
- hover states
- focus states
- sidebar
- top bar
- loading indicators
- empty states
- errors
- dialogs
- keyboard navigation
- resize behavior

Add:
- consistent icons
- tooltips where useful
- clear active states

Do not overdecorate.

Keep the dark cinematic design consistent.
```

---

# Phase 23 — Testing

```text
Read MASTER_PYSIDE6.md.

Expand tests.

Use:
- pytest
- pytest-qt

Test:
- auth
- repositories
- watchlist
- history
- ratings
- preferences
- recommendation engine
- TMDB mocked responses
- AppState
- navigation
- critical button signals
- worker result/error handling

Run complete suite.

Fix production code correctly rather than weakening tests.
```

---

# Phase 24 — PyInstaller Packaging

```text
Read MASTER_PYSIDE6.md.

Prepare Windows packaging.

Requirements:
- PyInstaller
- include QSS
- include icons
- include placeholders
- include assets
- correct resource path helper
- writable app data directory
- SQLite outside read-only bundle
- Qt plugins included correctly

Build:
MovieRecommendationSystem.exe

Test:
- first launch
- database initialization
- register/login
- API calls
- image loading
- recommendation engine
- persistence after restart

Create packaging instructions in README.
```

---

# Phase 25 — Final Audit

```text
Read MASTER_PYSIDE6.md one final time.

Audit:

Architecture:
- PySide6 UI has no large business logic
- services handle rules
- repositories handle DB
- TMDB client handles API
- recommendation engine isolated

Qt:
- one QApplication
- one QMainWindow
- QStackedWidget navigation
- signals/slots used properly
- no UI updates from background threads

Security:
- bcrypt
- no plaintext passwords
- no hard-coded API secrets

Features:
- register
- login
- onboarding
- discover
- movie details
- watchlist
- history
- ratings
- interactions
- personalized recommendations
- dashboard
- profile
- insights
- guest mode
- logout

Reliability:
- offline/error states
- no obvious UI freezing
- tests pass
- packaged executable launches

Clean:
- remove dead code
- remove debug prints
- remove unused imports
- resolve blocking TODOs

Create FINAL_PROJECT_STATUS.md with:
- completed features
- architecture
- setup
- running in PyCharm
- tests
- packaging
- known limitations
```

---

# Cursor Architecture Guardrail Prompt

```text
Stop and re-read MASTER_PYSIDE6.md.

Preserve this architecture:

PySide6 UI
    ↓
Services
    ↓
Repositories / Recommendation Engine / TMDB Client
    ↓
SQLite / External API

Qt rules:
- exactly one QApplication
- one main QMainWindow
- QStackedWidget for major page navigation
- use signals/slots
- never block the main thread with network/image/recommendation work
- never update widgets from a worker thread

Do not:
- move SQLAlchemy queries into UI pages
- call TMDB directly from widgets
- hard-code API secrets
- store plaintext passwords
- create new top-level windows for normal page navigation
- add unnecessary dependencies
- rewrite unrelated stable code

Before finishing:
1. inspect changed files
2. run relevant tests
3. launch python main.py
4. fix imports/runtime issues
5. summarize changed files only
```
