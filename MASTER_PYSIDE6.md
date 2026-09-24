# Movie Recommendation System — Master Build Specification (PySide6)

## 1. Project Overview

Build a modern desktop Movie Recommendation System using Python and PySide6.

The application should help users discover movies based on:
- Favorite genres
- Favorite movies
- Ratings
- Watch history
- Likes / dislikes
- Viewing interests and preferences

The application must run cleanly in:
- Cursor during development
- PyCharm for client/demo use
- Windows desktop after packaging with PyInstaller

The project should use a clean, layered architecture with reusable UI components and a separate recommendation engine.

---

## 2. Recommended Technology Stack

### Desktop UI
- Python 3.12+
- PySide6
- Qt Widgets
- QSS for styling
- Qt Designer (optional)

### Images / Media
- Pillow where useful
- QPixmap / QImage for Qt-native rendering

### Database
- SQLAlchemy 2.x
- SQLite
- Alembic

### External Movie Data
- TMDB API
- HTTPX

### Data Validation
- Pydantic

### Recommendation Engine
- scikit-learn
- NumPy
- pandas

### Security
- bcrypt

### Configuration
- python-dotenv

### Testing
- pytest
- pytest-qt

### Packaging
- PyInstaller

---

## 3. Why PySide6

PySide6 is the official Qt for Python binding.

Benefits for this project:
- Modern desktop UI
- Better layout and widget system than Tkinter
- Strong support for cards, dialogs, stacked pages, scroll areas, tables, and custom widgets
- QThread / QRunnable support for background work
- QSS-based theming
- Strong model/view architecture
- Easier to build polished movie grids and dashboard layouts
- LGPL licensing is generally friendlier than PyQt6 for many deployment scenarios

Use Qt Widgets for the first version instead of QML unless a later requirement specifically demands QML.

---

## 4. Why SQLite

Use SQLite as the default database because this is a desktop application.

Advantages:
- No server installation
- Easy to run in PyCharm
- Easy to package
- Suitable for a single-machine app
- Works well with SQLAlchemy
- Can later migrate to PostgreSQL if centralized multi-device data is required

Use PostgreSQL only if future requirements include:
- Multiple PCs sharing the same accounts
- Centralized data
- Network-based synchronization
- Concurrent multi-user access

---

## 5. High-Level Architecture

```text
PySide6 UI
    |
    v
Application Services
    |
    +-------------------------+
    |                         |
    v                         v
Repositories              TMDB Client
    |                         |
    v                         v
SQLAlchemy                 TMDB API
    |
    v
SQLite

RecommendationService
    |
    v
Recommendation Engine
    |
    v
scikit-learn / NumPy / pandas
```

The UI must not contain database queries, recommendation calculations, or direct API logic.

---

## 6. Recommended Project Structure

