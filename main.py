"""
main.py -- CLI testing ground for pawpal_system.py.

Creates an Owner with two Pets, gives them a handful of Tasks at different
times, and prints "Today's Schedule" ranked by the Scheduler so the core
logic can be sanity-checked before any UI is built on top of it.
"""

from datetime import datetime, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def format_task_row(task: Task) -> str:
    """One fixed-width row: #id  pet  category  time  description."""
    time_str = task.scheduled_time.strftime("%a %I:%M %p")
    return (
        f"  #{task.task_id:<3} {task.pet.name:<8} {task.category:<11} "
        f"{time_str:<12} {task.description}"
    )


def print_section(title: str, tasks: list[Task]) -> None:
    header = f"{title} ({len(tasks)})"
    print(header)
    print("-" * len(header))
    if not tasks:
        print("  (none)")
    for task in tasks:
        print(format_task_row(task))
    print()


def print_schedule(owner: Owner, scheduler: Scheduler, now: datetime) -> None:
    ranked = scheduler.get_upcoming_tasks(now=now)
    overdue = [t for t in ranked if t.is_overdue(now)]
    upcoming = [t for t in ranked if not t.is_overdue(now)]

    width = 60
    print("=" * width)
    print("  PawPal+ -- Today's Schedule".ljust(width))
    print("=" * width)
    print(f"Owner: {owner.name}    Pets: {', '.join(p.name for p in owner.list_pets())}")
    print()

    print_section("OVERDUE", overdue)
    print_section("UPCOMING", upcoming)

    print("-" * width)
    print(f"Total pending: {len(ranked)}   Overdue: {len(overdue)}")


def main() -> None:
    now = datetime.now()
    owner = Owner("Jordan")

    rex = Pet("Rex", "Dog", breed="Labrador", age=4)
    milo = Pet("Milo", "Cat", breed="Tabby", age=2)
    owner.add_pet(rex)
    owner.add_pet(milo)

    # Added deliberately out of chronological order, to prove sort_by_time()
    # (not just insertion order) is what puts these back in time order.
    walk = rex.add_task(
        Task("Evening walk around the block", now + timedelta(hours=6), frequency="daily", category="walk")
    )
    breakfast = rex.add_task(
        Task("Breakfast: chicken & rice", now - timedelta(hours=1), frequency="daily", category="feeding")
    )
    dinner = milo.add_task(
        Task("Wet food dinner", now + timedelta(hours=8), frequency="daily", category="feeding")
    )
    pill = rex.add_task(
        Task("Heartworm pill", now + timedelta(hours=2), frequency="monthly", category="medication")
    )
    # Deliberately scheduled at the exact same time as the heartworm pill
    # above, for a different pet, to exercise Scheduler.find_conflicts().
    checkup = milo.add_task(
        Task("Vet checkup", now + timedelta(hours=2), frequency="once", category="appointment")
    )

    scheduler = Scheduler(owner)

    print_schedule(owner, scheduler, now)

    print("=" * 60)
    print("  Sorting & Filtering Checks".ljust(60))
    print("=" * 60)
    print()

    # sort_by_time(): pure chronological order, ignoring category/overdue rank.
    print_section("ALL PENDING TASKS -- sort_by_time()", scheduler.sort_by_time())

    # Complete the overdue, recurring breakfast task -- Scheduler.complete_task()
    # should mark it done AND auto-create tomorrow's occurrence.
    print(f"Completing task #{breakfast.task_id} ({breakfast.description})...")
    next_breakfast = scheduler.complete_task(breakfast.task_id)
    if next_breakfast is not None:
        print(
            f"  -> recurring task auto-rescheduled: new task #{next_breakfast.task_id} "
            f"at {next_breakfast.scheduled_time:%a %I:%M %p}"
        )
    print()

    # filter_tasks(): completion-status and per-pet filters, after that completion.
    print_section("COMPLETED TASKS -- filter_tasks(completed=True)", scheduler.filter_tasks(completed=True))
    print_section(
        "REX'S PENDING TASKS -- filter_tasks(pet_name='Rex', completed=False)",
        scheduler.filter_tasks(pet_name="Rex", completed=False),
    )

    # find_conflicts(): Rex's heartworm pill and Milo's vet checkup were
    # scheduled at the exact same time -- this should surface as a warning,
    # not raise an exception.
    print("CONFLICT CHECK -- find_conflicts()")
    print("-" * 35)
    conflicts = scheduler.find_conflicts()
    if not conflicts:
        print("  (none)")
    for warning in conflicts:
        print(f"  WARNING: {warning}")


if __name__ == "__main__":
    main()
