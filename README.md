# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

**My version — VibeFinder 1.0** — scores a 20-song catalog against a stated taste profile
using four weighted rules totalling 5.0 points: genre match (+2.0), mood match (+1.0),
energy closeness (up to +1.5), and acoustic preference (up to +0.5). Every song is scored
independently, then the list is sorted and the top 5 returned with a plain-English reason
for each pick.

The design choice I care most about is that **energy is scored by closeness, not magnitude** —
a song that's too intense loses exactly as many points as one that's too sleepy. The
implementation detail I care most about is that scoring and ranking are separate:
`score_song()` is a pure function that never sees the other 19 songs, which is what made the
weight experiment in Phase 4 a one-line change.

The most useful thing I found wasn't in the code. Measuring the *reachable* score at
different energy targets showed a listener who wants quiet music tops out 54% below one who
wants loud music — a bias I introduced myself by adding ten songs, nine of them high-energy.
Full write-up in the [model card](model_card.md).

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

**How the `Recommender` scores a song:** each attribute produces a 0–1 signal based on its type, and each signal is multiplied by its own weight. The weights sum to **5.0**, so a song's total score always lands in a 0.0–5.0 range:

| Attribute type | Fields | Signal (0–1) | Weight |
|---|---|---|---|
| Exact match | `genre` | 1.0 if equal, else 0.0 | 2.0 |
| Exact match | `mood` | 1.0 if equal, else 0.0 | 1.0 |
| Target-distance | `energy` | `1 - \|target − value\|` | 1.5 |
| Boolean preference | `likes_acoustic` | `acousticness` if true, else `1 − acousticness` | 0.5 |

