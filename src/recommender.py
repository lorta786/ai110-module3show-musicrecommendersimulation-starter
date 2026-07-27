"""Core logic for the Music Recommender Simulation.

Two public surfaces share one scoring engine:
  - a dict-based functional API (load_songs / score_song / recommend_songs) used by src/main.py
  - a dataclass-based OOP API (Song / UserProfile / Recommender) used by tests/test_recommender.py

Both call _score_core(), so there is exactly one copy of the Algorithm Recipe.
"""

import csv
from typing import List, Dict, Tuple, Union
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Algorithm Recipe weights (see README.md).
# Kept as constants so a Phase 4 experiment is a one-line change.
# ---------------------------------------------------------------------------
GENRE_WEIGHT = 2.0     # exact genre match
MOOD_WEIGHT = 1.0      # exact mood match
ENERGY_WEIGHT = 1.5    # scaled by closeness to target_energy
ACOUSTIC_WEIGHT = 0.5  # soft nudge toward/away from acoustic texture
MAX_SCORE = GENRE_WEIGHT + MOOD_WEIGHT + ENERGY_WEIGHT + ACOUSTIC_WEIGHT  # 5.0

# A reason is only worth showing when the rule fired strongly.
ENERGY_REASON_THRESHOLD = 0.9
ACOUSTIC_REASON_THRESHOLD = 0.7


@dataclass
class Song:
    """One track and its attributes, as loaded from data/songs.csv."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """One listener's stated taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def _norm(text: str) -> str:
    """Normalizes a category string so 'Pop ' and 'pop' compare as equal."""
    return str(text).strip().lower()


def _score_core(
    favorite_genre: str,
    favorite_mood: str,
    target_energy: float,
    likes_acoustic: bool,
    genre: str,
    mood: str,
    energy: float,
    acousticness: float,
) -> Tuple[float, List[str]]:
    """Applies the four Algorithm Recipe rules to plain values, returning (score, reasons)."""
    score = 0.0
    reasons: List[str] = []

    # Rule 1 - Genre match: all or nothing, the strongest single signal.
    if _norm(genre) == _norm(favorite_genre):
        score += GENRE_WEIGHT
        reasons.append(f"matches your favorite genre ({_norm(genre)})")

    # Rule 2 - Mood match: a real signal, but softer than genre.
    if _norm(mood) == _norm(favorite_mood):
        score += MOOD_WEIGHT
        reasons.append(f"matches your {_norm(mood)} mood")

    # Rule 3 - Energy similarity: closeness, not magnitude. Both values are on a
    # 0-1 scale, so the absolute difference is already 0-1 and needs no scaling.
    # A song that is too energetic loses exactly as much as one that is too mellow.
    similarity = 1.0 - abs(float(target_energy) - float(energy))
    score += ENERGY_WEIGHT * similarity
    # Round before comparing: 0.8 - 0.70 is 0.10000000000000009 in binary floating
    # point, which would silently fail an exact >= 0.9 check on a true 0.90 match.
    if round(similarity, 6) >= ENERGY_REASON_THRESHOLD:
        reasons.append(
            f"energy ({float(energy):.2f}) is close to your target ({float(target_energy):.2f})"
        )

    # Rule 4 - Acoustic preference: a nudge, not a filter. It always contributes
    # something, so it breaks ties rather than deciding rankings.
    alignment = float(acousticness) if likes_acoustic else 1.0 - float(acousticness)
    score += ACOUSTIC_WEIGHT * alignment
    if round(alignment, 6) >= ACOUSTIC_REASON_THRESHOLD:
        reasons.append(
            "has the acoustic feel you like"
            if likes_acoustic
            else "has the produced, non-acoustic sound you prefer"
        )

    # An explanation should never be empty, even for a weak match.
    if not reasons:
        reasons.append("closest overall match in the catalog")

    return score, reasons


