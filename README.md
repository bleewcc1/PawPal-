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
=== PawPal+ Today's Schedule ===
Owner: Jordan  |  Pets: Rex, Milo

  🍽  [OVERDUE ] Mon 09:38 PM  |  Rex      |  feeding     |  Breakfast: chicken & rice
  💊  [upcoming] Tue 12:38 AM  |  Rex      |  medication  |  Heartworm pill
  🩺  [upcoming] Wed 01:38 AM  |  Milo     |  appointment |  Vet checkup
  🍽  [upcoming] Tue 06:38 AM  |  Milo     |  feeding     |  Wet food dinner
  🐕  [upcoming] Tue 04:38 AM  |  Rex      |  walk        |  Evening walk around the block

Overdue tasks: 1  |  Total pending: 5
```
