# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

A content-based music recommender that scores songs against a stated taste profile.

---

## 2. Intended Use

### What it does

VibeFinder takes one listener's stated preferences — a favorite genre, a favorite mood, a
target energy level, and whether they like acoustic music — and ranks a catalog of 20 songs
from best match to worst. It returns the top 5 along with a plain-English reason for each
pick, like "matches your favorite genre (pop), energy (0.82) is close to your target (0.80)."

### Who it's for

**This is a classroom exercise, not a product.** It exists to make the machinery of a
recommender visible: how attributes become numbers, how numbers become a ranking, and where
bias sneaks in. It is meant to be read and argued with, not deployed.

### What it assumes about the user

Three assumptions, and all three are worth being suspicious of:

1. **The user can describe their own taste accurately.** VibeFinder never watches behavior.
   It only knows what someone typed into a profile. Real platforms mostly ignore stated
   preferences because people are bad at self-reporting — they say they like jazz and then
   stream pop all week.
2. **Taste is a single fixed point.** One favorite genre, one favorite mood, one energy
   target. No sense of mood changing by time of day, or of liking two unrelated things.
3. **The four chosen attributes capture "vibe."** They don't. See section 6.

### Non-intended use

- **Not for real listeners.** A 20-song catalog isn't a music service.
- **Not a benchmark or a baseline.** The scores are not calibrated against anything, and a
  4.88 doesn't mean 98% correct — it means "collected most of the available points."
- **Not for deciding what any group of people should hear.** Section 6 documents a
  measurable bias toward loud music. Any system used to allocate attention or exposure
  needs a fairness audit VibeFinder has not had.
- **Not a model of how Spotify actually works.** Real recommenders lean mostly on
  *collaborative* filtering — comparing users to other users. VibeFinder is purely
  content-based and never compares one listener to another, so it structurally cannot
  produce the "people like you also liked" effect that drives most real recommendations.

---

## 3. How the Model Works

Imagine a judge with a scorecard worth 5 points total, listening to each song one at a time.

The judge cares about four things, and they are deliberately not worth the same amount:

- **Is it the right genre?** Worth **2 points** — the biggest single item on the card. It's
  all or nothing: exactly right, or nothing at all.
- **Is it the right mood?** Worth **1 point**, also all or nothing. Mood matters, but the
  same person wants happy songs and moody songs on different days, so it shouldn't be able
  to outweigh genre.
- **Is the energy right?** Worth up to **1.5 points**, and this one is graded on a sliding
  scale. The key idea is **closeness, not loudness**. If you asked for medium-energy music,
  a song that's too intense loses exactly as many points as one that's too sleepy. This is
  the part people usually get wrong when they first design a scoring rule — it's tempting to
  treat "more energy" as "better," and that would be a completely different system.
- **Does the acoustic texture match?** Worth up to **0.5 points** — a nudge, not a rule. It
  always contributes something, so in practice it breaks ties rather than deciding winners.

Add the four up and every song has a number between 0 and 5. Then — and this is a genuinely
separate step — sort all 20 numbers and hand back the top 5. The judging never involves
comparing songs to each other; a song's score is the same whether it's the only song in the
catalog or one of a million. Comparison happens once, at the end, when the list is sorted.

Alongside the score, the judge writes down *why*. A rule only earns a written reason if it
fired strongly, which is why some recommendations show three reasons and some show one.

### What changed from the starter code

The starter shipped the data structures and a working CSV loader; the scoring and ranking
were empty stubs. Beyond filling those in:

- **One scoring engine, two interfaces.** The project needs a dictionary-based API (for the
  command line) and a dataclass-based one (for the tests). Rather than write the recipe
  twice and let the two copies drift apart, both call a single internal function.
- **Weights are named constants**, not numbers buried in the logic, which is what made the
  Phase 4 experiment a one-line change instead of a rewrite.
