# PawPal+

A smart pet care management system. Tracks feedings, walks, medications, and
appointments across multiple pets, and uses a priority-based scheduling
algorithm to surface what needs attention first.

## Implementation Summary

The core (`pawpal_system.py`) is four small classes that each do one job and
compose into the whole system. A **Task** is the atomic unit -- a
description, a scheduled time, a frequency, and a completion flag. A **Pet**
just owns a list of its own `Task`s. An **Owner** owns a household of `Pet`s
and exposes `get_all_tasks()`, which flattens every pet's list into one
combined collection. The **Scheduler** is the only class that does any
"thinking": it never reaches into a `Pet` directly, it always asks the
`Owner` for the full task list via `get_all_tasks()`, then ranks whatever
comes back by overdue status, category urgency (medication > appointment >
feeding > walk), and soonest due time. That one indirection --
Scheduler → Owner → Pet -- is what makes the ranking correct across an
arbitrary number of pets instead of just one, and it's what
`tests/test_owner.py` and `tests/test_scheduler.py` exercise directly.

The rest of the system builds on top of that core without changing it:
`main.py` is a CLI script that wires up a sample `Owner`/`Pet`s/`Task`s and
prints the `Scheduler`'s ranked output, used to verify the logic works
before any UI touches it, and the `pytest` suite in `tests/` locks in that
same behavior (completion, overdue detection, recurrence, multi-pet
aggregation, and priority ranking) so future changes can't silently break
it.

## Architecture

Core logic lives in `pawpal_system.py`, with four classes:

- **Task** -- a single activity: description, scheduled time, frequency
  (`once`/`daily`/`weekly`/`monthly`), completion status, and a category used
  for priority weighting.
- **Pet** -- a pet's details plus the list of `Task`s that belong to it.
- **Owner** -- manages multiple `Pet`s. `get_all_tasks()` flattens every
  pet's tasks into one collection.
- **Scheduler** -- the "brain." It reads `Owner.get_all_tasks()` (never a
  single `Pet` directly) and ranks pending tasks by: overdue status, then
  category urgency (medication > appointment > feeding > walk), then
  soonest due time. It also handles marking tasks complete and
  auto-rescheduling recurring ones.

`main.py` is the CLI testing ground used to verify this logic works before
any UI is built on top of it.

## Smarter Scheduling

Beyond basic priority ranking, `Scheduler` implements four specific
behaviors:

- **Sorting by time** -- `Scheduler.sort_by_time(pet_name=None)` returns
  pending tasks ordered purely by `scheduled_time`, earliest first,
  ignoring category weight entirely. Useful when you just want "what's
  next chronologically" rather than a priority-weighted view.

- **Filtering by pet or completion status** --
  `Scheduler.filter_tasks(pet_name=None, completed=None)` narrows the full
  task list by either or both criteria (e.g. `completed=True` for a
  history view, `pet_name="Rex", completed=False` for one pet's open
  tasks). Both filters are optional and combine, and every other query
  method (`get_upcoming_tasks`, `sort_by_time`, `get_overdue_tasks`) is
  itself built on top of this one filter.

- **Conflict detection** -- `Scheduler.find_conflicts(pet_name=None)`
  groups pending tasks by exact `scheduled_time` and returns a
  human-readable warning string for every time slot with two or more
  tasks in it (whether for the same pet or different pets). It never
  raises -- an empty list just means no conflicts -- since a scheduling
  clash is a heads-up for the owner, not a program error. See
  `reflection.md` section 2b for the tradeoff this design makes
  (exact-time matches only, not overlapping durations).