```text
movie-recommendation-system/
│
├── main.py
├── requirements.txt
├── .env
├── .env.example
├── README.md
│
├── app/
│   ├── __init__.py
│   │
│   ├── ui/
│   │   ├── app_window.py
│   │   │
│   │   ├── pages/
│   │   │   ├── welcome_page.py
│   │   │   ├── login_page.py
│   │   │   ├── register_page.py
│   │   │   ├── onboarding_page.py
│   │   │   ├── dashboard_page.py
│   │   │   ├── discover_page.py
│   │   │   ├── recommendations_page.py
│   │   │   ├── movie_details_page.py
│   │   │   ├── watchlist_page.py
│   │   │   ├── history_page.py
│   │   │   ├── insights_page.py
│   │   │   └── profile_page.py
│   │   │
│   │   ├── widgets/
│   │   │   ├── sidebar.py
│   │   │   ├── topbar.py
│   │   │   ├── movie_card.py
│   │   │   ├── rating_widget.py
│   │   │   ├── search_bar.py
│   │   │   ├── filter_panel.py
│   │   │   ├── loading_widget.py
│   │   │   ├── empty_state.py
│   │   │   ├── toast.py
│   │   │   └── flow_layout.py
│   │   │
│   │   ├── dialogs/
│   │   │   ├── confirm_dialog.py
│   │   │   ├── rating_dialog.py
│   │   │   └── edit_profile_dialog.py
│   │   │
│   │   ├── workers/
│   │   │   ├── api_worker.py
│   │   │   ├── image_worker.py
│   │   │   └── recommendation_worker.py
│   │   │
│   │   └── theme/
│   │       ├── theme.qss
│   │       ├── colors.py
│   │       ├── fonts.py
│   │       └── spacing.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── movie_service.py
│   │   ├── recommendation_service.py
│   │   ├── watchlist_service.py
│   │   ├── history_service.py
│   │   ├── rating_service.py
│   │   └── user_service.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── movie_repository.py
│   │   ├── watchlist_repository.py
│   │   ├── history_repository.py
│   │   ├── rating_repository.py
│   │   └── preference_repository.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── movie.py
│   │   ├── genre.py
│   │   ├── rating.py
│   │   ├── watchlist.py
│   │   ├── watch_history.py
│   │   └── user_preference.py
│   │
│   ├── recommendation/
│   │   ├── engine.py
│   │   ├── content_based.py
│   │   ├── scoring.py
│   │   └── feature_builder.py
│   │
│   ├── api/
│   │   ├── tmdb_client.py
│   │   └── image_client.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── init_db.py
│   │
│   ├── schemas/
│   │   ├── auth_schema.py
│   │   ├── user_schema.py
│   │   └── movie_schema.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── state/
│   │   └── app_state.py
│   │
│   └── utils/
│       ├── validators.py
│       ├── constants.py
│       ├── helpers.py
│       ├── paths.py
│       └── logging_config.py
│
├── assets/
│   ├── icons/
│   ├── images/
│   ├── placeholders/
│   └── fonts/
│
├── migrations/
│
├── tests/
│   ├── test_auth.py
│   ├── test_movies.py
│   ├── test_recommendations.py
│   ├── test_watchlist.py
│   └── test_ui.py
│
└── build/
```

---

## 7. Main Qt Application Architecture

Use exactly one `QApplication`.

Use one main `QMainWindow`.

Inside the main window, use a `QStackedWidget` for page navigation.

Recommended structure:

```text
QApplication
    ↓
MainWindow (QMainWindow)
    ↓
Central Container
    ├── Sidebar
    └── QStackedWidget
          ├── WelcomePage
          ├── LoginPage
          ├── RegisterPage
          ├── OnboardingPage
          ├── DashboardPage
          ├── DiscoverPage
          ├── RecommendationsPage
          ├── MovieDetailsPage
          ├── WatchlistPage
          ├── HistoryPage
          ├── InsightsPage
          └── ProfilePage
```

Use Qt signals and slots for communication between UI components.

Do not tightly couple pages to each other.

---

## 8. UI Design Direction

The application should feel modern, clean, cinematic, and desktop-native.

Recommended:
- Dark theme by default
- Charcoal / near-black background
- White primary text
- Muted gray secondary text
- One accent color
- Rounded cards
- Poster-driven layouts
- Soft shadows only when appropriate
- Generous spacing
- Clear typography hierarchy
- Minimal borders
- Sidebar navigation
- Scrollable content areas

Avoid:
- Default-looking Qt widgets
- Excessive gradients
- Too many colors
- Crowded tables
- Giant modal workflows
- Hardcoded absolute positioning

Use layouts:
- `QVBoxLayout`
- `QHBoxLayout`
- `QGridLayout`
- custom flow layout where useful

Avoid fixed coordinates.

---

## 9. QSS Styling Rules

Use centralized QSS.

Example organization:

```text
theme.qss
colors.py
fonts.py
spacing.py
```

Do not scatter giant `setStyleSheet()` strings throughout widgets.

Use object names / properties for specific component variants.

Example:
```python
button.setProperty("variant", "primary")
```

QSS:
```css
QPushButton[variant="primary"] {
    border-radius: 8px;
    padding: 10px 16px;
}
```

---

## 10. Core User Flow