- **Genre and mood comparisons are normalized** for case and whitespace, so "Pop " matches
  "pop."
- **Rounding before threshold comparisons.** A real bug: one song's energy similarity was
  exactly 0.90, but because `0.8 - 0.70` evaluates to `0.10000000000000009` in binary
  floating point, the "is this close enough to mention?" check silently failed. The song
  still got its points — it just lost its explanation, which is the kind of bug that never
  crashes and never gets noticed.

---

## 4. Data

### Size and shape

**20 songs, 10 columns.** The starter file had 10 songs; I added 10 more (ids 11–20).

Each song carries: `id`, `title`, `artist`, `genre`, `mood`, `energy`, `tempo_bpm`,
`valence`, `danceability`, `acousticness`. The four 0–1 numerical columns were already in
the starter data. **Only `energy` and `acousticness` are actually scored** — `tempo_bpm`,
`valence`, and `danceability` are loaded, converted to numbers, and then ignored.

### Coverage

**12 genres across 20 songs**, which is the central problem with this dataset: lofi has 3
songs, six genres have 2, and five genres have exactly 1. The genre rule is worth 40% of the
total score but can only ever fire for 1–3 songs per user.

**6 moods**, distributed unevenly: happy (5), intense (5), chill (3), relaxed (3), moody (3),
focused (1). A user whose favorite mood is `focused` is competing over a single song.

### What I added, and how it backfired

I added 10 songs across 5 new genres — alternative rock, city pop, pop punk, r&b, and video
game music. Two things I only noticed when I measured the result:

| | mean energy | songs ≥ 0.5 energy | new moods |
|---|---|---|---|
| Starter 10 | 0.599 | 5 / 10 | — |
| **My 10** | **0.725** | **9 / 10** | **none** |
| All 20 | 0.662 | 14 / 20 | |

**I made the loudness skew worse.** Nine of my ten additions are high-energy, which pushed
the catalog mean from 0.599 to 0.662 and directly deepened the bias documented in section 6.
I was aiming for genre diversity and never checked the numerical distribution, so I
diversified along the axis I was looking at and concentrated along the one I wasn't.

**I added zero new moods.** All ten of my songs reuse moods that already existed, so `mood`
is no more expressive than it was in the starter file.

### What's missing from the dataset

No release year, no popularity, no language, no lyrics, no instrumentation, no artist
history. Whole regions of taste are absent — nothing classical, no hip-hop, no country, no
electronic dance music, nothing non-English. And every attribute is a single fixed number
per song, so there's no notion of a song that's quiet for two minutes and then explodes.

---

## 5. Strengths

### It works well for mainstream, internally consistent listeners

The three realistic profiles all got sensible top picks with scores above 4.8:

| Profile | Top pick | Score |
|---|---|---|
| Happy Pop | Sunrise City (pop, happy, 0.82) | 4.88 |
| Chill Lofi | Library Rain (lofi, chill, 0.35) | 4.85 |
| Deep Intense Rock | Broken Antenna (alt rock, intense, 0.83) | 4.81 |

In each case the #1 result is exactly the song I'd have picked by hand. When a listener's
stated preferences don't fight each other and the catalog actually contains their genre,
VibeFinder finds the right song.

### The closeness rule behaves correctly

This is the part I'm most confident in, because it's the part that's easiest to get wrong.
Chill Lofi (target 0.30) returns songs at 0.28–0.42 energy — including one *below* the
target — rather than marching toward the quietest song in the catalog. The rule is genuinely
measuring distance, not sorting by volume.

### Scoring and ranking are cleanly separated

`score_song()` is a pure function: one song in, one number out, no knowledge of the other 19.
All comparison happens in `recommend_songs()`. This sounds like a style preference but it's
what made the Phase 4 experiment possible — because the weights are named constants read at
scoring time, I could change them and re-rank without touching the ranking logic at all.

### The explanations are honest about partial matches