- **Recurring task logic** -- `Task.next_occurrence()` builds the next
  instance of a `daily`/`weekly`/`monthly` task by adding a fixed
  `timedelta` to its *original* `scheduled_time` (not the completion
  time, so a late completion doesn't drift the schedule).
  `Scheduler.complete_task(task_id)` calls this automatically whenever a
  recurring task is marked done, appending the new occurrence to the same
  pet so it shows up in the very next query.

## Running the CLI demo

```
python main.py
```

## Testing PawPal+

```
pip install -r requirements.txt
python -m pytest
```

`tests/` has one file per core class (`test_task.py`, `test_pet.py`,
`test_owner.py`, `test_scheduler.py`), 40 tests total, all passing. Coverage
includes:

- **Sorting correctness** -- tasks come back in true chronological order
  from `sort_by_time()`, regardless of category or insertion order
  (`test_sort_by_time_ignores_category_and_overdue_status`).
- **Recurrence logic** -- completing a `daily` task creates a new one
  scheduled for exactly the following day
  (`test_complete_task_marks_done_and_reschedules_recurring_task`), and
  completing an *already-completed* task raises instead of silently
  spawning a duplicate occurrence
  (`test_complete_task_raises_if_already_completed_and_does_not_double_recur`).
- **Conflict detection** -- `find_conflicts()` flags two tasks at the exact
  same time, whether for the same pet or different pets
  (`test_find_conflicts_detects_same_pet_double_booking`,
  `test_find_conflicts_detects_same_time_across_different_pets`), and
  correctly reports no conflicts once completed tasks are excluded.
- **Multi-pet aggregation and priority ranking** -- `Owner.get_all_tasks()`
  correctly combines every pet's tasks, and `Scheduler` ranks overdue
  status above category urgency above soonest due time.
- **Persistence** -- an `Owner` (with pets and tasks) round-trips through
  `save()`/`load()` without losing data.

Run `python main.py` alongside the tests for a terminal-visible sanity
check of the same behavior -- see Sample Output below.

### Test run output

```
============================= test session starts ==============================
platform darwin -- Python 3.11.6, pytest-9.1.1, pluggy-1.6.0
rootdir: /Volumes/T7Shield/CodePath/AppliedAI/AI110/week4/Project/PawPal+
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.8.0
collected 40 items

tests/test_owner.py .....                                                [ 12%]
tests/test_pet.py .....                                                  [ 25%]
tests/test_scheduler.py .....................                            [ 77%]
tests/test_task.py .........                                             [100%]

============================== 40 passed in 0.03s ==============================
```

### Confidence Level

Confidence Level: ★★★★☆ (4/5)

The core logic -- sorting, filtering, recurrence, conflict detection,
multi-pet aggregation, and persistence -- is well covered and every test
passes deterministically (fixed `now` fixture, no reliance on real clock
time or randomness). I'm not giving 5/5 because coverage is at the unit
level only: there's no test yet exercising the system the way a real user
would end-to-end (add a pet, add several tasks, complete some, reload from
disk, all in one flow), and known simplifications like exact-time-only
conflict detection and the fixed 30-day "monthly" interval (see
`reflection.md` section 2b) mean the system is reliable for what it
promises, not for every real-world scheduling nuance.

## Sample Output

```
============================================================
  PawPal+ -- Today's Schedule                               
============================================================
Owner: Jordan    Pets: Rex, Milo

OVERDUE (1)
-----------
  #2   Rex      feeding     Mon 10:11 PM Breakfast: chicken & rice

UPCOMING (4)
------------
  #4   Rex      medication  Tue 01:11 AM Heartworm pill
  #5   Milo     appointment Tue 01:11 AM Vet checkup
  #3   Milo     feeding     Tue 07:11 AM Wet food dinner
  #1   Rex      walk        Tue 05:11 AM Evening walk around the block

------------------------------------------------------------
Total pending: 5   Overdue: 1
============================================================
  Sorting & Filtering Checks                                
============================================================

ALL PENDING TASKS -- sort_by_time() (5)
---------------------------------------
  #2   Rex      feeding     Mon 10:11 PM Breakfast: chicken & rice
  #4   Rex      medication  Tue 01:11 AM Heartworm pill
  #5   Milo     appointment Tue 01:11 AM Vet checkup
  #1   Rex      walk        Tue 05:11 AM Evening walk around the block
  #3   Milo     feeding     Tue 07:11 AM Wet food dinner

Completing task #2 (Breakfast: chicken & rice)...
  -> recurring task auto-rescheduled: new task #6 at Tue 10:11 PM

COMPLETED TASKS -- filter_tasks(completed=True) (1)
---------------------------------------------------
  #2   Rex      feeding     Mon 10:11 PM Breakfast: chicken & rice

REX'S PENDING TASKS -- filter_tasks(pet_name='Rex', completed=False) (3)
------------------------------------------------------------------------
  #1   Rex      walk        Tue 05:11 AM Evening walk around the block
  #4   Rex      medication  Tue 01:11 AM Heartworm pill
  #6   Rex      feeding     Tue 10:11 PM Breakfast: chicken & rice

CONFLICT CHECK -- find_conflicts()
-----------------------------------
  WARNING: Scheduling conflict at 2026-09-29 01:11 AM: Rex's 'Heartworm pill', Milo's 'Vet checkup'
```
