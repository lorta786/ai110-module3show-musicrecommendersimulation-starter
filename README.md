# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

This is a **content-based** recommender: it matches song attributes to a user's stated taste, rather than comparing users to one another.

**What each `Song` uses** (from `data/songs.csv`):
- Categorical: `genre`, `mood`
- Numerical (normalized 0–1): `energy`, `valence`, `danceability`, `acousticness`
- Other: `tempo_bpm`, plus `id`, `title`, `artist`

**What the `UserProfile` stores:**
- `favorite_genre` and `favorite_mood` — target categories to match
- `target_energy` — a *target* value, not a "higher is better" value
- `likes_acoustic` — a boolean preference

**How the `Recommender` scores a song:** each attribute is scored by its type, then combined with weights that sum to 1.0 (keeping the final score in a 0–5 range):

| Attribute type | Fields | How it's scored |
|---|---|---|
| Exact match | `genre`, `mood` | 1.0 if equal, else 0.0 |
| Target-distance | `energy` | `1 - \|target − value\|` |
| Boolean preference | `likes_acoustic` | `acousticness` if true, else `1 − acousticness` |

The key idea is **closeness, not magnitude**: a song that's *too energetic* is penalized just as much as one that's *too mellow*. `score_song()` is a pure function — one song in, one score out.

**How songs are chosen:** scoring and ranking are separate steps. `score_song()` rates each song on its own; `recommend_songs()` then sorts all the scores descending and takes the top `k`:

```python
scored = [(song, *score_song(user, song)) for song in songs]  # score each
scored.sort(key=lambda x: x[1], reverse=True)                  # rank the list
return scored[:k]                                              # select top-k
```

# 🧾 Algorithm Recipe

The exact rules `score_song()` follows to turn one song + one user profile into one number.
This is the spec; `src/recommender.py` implements it.

---

## Inputs

**From the user profile**

| Field | Type | Meaning |
|---|---|---|
| `favorite_genre` | string | the genre to match exactly |
| `favorite_mood` | string | the mood to match exactly |
| `target_energy` | float 0–1 | a *target*, not a "more is better" dial |
| `likes_acoustic` | bool | whether acoustic songs are preferred |

