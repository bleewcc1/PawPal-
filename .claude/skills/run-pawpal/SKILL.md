---
name: run-pawpal
description: Run and verify PawPal+ locally -- the CLI test script (main.py) and, once it exists, the Streamlit UI (app.py). Use whenever the user asks to run, test, demo, or see PawPal+ working.
---

# Run PawPal+

PawPal+ follows a CLI-first workflow: verify core logic in the terminal
before touching the UI.

## 1. Verify core logic (always do this first)

```
python main.py
```

This imports `Owner`, `Pet`, `Task`, `Scheduler` from `pawpal_system.py`,
builds a sample household, and prints a ranked "Today's Schedule" to the
terminal. If this doesn't run cleanly, fix `pawpal_system.py` before doing
anything else -- the UI is only a thin layer on top of this logic.

Read the printed schedule and sanity-check the ranking: overdue tasks
first, then category urgency (medication > appointment > feeding > walk),
then soonest due time.

## 2. Run the Streamlit UI (once app.py exists)

```
pip install -r requirements.txt   # first time only
streamlit run app.py
```

This opens the app in the browser. Exercise the golden path (add a pet,
add a task, mark one complete, confirm the schedule re-ranks) and a couple
of edge cases (no pets yet, all tasks completed, an overdue task) before
reporting a change as working.

## Notes

- `pawpal_system.py` is UI-agnostic on purpose -- both `main.py` and
  `app.py` should drive it the same way, through `Owner` and `Scheduler`,
  never by poking at a `Pet`'s task list directly from the UI layer.
- Local data (if persistence is added) belongs in `data/`, which is
  gitignored.