The system never claims more than it earned. Gym Hero ranks #2 for Happy Pop but its reason
line says only "matches your favorite genre (pop), has the produced, non-acoustic sound you
prefer" — it does **not** claim a mood match it didn't have. A reader can see from the reason
line alone that this recommendation is weaker than it looks, which is exactly what surfaced
the over-weighted-genre problem in section 6.

---

## 6. Limitations and Bias

### The main finding: the system is quietly biased toward loud music

The scoring rules treat every listener equally, but the **catalog does not**. The 20 songs
average 0.662 energy and 14 of the 20 sit at or above 0.5, so a listener who wants quiet
music simply has fewer songs to be close to. To measure this I stripped out the genre and
mood rules and asked what the *best possible* score is for listeners at different energy
targets. Someone who wants loud music (target 0.9) can reach **1.96**; someone who wants
quiet music (target 0.1) tops out at **1.27** — a 54% advantage for the loud listener that
has nothing to do with their taste and everything to do with what was put in the CSV.

```
target_energy=0.1: best non-categorical score = 1.27
target_energy=0.3: best non-categorical score = 1.51
target_energy=0.5: best non-categorical score = 1.76
target_energy=0.7: best non-categorical score = 1.90
target_energy=0.9: best non-categorical score = 1.96
```

This is the dangerous kind of bias, because nothing in the code looks wrong. The energy
rule is symmetric and fair on paper. The unfairness lives entirely in the data, and it
would be invisible to anyone reading only `recommender.py`.

### Four more weaknesses found during testing

**1. The acoustic rule is nearly a duplicate of the energy rule.** In this catalog,
energy and acousticness correlate at **-0.962** — almost perfectly inverse. So the two
rules that look independent are really one signal counted twice, and the recommender
has 3 real inputs, not 4. It also means `likes_acoustic=True` plus a high `target_energy`
is close to a contradiction: the *Contradictory* profile below asked for both and its
best match scored 4.08, where every other realistic profile cleared 4.8.

**2. One artist can take multiple slots.** The *Chill Lofi* profile returns LoRoom at both
#2 and #3 (Midnight Coding, Focus Flow). There is no diversity rule, so a listener with a
narrow taste gets a narrow list back — a small-scale version of a filter bubble.

**3. The genre bonus reaches almost nobody.** 20 songs are spread across 12 genres, so the
median genre has 1–2 songs. The +2.0 bonus is 40% of the total scale but it can only ever
apply to about 10% of the catalog for a given user. And it is all-or-nothing: `pop punk`
earns **zero** credit against `pop`, exactly as much as jazz would.

**4. An unknown genre degrades silently.** The *Ghost Genre* profile asks for `k-pop`,
which is not in the catalog. The system does not warn, error, or say "no strong matches" —
it returns 5 confident-looking recommendations whose top score is 2.46 out of 5.0. A user
would have no way to tell this list apart from a good one.

### Features the model ignores entirely

`tempo_bpm`, `valence`, and `danceability` are loaded and converted to numbers, then never
scored. A 172 BPM pop punk track and a 90 BPM ballad are interchangeable to the recipe if
their energy values happen to line up. The model also has no idea what any song is *about* —
no lyrics, no language, no artist history, no release year.

---

## 7. Evaluation

### What I tested

Five profiles, all defined in `src/main.py` and runnable with `python -m src.main --all`:

| # | Profile | Genre | Mood | Target energy | Acoustic | Why |
|---|---|---|---|---|---|---|
| 1 | Happy Pop | pop | happy | 0.80 | no | Baseline, mainstream taste |
| 2 | Chill Lofi | lofi | chill | 0.30 | yes | Opposite end of the energy scale |
| 3 | Deep Intense Rock | alternative rock | intense | 0.90 | no | High energy, different genre |
| 4 | **Adversarial** — Contradictory | jazz | relaxed | 0.95 | yes | Every rule pulls a different way |
| 5 | **Adversarial** — Ghost genre | k-pop | focused | 0.50 | no | Genre that isn't in the catalog |

