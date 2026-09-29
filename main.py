"""
main.py -- CLI testing ground for pawpal_system.py.

Creates an Owner with two Pets, gives them a handful of Tasks at different
times, and prints "Today's Schedule" ranked by the Scheduler so the core
logic can be sanity-checked before any UI is built on top of it.
"""

from datetime import datetime, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task

CATEGORY_ICONS = {
    "medication": "\U0001F48A",  # pill
    "appointment": "\U0001FA7A",  # stethoscope
    "feeding": "\U0001F37D",  # plate
    "walk": "\U0001F415",  # dog
    "general": "\U0001F4CC",  # pin
}


def format_task(task: Task, now: datetime) -> str:
    icon = CATEGORY_ICONS.get(task.category, CATEGORY_ICONS["general"])
    status = "OVERDUE " if task.is_overdue(now) else "upcoming"
    pet_name = task.pet.name if task.pet else "?"
    time_str = task.scheduled_time.strftime("%a %I:%M %p")
    return (
        f"  {icon}  [{status}] {time_str}  |  {pet_name:<8} |  "
        f"{task.category:<11} |  {task.description}"
    )


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

    print("=== PawPal+ Today's Schedule ===")
    print(f"Owner: {owner.name}  |  Pets: {', '.join(p.name for p in owner.list_pets())}")
    print()

    ranked = scheduler.get_upcoming_tasks()
    if not ranked:
        print("  Nothing scheduled.")
    for task in ranked:
        print(format_task(task, now))

    overdue = scheduler.get_overdue_tasks()
    print()
    print(f"Overdue tasks: {len(overdue)}  |  Total pending: {len(ranked)}")


if __name__ == "__main__":
    main()
