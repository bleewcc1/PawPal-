"""
PawPal+ core system.

Four classes, each with one job:
  Task     - a single activity: description, time, frequency, completion status.
  Pet      - a pet's details plus the list of Tasks that belong to it.
  Owner    - manages multiple Pets; get_all_tasks() aggregates every pet's tasks.
  Scheduler- the "brain": reads Owner.get_all_tasks() and ranks/organizes/manages
             tasks across every pet. It never reaches into a single Pet directly.

This module is UI-agnostic. demo.py (CLI) and app.py (Streamlit) both import
Owner/Pet/Task/Scheduler and drive them the same way.
"""

from __future__ import annotations

import itertools
import json
from datetime import datetime, timedelta
from heapq import nsmallest
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Priority model (used by Scheduler to rank tasks)
# ---------------------------------------------------------------------------

# Lower number = inherently more urgent category, all else being equal.
CATEGORY_WEIGHT = {
    "medication": 0,
    "appointment": 1,
    "feeding": 2,
    "walk": 3,
}
DEFAULT_CATEGORY_WEIGHT = 4

# How far apart recurring occurrences of a task are.
FREQUENCY_INTERVALS = {
    "once": None,
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}


class Task:
    """A single activity: description, scheduled time, frequency, completion."""

    _id_counter = itertools.count(1)

    def __init__(
        self,
        description: str,
        scheduled_time: datetime,
        frequency: str = "once",
        completed: bool = False,
        category: str = "general",
    ):
        if frequency not in FREQUENCY_INTERVALS:
            raise ValueError(f"Unknown frequency {frequency!r}; expected one of {list(FREQUENCY_INTERVALS)}")

        self.task_id = next(Task._id_counter)
        self.description = description
        self.scheduled_time = scheduled_time
        self.frequency = frequency
        self.completed = completed
        self.category = category
        self.pet: Optional["Pet"] = None  # back-reference, set by Pet.add_task

    # -- behavior -----------------------------------------------------------

    def mark_complete(self) -> None:
        self.completed = True

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now()
        return (not self.completed) and self.scheduled_time < now

    def recurrence_interval(self) -> Optional[timedelta]:
        return FREQUENCY_INTERVALS[self.frequency]

    def next_occurrence(self) -> Optional["Task"]:
        """If recurring, build the next instance of this task (not yet added anywhere)."""
        interval = self.recurrence_interval()
        if interval is None:
            return None
        nxt = Task(
            description=self.description,
            scheduled_time=self.scheduled_time + interval,
            frequency=self.frequency,
            completed=False,
            category=self.category,
        )
        return nxt

    def priority_key(self, now: Optional[datetime] = None):
        """Sort key: overdue first, then category urgency, then soonest due."""
        now = now or datetime.now()
        overdue_rank = 0 if self.is_overdue(now) else 1
        weight = CATEGORY_WEIGHT.get(self.category, DEFAULT_CATEGORY_WEIGHT)
        return (overdue_rank, weight, self.scheduled_time)

    # -- display --------------------------------------------------------------

    def __repr__(self) -> str:
        status = "done" if self.completed else "pending"
        pet_name = self.pet.name if self.pet else "?"
        return f"<Task #{self.task_id} {pet_name}: {self.description!r} @ {self.scheduled_time:%Y-%m-%d %H:%M} ({status})>"

    # -- persistence --------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "scheduled_time": self.scheduled_time.isoformat(),
            "frequency": self.frequency,
            "completed": self.completed,
            "category": self.category,
        }

    @staticmethod
    def from_dict(data: dict) -> "Task":
        task = Task(
            description=data["description"],
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
            frequency=data["frequency"],
            completed=data["completed"],
            category=data["category"],
        )
        task.task_id = data["task_id"]
        return task