```text
Start
  ↓
Welcome
  ↓
Login / Register / Guest Browse
  ↓
Authentication
  ↓
First-Time Preference Onboarding
  ↓
Dashboard
  ↓
Discover / Recommendations / Watchlist / History / Insights / Profile
```

---

## 11. Registration Flow

Fields:
- Name
- Email
- Password
- Confirm Password

Validation:
- Required fields
- Valid email
- Password minimum 8 characters
- Matching passwords
- Unique email

Process:
1. Validate with Pydantic/service logic
2. Hash with bcrypt
3. Save user
4. Set active user
5. Open onboarding

Never store plaintext passwords.

---

## 12. Login Flow

1. Enter email/password
2. Find user
3. Verify password with bcrypt
4. If successful:
   - set `AppState.current_user`
   - navigate to dashboard
5. If unsuccessful:
   - show inline error / friendly dialog

---

## 13. Application State

Create a centralized lightweight state object.

Example:
```python
class AppState:
    current_user = None
    selected_movie = None
    previous_page = None
    active_filters = {}
```

Prefer explicit state management over random module globals.

---

## 14. Preference Onboarding

After registration, allow selection of:
- Favorite genres
- Favorite movies
- Preferred language
- Preferred release period
- Minimum preferred rating
- Optional viewing interests

Do not make every preference required.

Support editing later from Profile.

---

## 15. Dashboard

Dashboard sections:
- Recommended For You
- Trending
- Popular
- Recently Released
- Continue Exploring

Top area:
- Greeting
- Search shortcut
- Profile button

Sidebar:
- Home
- Discover
- Recommendations
- Watchlist
- History
- Insights
- Profile
- Logout

Use horizontal scroll areas or compact grids for movie groups.

---

## 16. Discover

Support:
- Search by title
- Keyword search
- Genre filter
- Rating filter
- Release year
- Language
- Sort by popularity
- Sort by rating
- Sort by release date

Movie cards should show:
- Poster
- Title
- Year
- Rating

Clicking a card opens Movie Details.

---

## 17. Movie Details

Display:
- Large poster
- Backdrop if desired
- Title
- Year
- Runtime
- Genres
- TMDB rating
- Overview
- Language
- Cast
- Director
- Similar movies

Actions:
- Add/remove Watchlist
- Mark Watched
- Rate
- Like
- Dislike
- Not Interested

---

## 18. Watchlist

Users can:
- Add movies
- Remove movies
- Open details
- Mark watched

Prevent duplicates.

---

## 19. Watch History

Track:
- Movie
- Date watched
- User rating
- Like/dislike state

Allow reopening Movie Details.

---

## 20. Ratings / Interactions

Rating:
- 1 to 5 stars

Interactions:
- Like
- Dislike
- Not Interested

These signals should affect recommendations.

---

## 21. Recommendation Engine

Use content-based filtering first.

Inputs:
- Favorite genres
- Favorite movies
- Ratings
- Likes
- Dislikes
- Watch history
- Not interested

Pipeline:

```text
User Preferences
      +
Ratings / Likes / History
      ↓
Build User Profile
      ↓
Fetch Candidate Movies
      ↓
Feature Engineering
      ↓
TF-IDF / Similarity
      ↓
Weighted Scoring
      ↓
Exclude / Penalize Negative Signals
      ↓
Rank
      ↓
Recommendations
```

Recommended tools:
- `TfidfVectorizer`
- `cosine_similarity`
- NumPy
- pandas

---

## 22. Recommendation Scoring

Starting idea:

```text
score =
    genre_similarity * 0.35
  + favorite_movie_similarity * 0.25
  + tmdb_rating_score * 0.15
  + popularity_score * 0.10
  + release_preference_score * 0.05
  + interaction_score * 0.10
```

Then apply:
- dislike penalty
- not-interested exclusion
- optional watched-movie penalty

Weights should live in configuration/constants, not scattered throughout code.

---

## 23. Cold Start Strategy

