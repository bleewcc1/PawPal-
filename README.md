# PawPal+

A smart pet care management system. Tracks feedings, walks, medications, and
appointments across multiple pets, and uses a priority-based scheduling
algorithm to surface what needs attention first.

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
