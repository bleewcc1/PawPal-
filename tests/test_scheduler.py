from datetime import timedelta

import pytest

from pawpal_system import Scheduler, Task


def test_get_upcoming_tasks_ranks_overdue_first(owner, now):
    rex = owner.get_pet("Rex")
    milo = owner.get_pet("Milo")
    overdue_feeding = rex.add_task(Task("Late breakfast", now - timedelta(hours=1), category="feeding"))
    upcoming_med = milo.add_task(Task("Pill", now + timedelta(hours=1), category="medication"))
    scheduler = Scheduler(owner)

    ranked = scheduler.get_upcoming_tasks(now=now)

    assert ranked[0] is overdue_feeding
    assert ranked[1] is upcoming_med


def test_get_upcoming_tasks_ranks_by_category_urgency_when_none_overdue(owner, now):
    rex = owner.get_pet("Rex")
    walk = rex.add_task(Task("Walk", now + timedelta(hours=1), category="walk"))
    medication = rex.add_task(Task("Pill", now + timedelta(hours=5), category="medication"))
    scheduler = Scheduler(owner)

    ranked = scheduler.get_upcoming_tasks(now=now)

    assert ranked == [medication, walk]


def test_get_upcoming_tasks_excludes_completed(owner, now):
    rex = owner.get_pet("Rex")
    done = rex.add_task(Task("Feed", now, category="feeding"))
    done.mark_complete()
    scheduler = Scheduler(owner)

    assert scheduler.get_upcoming_tasks(now=now) == []


def test_get_upcoming_tasks_can_filter_by_pet(owner, now):
    owner.get_pet("Rex").add_task(Task("Feed Rex", now, category="feeding"))
    owner.get_pet("Milo").add_task(Task("Feed Milo", now, category="feeding"))
    scheduler = Scheduler(owner)

    ranked = scheduler.get_upcoming_tasks(pet_name="Milo", now=now)

    assert len(ranked) == 1
    assert ranked[0].pet.name == "Milo"


def test_get_overdue_tasks_only_returns_late_pending_tasks(owner, now):
    rex = owner.get_pet("Rex")
    late = rex.add_task(Task("Late", now - timedelta(hours=1), category="feeding"))
    rex.add_task(Task("Future", now + timedelta(hours=1), category="feeding"))
    scheduler = Scheduler(owner)

    assert scheduler.get_overdue_tasks(now=now) == [late]


def test_complete_task_marks_done_and_reschedules_recurring_task(owner, now):
    rex = owner.get_pet("Rex")
    task = rex.add_task(Task("Breakfast", now, frequency="daily", category="feeding"))
    scheduler = Scheduler(owner)

    nxt = scheduler.complete_task(task.task_id)

    assert task.completed is True
    assert nxt is not None
    assert nxt.scheduled_time == now + timedelta(days=1)
    assert nxt.pet is rex
    assert nxt in rex.tasks


def test_complete_task_does_not_reschedule_one_off_task(owner, now):
    rex = owner.get_pet("Rex")
    task = rex.add_task(Task("Vet visit", now, frequency="once", category="appointment"))
    scheduler = Scheduler(owner)

    nxt = scheduler.complete_task(task.task_id)

    assert nxt is None
    assert len(rex.tasks) == 1


def test_complete_task_raises_for_unknown_id(owner):
    scheduler = Scheduler(owner)
    with pytest.raises(KeyError):
        scheduler.complete_task(9999)


def test_get_schedule_by_pet_groups_tasks_under_each_pet_name(owner, now):
    owner.get_pet("Rex").add_task(Task("Feed Rex", now, category="feeding"))
    owner.get_pet("Milo").add_task(Task("Feed Milo", now, category="feeding"))
    scheduler = Scheduler(owner)

    schedule = scheduler.get_schedule_by_pet(now=now)

    assert set(schedule.keys()) == {"Rex", "Milo"}
    assert schedule["Rex"][0].pet.name == "Rex"
    assert schedule["Milo"][0].pet.name == "Milo"
