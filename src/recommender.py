import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
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
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

# Columns that must be numbers so scoring can do math on them.
# Everything else (title, artist, genre, mood) stays a string.
NUMERIC_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
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

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    # TODO: Implement scoring logic using your Algorithm Recipe from Phase 2.
    # Expected return format: (score, reasons)
    return []

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    # TODO: Implement scoring and ranking logic
    # Expected return format: (song_dict, score, explanation)
    return []