def _profile_fields(user_prefs: Union[Dict, UserProfile]) -> Tuple[str, str, float, bool]:
    """Reads taste fields from either a UserProfile or a plain preferences dict."""
    if isinstance(user_prefs, UserProfile):
        return (
            user_prefs.favorite_genre,
            user_prefs.favorite_mood,
            user_prefs.target_energy,
            user_prefs.likes_acoustic,
        )
    # Dicts accept either the long names or the short aliases used in main.py.
    return (
        user_prefs.get("favorite_genre", user_prefs.get("genre", "")),
        user_prefs.get("favorite_mood", user_prefs.get("mood", "")),
        user_prefs.get("target_energy", user_prefs.get("energy", 0.5)),
        bool(user_prefs.get("likes_acoustic", False)),
    )


# ---------------------------------------------------------------------------
# Functional API (used by src/main.py)
# ---------------------------------------------------------------------------

# Columns that must be numbers so scoring can do math on them.
# Everything else (title, artist, genre, mood) stays a string.
NUMERIC_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")


def load_songs(csv_path: str) -> List[Dict]:
    """Reads the song catalog CSV into a list of dicts with numeric fields converted."""
    songs = []

    # newline="" is what the csv module expects: it lets the CSV parser handle
    # line endings itself instead of Python translating them first.
    with open(csv_path, newline="", encoding="utf-8") as f:
        # DictReader treats the first line as the header, so each row comes back
        # as a dict like {"title": "Sunrise City", "tempo_bpm": "118", ...}.
        for row in csv.DictReader(f):
            # Copy the row so we own the dict and can safely modify it.
            song = dict(row)

            # CSV gives us every value as a string, so convert the ones we need
            # to compare or do arithmetic with. "1" -> 1, "118" -> 118.0
            song["id"] = int(song["id"])
            for field in NUMERIC_FIELDS:
                song[field] = float(song[field])

            songs.append(song)

    return songs


def score_song(user_prefs: Union[Dict, UserProfile], song: Dict) -> Tuple[float, List[str]]:
    """Rates one song against one taste profile, returning (score, reasons)."""
    favorite_genre, favorite_mood, target_energy, likes_acoustic = _profile_fields(user_prefs)
    return _score_core(
        favorite_genre,
        favorite_mood,
        target_energy,
        likes_acoustic,
        song["genre"],
        song["mood"],
        song["energy"],
        song["acousticness"],
    )


def recommend_songs(
    user_prefs: Union[Dict, UserProfile],
    songs: List[Dict],
    k: int = 5,
) -> List[Tuple[Dict, float, str]]:
    """Scores every song, ranks by score descending, and returns the top k."""
    # Step 1: judge each song on its own. score_song() is a pure function and
    # knows nothing about the other songs in the catalog.
    scored = [(song, *score_song(user_prefs, song)) for song in songs]

    # Step 2: compare. sorted() returns a new list and leaves `songs` untouched,
    # which matters because the caller may reuse the catalog for another profile.
    # (.sort() would mutate the list in place and return None.)
    # Python's sort is stable, so ties stay in catalog order.
    scored.sort(key=lambda item: item[1], reverse=True)

    # Step 3: select. Flatten the reasons list into one readable sentence.
    return [(song, score, ", ".join(reasons)) for song, score, reasons in scored[:k]]


# ---------------------------------------------------------------------------
# OOP API (used by tests/test_recommender.py)
# ---------------------------------------------------------------------------

class Recommender:
    """Holds a song catalog and ranks it against a UserProfile."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Rates one Song against one UserProfile, returning (score, reasons)."""
        return _score_core(
            user.favorite_genre,
            user.favorite_mood,
            user.target_energy,
            user.likes_acoustic,
            song.genre,
            song.mood,
            song.energy,
            song.acousticness,
        )

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Returns the top k Songs for this user, highest score first."""
        ranked = sorted(self.songs, key=lambda song: self.score(user, song)[0], reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Returns a one-line, human-readable reason this song was recommended."""
        score, reasons = self.score(user, song)
        return f"Score {score:.2f} - " + ", ".join(reasons)