**From the song** — `genre`, `mood`, `energy` (0–1), `acousticness` (0–1).
Unused for now: `tempo_bpm`, `valence`, `danceability`. See [Ideas to test](#ideas-to-test).

---

## The four rules

Every song starts at **0.0 points**. Each rule adds points independently, then the totals are ranked.

### Rule 1 — Genre match: **+2.0**

```
+2.0  if song.genre == user.favorite_genre
 0.0  otherwise
```

Genre is the single strongest signal, so it is worth double a mood match. It is
**all-or-nothing**: there is no partial credit for a related genre.

### Rule 2 — Mood match: **+1.0**

```
+1.0  if song.mood == user.favorite_mood
 0.0  otherwise
```

Mood is a real signal but a softer one — the same person wants "happy" and "moody"
songs on different days, so it should not outweigh genre.

### Rule 3 — Energy similarity: **up to +1.5**

```
similarity = 1 - |user.target_energy - song.energy|     # 0.0 → 1.0
points     = 1.5 * similarity
```

Both values are on a 0–1 scale, so the absolute difference is already 0–1 and no
extra normalizing is needed.

The key idea is **closeness, not magnitude**. A song that is *too energetic* is
penalized exactly as much as one that is *too mellow*: for `target_energy = 0.5`,
a 0.9-energy song and a 0.1-energy song both score `1.5 * 0.6 = 0.90`.

The 1.5 cap is deliberately set *between* the genre weight (2.0) and the mood
weight (1.0). That means energy can never overturn a genre match on its own, but
it can beat a mood match — it is the main tiebreaker inside a genre.

### Rule 4 — Acoustic preference: **up to +0.5**

```
points = 0.5 * song.acousticness          if user.likes_acoustic
         0.5 * (1 - song.acousticness)    otherwise
```

A soft nudge, not a filter. Worth the least because it is a texture preference
rather than a taste category, and it always contributes *something* — it breaks
ties rather than deciding rankings.

---

## Total

```
score = genre_points + mood_points + energy_points + acoustic_points
```

**Range: 0.0 to 5.0.** A perfect 5.0 means an exact genre match, an exact mood
match, energy identical to the target, and acousticness perfectly aligned with
the boolean preference.

Weights at a glance:

| Rule | Max | Share of total |
|---|---|---|
| Genre match | 2.0 | 40% |
| Mood match | 1.0 | 20% |
| Energy similarity | 1.5 | 30% |
| Acoustic preference | 0.5 | 10% |

---

## Ranking

Scoring and selecting are separate steps. `score_song()` is a **pure function** —
one song in, one score out, no knowledge of the other songs. `recommend_songs()`
does the comparing:

1. Score every song in the catalog independently.
2. Sort by score, descending.
3. Return the top `k`.

Ties are left in catalog order (Python's sort is stable). No de-duplication by
artist, and no diversity rule — a single artist can occupy every slot.

---

## Explanations

Each rule that fires contributes one human-readable reason, collected in the same
pass as the score:

| Rule | Reason emitted |
|---|---|
| Genre match | `"matches your favorite genre (pop)"` |
| Mood match | `"matches your happy mood"` |
| Energy ≥ 0.9 similarity | `"energy (0.82) is close to your target (0.80)"` |
| Acoustic ≥ 0.7 aligned | `"has the acoustic feel you like"` |

If no rule fires strongly, fall back to `"closest overall match in the catalog"`
so an explanation is never empty.

---

## Worked example

**Profile:** `genre=pop`, `mood=happy`, `target_energy=0.8`, `likes_acoustic=False`

| # | Song | Genre | Mood | Energy | Acoustic | **Total** |
|---|---|---|---|---|---|---|
| 1 | Sunrise City (pop, happy, 0.82) | 2.0 | 1.0 | 1.47 | 0.41 | **4.88** |
| 2 | Gym Hero (pop, intense, 0.93) | 2.0 | 0.0 | 1.31 | 0.48 | **3.78** |
| 3 | Backyard Fireworks (pop punk, happy, 0.88) | 0.0 | 1.0 | 1.38 | 0.46 | **2.84** |
| 4 | Rooftop Lights (indie pop, happy, 0.76) | 0.0 | 1.0 | 1.44 | 0.33 | **2.77** |
| 5 | Overworld Theme (video game, happy, 0.70) | 0.0 | 1.0 | 1.35 | 0.40 | **2.75** |

What this shows:

- The genre match creates a **hard cliff**. The two pop songs clear 3.7; nothing
  else gets past 2.9. Even a mood mismatch (Gym Hero is `intense`, not `happy`)
  can't drop a pop song below a non-pop one.
- **"pop punk" earns zero genre credit against "pop."** String equality treats it
  as no more related than jazz. This is the biggest known weakness of the recipe.
- Once genre is off the table, ranks 3–5 are separated by **0.09 points** — the
  tail of the list is decided almost entirely by energy rounding.

---

## Known weaknesses

1. **No partial genre credit.** `pop` vs `pop punk` vs `indie pop` are three
   unrelated strings. With 13 genres across 20 songs, most genres have only 1–2
   songs, so the +2.0 bonus applies to a very small slice of the catalog and the
   rest of the ranking is decided without it.
2. **Case and whitespace sensitive.** `"Pop"` will not match `"pop"` unless the
   comparison normalizes both sides.
3. **Energy similarity never reaches 0.** The worst possible mismatch still earns
   `1.5 * 0.0`… but a merely bad one (0.4 apart) still earns 0.90 — more than a
   mood match. Distance is soft where genre is hard.
4. **One artist can dominate.** Pixel Forge or Neon Echo can take multiple slots.
5. **Half the columns are ignored** — `tempo_bpm`, `valence`, `danceability` do
   nothing, so a 168 BPM pop punk track and a 90 BPM ballad are interchangeable
   to the recipe if their energy values happen to match.

---

## Ideas to test

Change one thing at a time and record the effect in the README's *Experiments*
section:

- Drop the genre weight from **2.0 → 0.5** and see how far non-pop songs climb.
- Give **partial genre credit** (e.g. +1.0 when one genre string contains the
  other, so `pop` ↔ `pop punk` scores something).
- Let energy **go negative**: `1.5 * (1 - 2*|diff|)`, so a badly mismatched song
  is punished instead of merely under-rewarded.
- Add **valence** (+0.5) for users who want "upbeat" independent of mood label.
- Add a **one-song-per-artist** cap in the ranking step and see whether the top 5
  gets more interesting.




---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



