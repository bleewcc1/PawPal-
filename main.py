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

    rex.add_task(
        Task("Breakfast: chicken & rice", now - timedelta(hours=1), frequency="daily", category="feeding")
    )
    rex.add_task(
        Task("Heartworm pill", now + timedelta(hours=2), frequency="monthly", category="medication")
    )
    rex.add_task(
        Task("Evening walk around the block", now + timedelta(hours=6), frequency="daily", category="walk")
    )
    milo.add_task(
        Task("Vet checkup", now + timedelta(days=1, hours=3), frequency="once", category="appointment")
    )
    milo.add_task(
        Task("Wet food dinner", now + timedelta(hours=8), frequency="daily", category="feeding")
    )

    scheduler = Scheduler(owner)

    print_schedule(owner, scheduler, now)


if __name__ == "__main__":
    main()