The full point values and the reasoning behind each weight are spelled out in the [Algorithm Recipe](#-algorithm-recipe) below — that section is the spec `src/recommender.py` implements.

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
| 3 | Backyard Fireworks (pop punk, happy, 0.88) | 0.0 | 1.0 | 1.38 | 0.46 | **2.83** |
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
2. ~~**Case and whitespace sensitive.**~~ *Fixed in implementation.* Both sides of
   every category comparison now run through `_norm()` (`.strip().lower()`), so
   `"Pop "` and `"pop"` match. This does nothing for the deeper problem in #1 —
   normalizing case still leaves `pop` and `pop punk` as unrelated strings.
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

Actual terminal output from `python -m src.main` on the default profile:

```
Loaded songs: 20

Profile: Happy Pop
  genre=pop  mood=happy  target_energy=0.8  likes_acoustic=False
------------------------------------------------------------------------
1. Sunrise City - Neon Echo  [score: 4.88]
   Because: matches your favorite genre (pop), matches your happy mood, energy (0.82) is close to your target (0.80), has the produced, non-acoustic sound you prefer
2. Gym Hero - Max Pulse  [score: 3.78]
   Because: matches your favorite genre (pop), has the produced, non-acoustic sound you prefer
3. Backyard Fireworks - Curfew Kids  [score: 2.83]
   Because: matches your happy mood, energy (0.88) is close to your target (0.80), has the produced, non-acoustic sound you prefer
4. Rooftop Lights - Indigo Parade  [score: 2.77]
   Because: matches your happy mood, energy (0.76) is close to your target (0.80)
5. Overworld Theme - Pixel Forge  [score: 2.75]
   Because: matches your happy mood, energy (0.70) is close to your target (0.80), has the produced, non-acoustic sound you prefer
------------------------------------------------------------------------
```

This matches the [worked example](#worked-example) above line for line, which is the check that the code and the spec actually agree.

Two things worth noticing in the reasons:

- **Gym Hero has no energy reason.** Its energy similarity is `1 - |0.80 - 0.93| = 0.87`, just under the 0.90 threshold for emitting a reason — but it still collected `1.5 * 0.87 = 1.31` points. The score and the explanation are deliberately not the same thing: every rule contributes points, only strong rules contribute *sentences*.
- **Rooftop Lights has no acoustic reason.** Its alignment is `1 - 0.35 = 0.65`, under the 0.70 threshold, so the 0.33 points it earned go unexplained.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

### Experiment 1 — Weight shift: genre 2.0 → 1.0, energy 1.5 → 3.0

To reproduce: change `GENRE_WEIGHT` to `1.0` and `ENERGY_WEIGHT` to `3.0` at the top of
`src/recommender.py`, run `python -m src.main --all`, then restore the original values.
Keeping the weights as named constants is what makes this a two-line change rather than a
rewrite.

**Result: more accurate, not just different.** For the Happy Pop profile, Gym Hero fell from
**#2 to #5** and all three genuinely `happy` songs moved up past it. The baseline was ranking
an `intense` gym track second for someone who asked for happy pop, purely because it was
tagged `pop`. Halving genre removed that cliff.

**But the set of songs barely moved.** All 5 songs stayed in Happy Pop's top 5 — only the
order changed. Across all five profiles the set overlap was 4–5 of 5. With 20 songs there
isn't enough material for a weight change to surface anything genuinely new, so I can't tell
whether this generalizes or is an artifact of a tiny catalog.

**And it made the fairness problem worse.** Doubling energy's weight amplifies the loudness
bias below. Better rankings, worse bias — a real trade-off, not a free win.

### Experiment 2 — Reachable-score ceiling by energy target

Not a weight change but a probe: strip out the genre and mood rules, then ask what the best
possible score is for listeners at different energy targets. This is what surfaced the
main bias, and it's the experiment I'd run first next time.

```
target_energy=0.1: best non-categorical score = 1.27
target_energy=0.3: best non-categorical score = 1.51
target_energy=0.5: best non-categorical score = 1.76
target_energy=0.7: best non-categorical score = 1.90
target_energy=0.9: best non-categorical score = 1.96
```

### Behavior across user types

Five profiles tested (`python -m src.main --all`): three realistic, two adversarial. All
three realistic profiles got sensible #1 picks scoring above 4.8. The adversarial ones did
not — a profile with contradictory preferences topped out at 4.08, and one asking for a
genre absent from the catalog topped out at **2.46** while still returning five
confident-looking results. Full outputs and pairwise comparisons in the
[model card](model_card.md#7-evaluation).

---

## Limitations and Risks

- **Biased toward loud music, measurably.** A listener wanting quiet music can reach at best
  1.27 points from energy and acousticness; one wanting loud music reaches 1.96. The rule is
  symmetric and fair — the *catalog* isn't (mean energy 0.662, 14 of 20 songs above 0.5).
  I caused this myself by adding 10 songs, 9 of them high-energy.
- **Two of the four rules measure nearly the same thing.** Energy and acousticness correlate
  at **-0.962**, so the model has 3 real signals, not 4.
- **Genre is all-or-nothing, and the catalog is thin.** 12 genres across 20 songs. `pop punk`
  earns zero credit against `pop` — exactly as much as jazz would.
- **Half the columns do nothing.** `tempo_bpm`, `valence`, and `danceability` are loaded and
  ignored. A 172 BPM pop punk track and a 90 BPM ballad are interchangeable if their energy
  values match.
- **One artist can dominate.** No diversity rule — the Chill Lofi profile returns LoRoom at
  both #2 and #3.
- **It never admits it doesn't know.** An unknown genre produces five confident-looking
  recommendations with no warning; only the low score hints anything is wrong, and real apps
  don't show scores.
- **It doesn't understand music.** No lyrics, no language, no artist history, no release
  year. Each attribute is one fixed number, so a song that's quiet then explodes is just
  "medium."
- **It's not how real recommenders work.** This is purely content-based. Real platforms lean
  mostly on collaborative filtering — comparing users to other users — which VibeFinder
  structurally cannot do.

Deeper analysis in the [model card](model_card.md#6-limitations-and-bias).

---

## Reflection

Read the full write-up here: [**Model Card**](model_card.md)

**On how recommenders turn data into predictions.** The machinery is almost embarrassingly
simple — four `if` statements and a `sort` — and the output still feels like understanding.
What I didn't expect is how much of the behavior is decided by things that aren't the
algorithm. The single biggest lever on my results wasn't any weight; it was which songs I
put in the CSV. The second biggest was the *relative* size of the weights rather than their
values: because genre was worth 2.0 and energy only 1.5, no amount of energy similarity
could ever overturn a genre match, which meant an `intense` gym track outranked three
genuinely happy songs for a listener who asked for happy pop. I'd written that constraint
into the recipe deliberately and still didn't anticipate what it would do.

**On where bias shows up.** I expected bias to look like a mistake in the code. It doesn't.
My energy rule is symmetric by construction — too loud is penalized exactly as much as too
quiet — and I'd have defended it as unbiased. But when I measured what score was actually
*reachable* for different listeners, quiet-music fans topped out 54% below loud-music fans,
because the catalog is skewed loud. Nothing in `recommender.py` is wrong. The unfairness
lives entirely in the data, and it's invisible to anyone reading only the code. Worse, I
introduced it while trying to improve the dataset: I added ten songs chasing genre diversity
and never looked at the energy distribution, so I diversified along the axis I was watching
and concentrated along the one I wasn't. That's the lesson I'll actually keep — you can't
find this class of problem by reading code, only by measuring output, and the person most
likely to miss it is the one who built the thing.



