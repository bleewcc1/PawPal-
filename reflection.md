# PawPal+ Reflection

## 1. Design Choices

**Four classes, one job each.** `Task`, `Pet`, `Owner`, and `Scheduler` map
directly to the assignment's required structure: `Task` is pure data plus
small behaviors (`mark_complete`, `is_overdue`, `next_occurrence`), `Pet`
owns its own `tasks` list, `Owner` owns a household of `Pet`s and exposes
`get_all_tasks()`, and `Scheduler` is the only class that ranks/filters
anything -- and it does so exclusively through `Owner.get_all_tasks()`,
never by reaching into a `Pet` directly. That indirection is what makes
ranking, sorting, filtering, and conflict detection correct across any
number of pets instead of just one.

**A flat `Task` with a `category` string, not subclasses.** An earlier
draft had `Feeding`/`Walk`/`Medication`/`Appointment` as subclasses of an
abstract `Task`. I flattened that into a single `Task` class with a plain
`category: str` used only for priority weighting (via the `CATEGORY_WEIGHT`
dict). This keeps exactly four classes in the system, as required, and
means adding a new category is a one-line dict entry rather than a new
class.

**Priority as a sortable tuple, not nested conditionals.**
`Task.priority_key(now)` returns `(overdue_rank, category_weight,
scheduled_time)`, and `Scheduler.get_upcoming_tasks()` feeds that straight
into `heapq.nsmallest`. Ranking logic lives in one small, declarative
function instead of branching if/else code, and Python's tuple comparison
does the "overdue beats category beats time" precedence for free.