Profiles 4 and 5 were built specifically to try to break the scoring logic rather than to
represent a real person.

### Output for all five profiles

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

Profile: Chill Lofi
  genre=lofi  mood=chill  target_energy=0.3  likes_acoustic=True
------------------------------------------------------------------------
1. Library Rain - Paper Lanterns  [score: 4.85]
   Because: matches your favorite genre (lofi), matches your chill mood, energy (0.35) is close to your target (0.30), has the acoustic feel you like
2. Midnight Coding - LoRoom  [score: 4.68]
   Because: matches your favorite genre (lofi), matches your chill mood, has the acoustic feel you like
3. Focus Flow - LoRoom  [score: 3.74]
   Because: matches your favorite genre (lofi), energy (0.40) is close to your target (0.30), has the acoustic feel you like
4. Spacewalk Thoughts - Orbit Bloom  [score: 2.93]
   Because: matches your chill mood, energy (0.28) is close to your target (0.30), has the acoustic feel you like
5. Coffee Shop Stories - Slow Stereo  [score: 1.84]
   Because: energy (0.37) is close to your target (0.30), has the acoustic feel you like
------------------------------------------------------------------------

Profile: Deep Intense Rock
  genre=alternative rock  mood=intense  target_energy=0.9  likes_acoustic=False
------------------------------------------------------------------------
1. Broken Antenna - The Hollow Wires  [score: 4.81]
   Because: matches your favorite genre (alternative rock), matches your intense mood, energy (0.83) is close to your target (0.90), has the produced, non-acoustic sound you prefer
2. Fading Signal - Grey Static  [score: 3.64]
   Because: matches your favorite genre (alternative rock), has the produced, non-acoustic sound you prefer
3. Last Summer Regret - Detention Hall  [score: 2.96]
   Because: matches your intense mood, energy (0.90) is close to your target (0.90), has the produced, non-acoustic sound you prefer
4. Storm Runner - Voltline  [score: 2.94]
   Because: matches your intense mood, energy (0.91) is close to your target (0.90), has the produced, non-acoustic sound you prefer
5. Gym Hero - Max Pulse  [score: 2.93]
   Because: matches your intense mood, energy (0.93) is close to your target (0.90), has the produced, non-acoustic sound you prefer
------------------------------------------------------------------------

Profile: ADVERSARIAL - Contradictory (loud + relaxed + acoustic)
  genre=jazz  mood=relaxed  target_energy=0.95  likes_acoustic=True
------------------------------------------------------------------------
1. Coffee Shop Stories - Slow Stereo  [score: 4.08]
   Because: matches your favorite genre (jazz), matches your relaxed mood, has the acoustic feel you like
2. Neon Harbor - Sailing Cassette  [score: 2.12]
   Because: matches your relaxed mood
3. Velvet Hours - Suede Marlowe  [score: 2.06]
   Because: matches your relaxed mood
4. Final Boss Ascent - Pixel Forge  [score: 1.51]
   Because: energy (0.94) is close to your target (0.95)
5. Gym Hero - Max Pulse  [score: 1.50]
   Because: energy (0.93) is close to your target (0.95)
------------------------------------------------------------------------

Profile: ADVERSARIAL - Ghost genre (k-pop is not in the catalog)
  genre=k-pop  mood=focused  target_energy=0.5  likes_acoustic=False
------------------------------------------------------------------------
1. Focus Flow - LoRoom  [score: 2.46]
   Because: matches your focused mood, energy (0.40) is close to your target (0.50)
2. Velvet Hours - Suede Marlowe  [score: 1.76]
   Because: energy (0.52) is close to your target (0.50)
3. Slow Confession - Ivory Lane  [score: 1.73]
   Because: energy (0.48) is close to your target (0.50)
4. Neon Harbor - Sailing Cassette  [score: 1.71]
   Because: energy (0.58) is close to your target (0.50)
