from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.recommendation.feature_builder import (
    CandidateMovie,
    UserRecommendationSignals,
    movie_feature_text,
    user_genre_text,
    user_profile_text,
)
from app.utils.constants import CONTENT_MATCH_THRESHOLD


def _vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        norm="l2",
        token_pattern=r"(?u)\b\w+\b",
    )


def cosine_to_user_vector(document_texts: Sequence[str], user_text: str) -> np.ndarray:
    documents = [text.strip() if text else "" for text in document_texts]
    count = len(documents)
    if count == 0:
        return np.zeros(0, dtype=float)
    if not any(documents) or not (user_text or "").strip():
        return np.zeros(count, dtype=float)

    vectorizer = _vectorizer()
    try:
        matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return np.zeros(count, dtype=float)
    if not getattr(vectorizer, "vocabulary_", None):
        return np.zeros(count, dtype=float)

    user_vector = vectorizer.transform([user_text])
    scores = cosine_similarity(user_vector, matrix).ravel()
    return np.asarray(scores, dtype=float)


def nearest_seed_titles(
    candidate_texts: Sequence[str],
    seed_movies: Sequence[CandidateMovie],
    *,
    min_score: float = CONTENT_MATCH_THRESHOLD,
) -> tuple[str | None, ...]:
    if not candidate_texts:
        return ()
    if not seed_movies:
        return tuple(None for _ in candidate_texts)

    seed_texts = [movie_feature_text(movie) for movie in seed_movies]
    if not any(text.strip() for text in seed_texts):
        return tuple(None for _ in candidate_texts)

    vectorizer = _vectorizer()
    try:
        matrix = vectorizer.fit_transform([*candidate_texts, *seed_texts])
    except ValueError:
        return tuple(None for _ in candidate_texts)

    candidate_count = len(candidate_texts)
    similarities = cosine_similarity(matrix[:candidate_count], matrix[candidate_count:])
    nearest: list[str | None] = []
    for row in similarities:
        index = int(np.argmax(row))
        nearest.append(seed_movies[index].title if float(row[index]) >= min_score else None)
    return tuple(nearest)


@dataclass(frozen=True)
class ContentScores:
    genre_similarity: np.ndarray
    favorite_movie_similarity: np.ndarray
    nearest_favorite: tuple[str | None, ...]


def compute_content_scores(
    frame: pd.DataFrame,
    signals: UserRecommendationSignals,
    catalog: Mapping[int, CandidateMovie],
) -> ContentScores:
    genre_documents = frame["genre_text"].fillna("").astype(str).tolist()
    content_documents = frame["feature_text"].fillna("").astype(str).tolist()
    return ContentScores(
        genre_similarity=cosine_to_user_vector(genre_documents, user_genre_text(signals, catalog)),
        favorite_movie_similarity=cosine_to_user_vector(
            content_documents,
            user_profile_text(signals, catalog),
        ),
        nearest_favorite=nearest_seed_titles(content_documents, signals.favorite_movies),
    )