For new users with little data:
1. Use onboarding genres
2. Use favorite movies
3. Use language / era preferences
4. Blend with highly rated/popular movies
5. Gradually shift toward behavioral signals as the user interacts

---

## 24. TMDB Integration

Use TMDB for:
- Search
- Popular movies
- Trending
- Movie details
- Posters
- Backdrops
- Genres
- Credits
- Similar movies
- Discover

Use `.env`:

```env
TMDB_API_KEY=your_key_here
TMDB_ACCESS_TOKEN=your_token_here
DATABASE_URL=sqlite:///movie_recommendation.db
```

Never hard-code credentials.

---

## 25. TMDB Client

`tmdb_client.py` should expose methods such as:

```python
search_movies(query, page=1)
get_movie_details(movie_id)
get_popular_movies(page=1)
get_trending_movies()
get_genres()
get_movie_credits(movie_id)
get_similar_movies(movie_id)
discover_movies(filters)
```

The UI must call `MovieService`, not `TMDBClient` directly.

---

## 26. Local Movie Cache

Cache useful metadata locally:
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

Benefits:
- Faster repeated views
- Fewer API calls
- Better recommendation processing

---

## 27. Database Models

### users
```text
id
name
email
password_hash
onboarding_completed
created_at
updated_at
```

### movies
```text
id
tmdb_id
title
original_title
overview
poster_path
backdrop_path
release_date
runtime
vote_average
vote_count
popularity
original_language
created_at
updated_at
```

### genres
```text
id
tmdb_genre_id
name
```

### movie_genres
```text
movie_id
genre_id
```

### user_preferences
```text
id
user_id
preference_type
preference_value
weight
```

### ratings
```text
id
user_id
movie_id
rating
created_at
updated_at
```

### watchlist
```text
id
user_id
movie_id
created_at
```

### watch_history
```text
id
user_id
movie_id
watched_at
```

### interactions
```text
id
user_id
movie_id
interaction_type
created_at
updated_at
```

---

## 28. Service Layer

### AuthService
- register
- login
- password verification

### MovieService
- search
- details
- discover
- local caching

### RecommendationService
- build user profile
- generate recommendations
- explain recommendation reason

### WatchlistService
- add
- remove
- list

### HistoryService
- mark watched
- history list

### RatingService
- create/update rating
- get ratings

### UserService
- profile
- preferences
- insights

---

## 29. Repository Layer

Repositories handle persistence only.

Example:

```text
WatchlistPage
    ↓
WatchlistService
    ↓
WatchlistRepository
    ↓
SQLAlchemy
    ↓
SQLite
```

Do not call SQLAlchemy directly from pages/widgets.

---

## 30. Background Work and Threads

Never block the Qt UI thread with:
- HTTP requests
- image downloads
- recommendation calculations
- heavy database operations

Preferred options:
- `QThread`
- `QRunnable`
- `QThreadPool`

Use signals to send results back to the main thread.

Example:

```text
Search Button
    ↓
Worker starts
    ↓
HTTP request
    ↓
Worker emits result signal
    ↓
Main UI thread renders results
```

Never directly update Qt widgets from a worker thread.

---

## 31. Worker Pattern

Workers should emit signals such as:
- `finished`
- `result`
- `error`
- `progress`

Do not create one-off threading logic in every page.

Create reusable worker abstractions.

---

## 32. Image Handling

Use:
- `QPixmap`
- `QImage`
- HTTPX for downloading
- optional Pillow for preprocessing

Requirements:
- placeholder images
- aspect-ratio-preserving scaling
- local cache where practical
- async/background loading
- no UI freeze

---

## 33. Flow Layout / Movie Grid

For poster cards, consider:
- `QGridLayout` for fixed responsive columns
- custom `FlowLayout` for more flexible wrapping
- `QScrollArea` around card collections

Do not use tables for movie discovery unless specifically required.

---

## 34. Error Handling

Handle:
- No internet
- TMDB timeout
- Bad API key
- Empty search
- API unavailable
- Missing movie
- Missing poster
- Database failure
- Invalid user input