5. Overworld Theme - Pixel Forge  [score: 1.60]
   Because: has the produced, non-acoustic sound you prefer
------------------------------------------------------------------------
```

### Comparing every pair of profiles

| Pair | What changed | Why that makes sense |
|---|---|---|
| 1 vs 2 | Zero song overlap. Happy Pop gets 0.70–0.93 energy tracks; Chill Lofi gets 0.28–0.42. | These are the two ends of the energy scale, and no genre or mood is shared. This is the cleanest evidence the profile fields are actually driving the output. |
| 1 vs 3 | Only Gym Hero appears in both — at #2 for Happy Pop, #5 for Deep Rock. | Gym Hero is `pop` + `intense`, so it collects the genre bonus from one profile and the mood bonus from the other. Same song, two different reasons. |
| 1 vs 4 | Both want high energy, yet share only Gym Hero (#2 vs #5). | The `relaxed` mood and `likes_acoustic=True` in profile 4 override the shared energy target — proof that energy's 1.5 can't outvote genre + mood + acoustic combined. Gym Hero survives in both lists only because it is the loudest non-acoustic track in the catalog. |
| 1 vs 5 | No overlap except Overworld Theme (#5 in both). | Overworld Theme is the "middle" song: it wins nothing decisively, so it drifts into the bottom of both lists whenever nothing stronger is competing. |
| 2 vs 3 | Zero overlap, and near-mirror-image energies (0.28–0.42 vs 0.74–0.93). | The two profiles are opposites on all four fields, so this is the expected result. If they *had* overlapped, the scoring would be broken. |
| 2 vs 4 | Coffee Shop Stories is #5 for Chill Lofi but #1 for Contradictory. | It's the catalog's only `jazz` song, so the +2.0 genre bonus lifts it from the bottom of one list to the top of another. One rule, four ranks of movement. |
| 2 vs 5 | Focus Flow is #3 for Chill Lofi and #1 for Ghost Genre. | Ghost Genre can never claim the +2.0 genre bonus, so a song only needs a mood match plus decent energy to win. The bar for #1 drops from 4.85 to 2.46. |
| 3 vs 4 | Share only Gym Hero (#5 in both). Final Boss Ascent reaches #4 for profile 4 but misses profile 3's top 5 entirely. | Both profiles want ~0.9 energy, so the loudest tracks float up for each. But profile 3 has two `alternative rock` matches and five `intense` matches competing for slots, while profile 4 has almost nothing — so the same loud songs rank far higher for the profile the system serves worse. |
| 3 vs 5 | No overlap at all. | Profile 5 targets 0.5 energy, and there are no `alternative rock` or `intense` matches to pull anything up. |
| 4 vs 5 | Share Neon Harbor and Velvet Hours (mid-energy r&b / city pop). | Both are profiles the system serves badly, so both fall back on mid-catalog filler. Two very different users get similar recommendations, which is a bad sign. |

### The three things that surprised me

**1. The genre bonus decides the winner more often than the winner deserves.** For Happy
Pop, the gap between #1 and #2 is **1.10 points**, and #2 (Gym Hero) is `intense` — the
opposite of the `happy` mood that was asked for. Gym Hero beats three genuinely happy songs
purely because it's tagged `pop`. Explained to a non-programmer: *the system thinks the
label on the box matters more than what's inside it.*

**2. A song can rank #1 while failing most of the request.** Coffee Shop Stories tops the
Contradictory profile with 4.08 despite having energy 0.37 against a target of 0.95 — it
essentially failed the loudness test completely and still won, because genre + mood +
acoustic together are worth 3.5 and energy is only worth 1.5.

**3. The system never admits it doesn't know.** The Ghost Genre profile produced five
recommendations that *look* identical in format to the good ones. Only the score (2.46 vs
4.88) hints that anything is wrong, and the score isn't shown to a real end user. A useful
recommender should be able to say "I don't have anything for you."

### Experiment: doubling energy, halving genre

I changed `GENRE_WEIGHT` and `ENERGY_WEIGHT` in `src/recommender.py` from 2.0 / 1.5 to
1.0 / 3.0, re-ran the profiles, then restored the original values. Note that the shifted
weights sum to 5.5, not 5.0, so **only ranks are comparable between the two columns, not
raw scores.**

```
Profile: Happy Pop
  BASELINE (genre 2.0 / energy 1.5)              SHIFTED (genre 1.0 / energy 3.0)
  --------------------------------------------------------------------------------------------
  1. Sunrise City (4.88)                         1. Sunrise City (5.35)
  2. Gym Hero (3.78)                             2. Backyard Fireworks (4.21)  <-- changed
  3. Backyard Fireworks (2.83)                   3. Rooftop Lights (4.21)  <-- changed
  4. Rooftop Lights (2.77)                       4. Overworld Theme (4.10)  <-- changed
  5. Overworld Theme (2.75)                      5. Gym Hero (4.08)  <-- changed
  Set overlap: 5/5 songs appear in both top 5s.
  Order kept:  1/5 songs held the exact same rank.
