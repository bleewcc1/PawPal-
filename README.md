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

## Running the tests

```
pip install -r requirements.txt
pytest -q
```

`tests/` has one file per core class, exercising completion/overdue logic,
recurrence, Owner's multi-pet task aggregation, and the Scheduler's
priority ranking.

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