Show user-friendly UI messages.

Log technical details separately.

---

## 35. Insights Page

Display:
- Total watched
- Watchlist count
- Average user rating
- Favorite genres
- Most-watched genre
- Highest-rated movies
- Recent activity

Charts are optional, not required for MVP.

---

## 36. Guest Mode

Guests can:
- Browse
- Search
- View movie details

Guests cannot persist:
- Watchlist
- Ratings
- History
- Likes/dislikes
- Personalized recommendations

If a guest tries a protected action, show a sign-in prompt.

---

## 37. Logging

Use Python logging.

Log:
- startup
- database initialization
- API failures
- worker errors
- recommendation exceptions
- unexpected exceptions

Never log:
- passwords
- access tokens
- API secrets

---

## 38. Testing

Use:
- pytest
- pytest-qt

Priority tests:

### Auth
- registration
- duplicate email
- password verification

### Repositories
- create/read/update
- duplicate prevention

### Watchlist
- add/remove
- duplicate handling

### Ratings
- create/update
- invalid range

### Recommendations
- genre relevance
- dislike penalty
- not-interested exclusion
- cold start

### TMDB
- mocked responses
- timeout
- error responses

### UI
- page navigation
- critical button actions
- signal handling where practical

---

## 39. Packaging

Use PyInstaller.

Target:
```text
dist/
└── MovieRecommendationSystem.exe
```

Include:
- QSS
- icons
- placeholders
- image assets
- Qt platform plugins automatically discovered by PyInstaller
- required runtime files

SQLite should live in a writable app-data directory, not inside a read-only bundle path.

---

## 40. Cursor Development Rules

Cursor must:

1. Read this file before major changes.
2. Preserve layered architecture.
3. Keep pages/widgets focused on UI.
4. Keep business logic in services.
5. Keep persistence in repositories.
6. Keep API calls in TMDB client/service.
7. Keep recommendation logic isolated.
8. Use Qt signals/slots.
9. Avoid blocking the UI thread.
10. Avoid hard-coded secrets.
11. Use type hints.
12. Keep functions/classes focused.
13. Reuse components.
14. Avoid unnecessary dependencies.
15. Avoid unrelated rewrites.
16. Run affected tests after each phase.
17. Ensure `python main.py` still launches.

---

## 41. Code Style

Follow:
- PEP 8
- Type hints
- Clear class names
- Small methods
- Single responsibility
- Explicit dependencies

Good:
```python
class MovieService:
    def search_movies(self, query: str, page: int = 1) -> list[MovieDTO]:
        ...
```

Avoid:
```python
def doStuff(x):
    ...
```

---

## 42. Development Phases

1. Project foundation
2. Database
3. Auth services
4. Auth UI
5. Main window/navigation
6. Theme/design system
7. TMDB
8. Local cache
9. Image workers/movie cards
10. Discover
11. Movie details
12. Watchlist/history/ratings
13. Onboarding
14. Recommendation engine
15. Recommendations UI
16. Dashboard
17. Profile/insights
18. Guest mode
19. Threading audit
20. UX polish
21. Testing
22. Packaging
23. Final audit

---

## 43. Definition of Done

The system is complete when:

- Runs in PyCharm
- Starts with `python main.py`
- Uses one QApplication
- Uses one main QMainWindow
- Uses QStackedWidget for major pages
- Registration works
- Login works
- Passwords are hashed
- Onboarding works
- Search works
- TMDB data works
- Posters load without freezing
- Movie details work
- Watchlist persists
- History persists
- Ratings persist
- Like/dislike works
- Personalized recommendations work
- Recommendations react to user behavior
- Profile works
- Insights work
- Guest mode works
- Errors do not crash the app
- Tests pass
- PyInstaller build works

---

## 44. Final Architecture Principle

Always preserve this separation:

```text
PySide6 UI
    ↓
Services
    ↓
Repositories / Recommendation Engine / TMDB Client
    ↓
SQLite / External API
```

The UI should remain easy to:
- understand
- test
- replace
- extend
- demonstrate
- package