```

**Was it more accurate, or just different?** More accurate — and this was the clearest
result of the whole phase. Gym Hero fell from **#2 to #5**, and the three `happy` songs all
moved up past it. The baseline was ranking an `intense` gym track second for someone who
asked for happy pop; the shifted version ranks all the happy songs above it. That matches
my intuition much better.

Two caveats I'd want to check before calling this a real improvement:

- **The set of songs barely moved.** For Happy Pop, all 5 songs stayed in the top 5 — only
  the order changed. Across all five profiles the set overlap was 4–5 out of 5. With 20
  songs the recommender doesn't have enough material for a weight change to surface
  anything genuinely new, so I can't tell whether this generalizes or is an artifact of a
  tiny catalog.
- **It makes the loudness bias worse.** Doubling the weight on energy doubles the raw point
  advantage that high-energy listeners already get from the skewed catalog, and halving
  genre removes some of the counterweight. Fixing the ranking made the fairness problem
  bigger, which is a real trade-off rather than a free win.

---

## 8. Future Work

These are ordered by how much I think they'd actually fix, not by how hard they'd be.

### 1. Fix the catalog before touching the code

The biggest problem VibeFinder has isn't in `recommender.py` — it's that the CSV is skewed
loud (section 4). Adding 10 low-energy songs across the missing genres would do more for
recommendation quality than any weight change, and it's the cheapest thing on this list. I'd
also add a startup check that prints the catalog's energy distribution and genre counts, so
the skew is visible instead of something you have to go looking for.

### 2. Partial genre credit

Right now `pop` and `pop punk` are as unrelated as `pop` and `jazz`, which is the single
most obviously wrong thing about the recipe. The cheap version: award +1.0 when one genre
string contains the other. The honest version: a small hand-written similarity table
(`pop`↔`indie pop` = 0.7, `rock`↔`alternative rock` = 0.8), which is more work but doesn't
break the moment two related genres don't happen to share a substring — `lofi` and `ambient`
are close neighbors with nothing in common as text.

### 3. Drop or replace the acoustic rule

Energy and acousticness correlate at **-0.962** in this catalog, so the acoustic rule is
mostly re-measuring energy under a different name. I'd either cut it and redistribute its
0.5 points, or swap it for `valence` — which is currently unused and would let a listener
ask for "upbeat" independently of the mood label. That would give the model 4 genuinely
distinct signals instead of 3 signals with one counted twice.

### 4. A diversity rule for the ranking step

The Chill Lofi profile returns the same artist at #2 and #3. A per-artist penalty applied
during ranking — halve a song's score if its artist is already in the list — would fix it.
It belongs in `recommend_songs()`, not `score_song()`, because it's inherently a fact about
the *list*, and keeping `score_song()` pure is what makes the whole thing testable.

### 5. Let the system say "I don't know"

The ghost-genre profile returned five confident-looking recommendations with a top score of
2.46 out of 5. I'd add a threshold: below ~2.5, say "no strong matches for this profile —
here are the closest anyway" instead of presenting weak results in the same format as good
ones. Knowing when to decline is a feature, and it's one almost no real recommender has.

### 6. Richer taste profiles

One favorite genre, one mood, one energy target is a very thin model of a person. I'd allow
a ranked list of genres rather than a single string, and separate "what I want right now"
from "what I like in general" — a listener wanting focus music at 2pm isn't a different
person from the one wanting loud music at the gym.

---

## 9. Personal Reflection

> **Note to self: rewrite this in your own words before submitting.** The events below are
> real — they're what actually happened while building this — but the phrasing is a draft.

### The biggest learning moment

Realizing that **a scoring rule can be perfectly fair and still produce unfair results.**

The energy rule is symmetric by construction. Too loud is penalized exactly as much as too
quiet. I would have defended it as unbiased if someone had asked. Then I measured what score
was actually *reachable* at different energy targets, and a listener who wants quiet music
tops out at 1.27 while a listener who wants loud music reaches 1.96 — a 54% gap that has
nothing to do with the code and everything to do with which songs are in the CSV.

What makes this stick is that **I caused it.** I added ten songs to the catalog, nine of them
high-energy, because I was optimizing for genre diversity and never looked at the numerical
distribution. I introduced the bias while actively trying to make the dataset better, and I
didn't find it by reading the code — I found it by measuring the output. That's a different
skill from writing correct functions, and it's the one this project actually taught me.

### How AI helped, and where I had to check it

AI was fastest at the things where I could immediately tell whether the answer was right:
CSV parsing, sorting idioms, `.sort()` vs `sorted()`, docstrings. Structural work — one
scoring engine feeding both the dict API and the dataclass API — also went well, because
"don't write the recipe twice" is a judgment I could evaluate on sight.

Where I had to be careful:

- **Numbers in prose.** Several claims written into this model card were wrong until they
  were checked against a live run. Two entries in the pairwise comparison table stated the
  wrong overlap between profiles, and my README worked example said a score was 2.84 when
  the code produces 2.83. Confident, specific, and false is the worst failure mode, because
  it's the one that reads like it was verified.
- **Tests passing for the wrong reason.** The starter `Recommender.recommend()` returned
  `self.songs[:k]` — no scoring at all — and the test suite passed, because the pop song
  happened to be first in the list. A green checkmark meant nothing here.
- **Silent bugs.** The float rounding issue (`0.8 - 0.70` being `0.10000000000000009`) never
  crashed and never showed up in any test. It just quietly withheld one explanation. It only
  surfaced because I compared the output line by line against the spec I'd written down.

The pattern: AI is reliable for code whose correctness I can see, and unreliable for claims
about what the code *did* — those have to be re-derived from a real run every time.

### What surprised me about how simple this is

Four `if` statements and a `sort` produce output that feels like it understands something.
Sunrise City at 4.88 for a happy-pop listener looks like insight, and it's arithmetic on
four columns.

The unsettling part is the reverse case. When VibeFinder is asked for a genre that doesn't
exist, it returns five recommendations in exactly the same confident format, with the same
reassuring "Because:" lines. The only signal that something is wrong is a score of 2.46 —
and real apps don't show you the score. I've spent a lot of time assuming a recommendation
feed reflects some understanding of me. Now my first question is what a *bad* result would
look like, and whether I'd be able to tell.

### What I'd try next

Fix the catalog skew I created, then partial genre credit. But the thing I'm most curious
about is building the evaluation *first* next time — writing the "what does the best
possible score look like for different users" check before tuning any weights. Every real
finding in this project came from measuring, and I did all of it at the end, after the
design decisions were already locked in.
