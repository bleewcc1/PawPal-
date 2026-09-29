# AI Collaboration Reflection

## What AI suggested

I used Claude Code as a pair-programmer for PawPal+'s core logic. Before I
gave it the actual class skeleton the assignment specifies, it went ahead
and designed its own version of `pawpal_system.py`: an abstract `Task` base
class with separate `Feeding`/`Walk`/`Medication`/`Appointment` subclasses,
a `Scheduler` that owned its own internal task registry, and a fifth
`PawPalSystem` facade class wrapping everything for persistence and CLI
convenience.

Once I gave it the real requirement -- exactly four classes (`Task`,
`Pet`, `Owner`, `Scheduler`), with `Pet` owning its own tasks and
`Scheduler` required to read from `Owner.get_all_tasks()` instead of
touching a `Pet` directly -- it proposed the design that's actually in the
repo now: a flat `Task` with a `category` string used only for priority
weighting, `Pet.tasks` as the real source of truth, `Owner.get_all_tasks()`
as the single aggregation point, and `Scheduler` holding a reference to the
`Owner` and re-querying `get_all_tasks()` on every call so it never goes
stale.

It also suggested things along the way I hadn't asked for directly: a
`heapq.nsmallest`-based ranking instead of a hand-rolled sort, JSON
save/load on `Owner`, a `pytest` suite with one file per class plus shared
fixtures, and a `.claude/skills/run-pawpal` skill documenting how to
run/test the project.

## What I accepted or rejected

I rejected the first pass entirely -- the subclass hierarchy and the extra
`PawPalSystem` facade were more machinery than the assignment asked for,
and the "multi-pet point" specifically requires `Scheduler` to go through
`Owner.get_all_tasks()`, which the subclass-based design didn't enforce. I
had it rebuild around the four required classes instead.

I accepted the `Owner.get_all_tasks()` aggregation design once it was
explained: `Scheduler` never stores its own copy of tasks or reaches into
a `Pet`, it just asks the `Owner` fresh each time. That's the one design
decision I leaned on the AI's judgment for the most, since I wasn't sure
how to wire multi-pet scheduling correctly.

I also asked it to redo the terminal output twice: first to drop an
emoji-heavy layout for something more readable, then to separate overdue
from upcoming tasks into their own labeled sections. Both changes were
straightforward once I flagged the readability problem, and I kept the
result.

I accepted the `pytest` suite as designed, but caught one gap myself: it
initially only tested that a task got added to a pet's list, not that the
list's length actually increased, so I asked for an explicit count-based
test before considering task-addition covered.

## How I verified the result

For every change, I had it re-run `python main.py` and read the printed
schedule myself to confirm the ranking made sense (overdue first, then
medication > appointment > feeding > walk, then soonest time). Once the
`pytest` suite existed, I ran `python -m pytest` after every subsequent
change to `pawpal_system.py` and confirmed all tests passed (28 total,
covering completion, overdue detection, recurrence, multi-pet
aggregation, and priority ranking). I also had it confirm the test suite
still worked when invoked from outside the project directory, which
caught a real import-path bug before it could bite me later. Finally, I
reviewed the actual diffs and `git status` output at each step rather than
just trusting the AI's summary of what it changed.