class Pet:
    """A pet's details plus the list of Tasks that belong to it."""

    def __init__(self, name: str, species: str, breed: str = "", age=None, weight=None, notes: str = ""):
        self.name = name
        self.species = species
        self.breed = breed
        self.age = age
        self.weight = weight
        self.notes = notes
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> Task:
        task.pet = self
        self.tasks.append(task)
        return task

    def remove_task(self, task_id: int) -> None:
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks(self, include_completed: bool = True) -> list[Task]:
        if include_completed:
            return list(self.tasks)
        return [t for t in self.tasks if not t.completed]

    def __repr__(self) -> str:
        return f"<Pet {self.name} ({self.species}), {len(self.tasks)} task(s)>"

    # -- persistence --------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "age": self.age,
            "weight": self.weight,
            "notes": self.notes,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @staticmethod
    def from_dict(data: dict) -> "Pet":
        pet = Pet(
            name=data["name"],
            species=data["species"],
            breed=data.get("breed", ""),
            age=data.get("age"),
            weight=data.get("weight"),
            notes=data.get("notes", ""),
        )
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet


class Owner:
    """Manages multiple Pets and provides access to all their tasks."""

    def __init__(self, name: str):
        self.name = name
        self.pets: dict[str, Pet] = {}

    def add_pet(self, pet: Pet) -> None:
        if pet.name in self.pets:
            raise ValueError(f"Pet named {pet.name!r} already exists")
        self.pets[pet.name] = pet

    def remove_pet(self, name: str) -> None:
        del self.pets[name]

    def get_pet(self, name: str) -> Pet:
        return self.pets[name]

    def list_pets(self) -> list[Pet]:
        return list(self.pets.values())

    def get_all_tasks(self) -> list[Task]:
        """Flatten every pet's task list into one collection.

        This is the single aggregation point for the whole household: the
        Scheduler calls this instead of reading any one Pet's task list, so
        it always sees every pet's tasks and stays correct as pets/tasks are
        added or removed.
        """
        all_tasks: list[Task] = []
        for pet in self.pets.values():
            all_tasks.extend(pet.tasks)
        return all_tasks

    def __repr__(self) -> str:
        return f"<Owner {self.name}, {len(self.pets)} pet(s)>"

    # -- persistence --------------------------------------------------------

    def save(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {"name": self.name, "pets": [p.to_dict() for p in self.pets.values()]}
        target.write_text(json.dumps(payload, indent=2))

    @staticmethod
    def load(path: str) -> "Owner":
        payload = json.loads(Path(path).read_text())
        owner = Owner(payload["name"])
        for pet_data in payload["pets"]:
            owner.add_pet(Pet.from_dict(pet_data))
        return owner


class Scheduler:
    """The "brain": retrieves, organizes, and manages tasks across all pets.

    It never stores its own copy of tasks and never reaches into a single
    Pet directly. Every query goes through owner.get_all_tasks(), so the
    Scheduler automatically reflects whichever pets/tasks the Owner
    currently holds -- add a pet, or a task, or complete one, and the very
    next query already accounts for it.
    """

    def __init__(self, owner: Owner):
        self.owner = owner

    def _pending(self, pet_name: Optional[str] = None) -> list[Task]:
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet.name == pet_name]
        return [t for t in tasks if not t.completed]

    def get_upcoming_tasks(self, limit: Optional[int] = None, pet_name: Optional[str] = None, now=None) -> list[Task]:
        """Pending tasks ranked highest-priority first (heap-based top-k selection)."""
        now = now or datetime.now()
        pending = self._pending(pet_name)
        n = limit if limit is not None else len(pending)
        return nsmallest(n, pending, key=lambda t: t.priority_key(now))

    def get_overdue_tasks(self, pet_name: Optional[str] = None, now=None) -> list[Task]:
        now = now or datetime.now()
        pending = self._pending(pet_name)
        late = [t for t in pending if t.is_overdue(now)]
        return sorted(late, key=lambda t: t.scheduled_time)

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        for task in self.owner.get_all_tasks():
            if task.task_id == task_id:
                return task
        return None

    def complete_task(self, task_id: int) -> Optional[Task]:
        """Marks a task done and, if recurring, schedules its next occurrence."""
        task = self.get_task_by_id(task_id)
        if task is None:
            raise KeyError(f"No task with id {task_id}")
        task.mark_complete()
        nxt = task.next_occurrence()
        if nxt is not None:
            task.pet.add_task(nxt)
        return nxt

    def get_schedule_by_pet(self, now=None) -> dict[str, list[Task]]:
        """Every pet's upcoming tasks, ranked, grouped by pet name."""
        now = now or datetime.now()
        return {
            pet.name: self.get_upcoming_tasks(pet_name=pet.name, now=now)
            for pet in self.owner.list_pets()
        }