**`Scheduler` re-queries `Owner` on every call instead of caching.**
`filter_tasks()`, `sort_by_time()`, `get_upcoming_tasks()`, etc. all pull a
fresh list from `owner.get_all_tasks()` each time rather than maintaining
their own copy. This trades a small amount of repeated work (irrelevant at
the scale of one household's pet-care tasks) for a guarantee that results
are never stale after a pet or task is added, removed, or completed.

**Recurrence anchored to the original time, not "now."**
`Task.next_occurrence()` computes `self.scheduled_time + interval`, not
`datetime.now() + interval`. A `daily` 8am task completed late at 2pm still
recurs at 8am tomorrow, not 2pm tomorrow -- otherwise the schedule would
drift later every time a task was completed late.

**Persistence as plain JSON dicts, not pickling.** `to_dict()`/`from_dict()`
on `Task`, `Pet`, and `Owner` produce human-readable, diffable JSON rather
than a binary pickle. It's more code than `pickle.dump`, but the save file
stays inspectable and doesn't break if the class definitions change shape
later.

## 2. Tradeoffs

### 2a. Flat `Task` + category string vs. typed subclasses

Pro: satisfies the four-class requirement exactly, and priority weighting
is a single dict lookup (`CATEGORY_WEIGHT.get(self.category, ...)`) instead
of per-subclass overrides. Con: there's no compile-time guarantee that a
"feeding" task carries feeding-specific fields, and a typo'd category
string (e.g. `"medicaton"`) silently falls back to the lowest priority
weight instead of raising. I accepted this because the assignment's `Task`
is explicitly meant to be minimal (description, time, frequency,
completion), and category is only ever used for sorting, never for
branching behavior.

### 2b. Tradeoffs

`Scheduler.find_conflicts()` only flags two tasks as conflicting when their
`scheduled_time` values are exactly equal, not when they'd merely overlap
(e.g. a 30-minute walk at 5:00 PM and a vet appointment at 5:15 PM). This
was a deliberate simplification rather than an oversight: `Task` only has a
single `scheduled_time`, not a duration or end time, so there's nothing to
compute an overlap *against* -- the assignment's four-attribute `Task`
(description, time, frequency, completion) doesn't carry one. Exact-match
grouping is also cheap: one pass to bucket tasks by timestamp plus a sort
of the distinct times, versus the sort-and-sweep an interval-overlap check
would need (sort all tasks by start time, then compare each task's start
against the running end of the previous one).

The cost is false negatives: two back-to-back tasks that would genuinely
clash in a real calendar go undetected if they don't start at the identical
minute. I accepted that gap for now rather than adding a `duration` field
to `Task`, since it would widen the data model beyond what this milestone
asked for. If PawPal+ later needs real overlap detection, that's the
concrete next step: give `Task` a duration/end time and swap the grouping
logic in `find_conflicts()` for an interval-sweep.

### 2c. Fixed 30-day `timedelta` for "monthly," not a calendar month

`FREQUENCY_INTERVALS["monthly"] = timedelta(days=30)` is an approximation:
completing a monthly task on Jan 31 produces a next occurrence on Mar 2,
not "the 31st of next month" (which doesn't always exist) or Feb 28. The
alternative -- true calendar-month arithmetic -- needs either manual
month/year rollover logic or a third-party dependency like
`dateutil.relativedelta`, neither of which felt justified for a
feature that's a small fraction of the app's total task volume (most
pet-care tasks are daily or weekly). I accepted the drift and documented
it here rather than silently letting it surprise someone later.

## 3. AI Strategy

### Which AI coding assistant features were most effective for building your scheduler?

Three, specifically:

- **Actually running code instead of just writing it.** The most valuable
  moments weren't suggestions, they were verification: having the
  assistant execute a reproduction script for the double-completion bug
  before touching a line of code, re-running `python main.py` after every
  change to `pawpal_system.py`, and running `python -m pytest` after every
  subsequent edit. A suggestion that "should work" is a guess; a
  suggestion that just printed passing output in front of me is a fact.
- **Driving the Streamlit app with a real headless browser (Playwright)**
  rather than declaring the UI done once the code looked plausible. It
  caught nothing dramatic this time, but it's the only way "the UI works"
  is actually a verified claim instead of a hope -- and it did surface,
  visually, that a scheduling conflict warning appeared and then correctly
  cleared once the collision was resolved.
- **Reading the whole relevant file before editing it**, so new methods
  (`sort_by_time`, `filter_tasks`, `find_conflicts`) and their docstrings
  stayed consistent with the actual method signatures already in
  `pawpal_system.py` instead of subtly drifting from them.

### One AI suggestion I rejected or modified to keep the design clean

The clearest example: the assistant's first, unprompted pass at
`pawpal_system.py` built an abstract `Task` base class with
`Feeding`/`Walk`/`Medication`/`Appointment` subclasses, plus a fifth
`PawPalSystem` facade class wrapping `Owner` and `Scheduler` together for
persistence and CLI convenience. It was reasonable OOP, but it was *more*
system than the assignment called for, and it actively worked against one
requirement: `Scheduler` needs to read every pet's tasks through
`Owner.get_all_tasks()`, and a facade class sitting on top blurred exactly
who was responsible for that. I rejected the whole pass and had it rebuild
around a flat `Task` with a `category` string and exactly four classes
(see section 2a). A smaller, more constrained system turned out to be the
correct one, not just the simpler one.

A second, smaller example from later on: for the Streamlit UI, I rejected
hotlinking external "happy dog" photo URLs the assistant couldn't verify
were actually live, in favor of a CSS/emoji hero banner that renders with
zero network dependency. Nicer-sounding isn't the same as reliable, and a
broken-image icon in a submitted screenshot is worse than a simpler but
guaranteed-working banner.

### How did using separate chat sessions for different phases help you stay organized?

The git history splits cleanly along the CLI-first phases the assignment
asks for: scaffolding the four classes and their skeletons, writing
`main.py` as a demo script, and adding the first pytest smoke tests each
landed as their own commit before I ever brought up the scheduling
algorithms (sorting, filtering, conflict detection, the recurrence guard)
or the Streamlit UI in a later session. Keeping the backend-scaffolding
phase in its own session meant that session's context stayed entirely
about "does the core logic work," so I could review and commit a small,
understandable diff before moving on. Starting fresh for the
algorithms/UI phase meant that session could treat the already-committed
backend as ground truth -- something to build on and test against --
rather than something still being negotiated. It mirrors the CLI-first
principle itself: verify and lock in one layer before the next layer is
allowed to depend on it, at the level of my own workflow, not just the
code's.

### What I learned about being the "lead architect" when collaborating with powerful AI tools

Left unconstrained, the assistant defaults to the most general, most
"impressive" version of a solution -- the subclass hierarchy plus facade
class was good software engineering in the abstract, and still the wrong
answer for this assignment. Being the lead architect meant my job was to
supply the actual constraints (exactly four classes; `Scheduler` must go
through `Owner.get_all_tasks()`) before asking for a design, not to
react to whatever came out first. The assistant was excellent at
mechanical thoroughness once a target was clear -- writing the matching
test for every new method, formatting terminal output, running
verification loops without being asked twice -- but the decisions that
actually shaped the system (which four classes, which tradeoffs were
acceptable, when "it runs" was enough versus when an edge case like
double-completion needed a real guard) stayed mine to make. The
discipline that mattered most wasn't writing code myself, it was refusing
to accept a result -- a design, a test suite, a UI -- until I'd either
understood why it was correct or watched it prove itself.
