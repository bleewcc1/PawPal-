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
  #1   Rex      feeding     Mon 09:45 PM Breakfast: chicken & rice

UPCOMING (4)
------------
  #2   Rex      medication  Tue 12:45 AM Heartworm pill
  #4   Milo     appointment Wed 01:45 AM Vet checkup
  #5   Milo     feeding     Tue 06:45 AM Wet food dinner
  #3   Rex      walk        Tue 04:45 AM Evening walk around the block

------------------------------------------------------------
Total pending: 5   Overdue: 1
```
