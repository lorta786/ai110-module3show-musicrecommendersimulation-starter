"""Command line runner for the Music Recommender Simulation.

Run from the repository root:

    python -m src.main          # default profile only
    python -m src.main --all    # every stress-test profile (Phase 4)
"""

import sys
from pathlib import Path

from src.recommender import load_songs, recommend_songs

# Resolve the CSV relative to this file, so the script works from any directory.
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "songs.csv"

# Default taste profile. Field names match the Algorithm Recipe in README.md.
DEFAULT_PROFILE = {
    "name": "Happy Pop",
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.8,
    "likes_acoustic": False,
}

# Phase 4 stress tests. The first three are ordinary listeners; the last two are
# adversarial profiles built to try to break the scoring logic.
PROFILES = [
    DEFAULT_PROFILE,
    {
        "name": "Chill Lofi",
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.3,
        "likes_acoustic": True,
    },
    {
        "name": "Deep Intense Rock",
        "favorite_genre": "alternative rock",
        "favorite_mood": "intense",
        "target_energy": 0.9,
        "likes_acoustic": False,
    },
    {
        # Adversarial 1: every rule pulls a different direction. "relaxed" music
        # is low energy in this catalog, and acoustic music is low energy too,
        # but this listener asks for 0.95 energy. No song can satisfy all three.
        "name": "ADVERSARIAL - Contradictory (loud + relaxed + acoustic)",
        "favorite_genre": "jazz",
        "favorite_mood": "relaxed",
        "target_energy": 0.95,
        "likes_acoustic": True,
    },
    {
        # Adversarial 2: a genre that does not exist in the catalog, so the
        # strongest rule (+2.0) can never fire for anyone. Tests what the
        # ranking falls back on when 40% of the scale is unreachable.
        "name": "ADVERSARIAL - Ghost genre (k-pop is not in the catalog)",
        "favorite_genre": "k-pop",
        "favorite_mood": "focused",
        "target_energy": 0.5,
        "likes_acoustic": False,
    },
]


def print_recommendations(profile: dict, songs: list, k: int = 5) -> None:
    """Prints the top k recommendations for one profile in a readable block."""
    print(f"\nProfile: {profile['name']}")
    print(
        f"  genre={profile['favorite_genre']}  mood={profile['favorite_mood']}  "
        f"target_energy={profile['target_energy']}  likes_acoustic={profile['likes_acoustic']}"
    )
    print("-" * 72)

    for rank, (song, score, explanation) in enumerate(recommend_songs(profile, songs, k=k), start=1):
        print(f"{rank}. {song['title']} - {song['artist']}  [score: {score:.2f}]")
        print(f"   Because: {explanation}")

    print("-" * 72)


def main() -> None:
    """Loads the catalog and prints recommendations for one or all profiles."""
    songs = load_songs(DATA_PATH)
    print(f"Loaded songs: {len(songs)}")

    profiles = PROFILES if "--all" in sys.argv else [DEFAULT_PROFILE]
    for profile in profiles:
        print_recommendations(profile, songs, k=5)


if __name__ == "__main__":
    main()
