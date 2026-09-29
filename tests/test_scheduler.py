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


def test_filter_tasks_with_no_args_returns_everything(owner, now):
    rex_task = owner.get_pet("Rex").add_task(Task("Feed Rex", now, category="feeding"))
    milo_task = owner.get_pet("Milo").add_task(Task("Feed Milo", now, category="feeding"))
    scheduler = Scheduler(owner)

    assert scheduler.filter_tasks() == [rex_task, milo_task]


def test_filter_tasks_by_pet_name(owner, now):
    rex_task = owner.get_pet("Rex").add_task(Task("Feed Rex", now, category="feeding"))
    owner.get_pet("Milo").add_task(Task("Feed Milo", now, category="feeding"))
    scheduler = Scheduler(owner)

    assert scheduler.filter_tasks(pet_name="Rex") == [rex_task]


def test_filter_tasks_by_completion_status(owner, now):
    rex = owner.get_pet("Rex")
    done = rex.add_task(Task("Done", now, category="feeding"))
    done.mark_complete()
    pending = rex.add_task(Task("Pending", now, category="feeding"))
    scheduler = Scheduler(owner)

    assert scheduler.filter_tasks(completed=True) == [done]
    assert scheduler.filter_tasks(completed=False) == [pending]


def test_filter_tasks_combines_pet_name_and_completion_status(owner, now):
    rex = owner.get_pet("Rex")
    milo = owner.get_pet("Milo")
    rex_done = rex.add_task(Task("Rex done", now, category="feeding"))
    rex_done.mark_complete()
    rex.add_task(Task("Rex pending", now, category="feeding"))
    milo_done = milo.add_task(Task("Milo done", now, category="feeding"))
    milo_done.mark_complete()
    scheduler = Scheduler(owner)

    assert scheduler.filter_tasks(pet_name="Milo", completed=True) == [milo_done]


def test_sort_by_time_ignores_category_and_overdue_status(owner, now):
    rex = owner.get_pet("Rex")
    earliest = rex.add_task(Task("Walk", now + timedelta(hours=1), category="walk"))
    middle = rex.add_task(Task("Late pill", now - timedelta(hours=1), category="medication"))
    latest = rex.add_task(Task("Feed", now + timedelta(hours=5), category="feeding"))
    scheduler = Scheduler(owner)

    assert scheduler.sort_by_time() == [middle, earliest, latest]


def test_sort_by_time_excludes_completed_and_can_filter_by_pet(owner, now):
    rex = owner.get_pet("Rex")
    milo = owner.get_pet("Milo")
    done = rex.add_task(Task("Done", now, category="feeding"))
    done.mark_complete()
    rex_task = rex.add_task(Task("Rex task", now + timedelta(hours=1), category="feeding"))
    milo.add_task(Task("Milo task", now + timedelta(hours=2), category="feeding"))
    scheduler = Scheduler(owner)

    assert scheduler.sort_by_time(pet_name="Rex") == [rex_task]


def test_find_conflicts_returns_empty_list_when_no_clashes(owner, now):
    owner.get_pet("Rex").add_task(Task("Feed", now, category="feeding"))
    owner.get_pet("Milo").add_task(Task("Feed", now + timedelta(hours=1), category="feeding"))
    scheduler = Scheduler(owner)

    assert scheduler.find_conflicts() == []


def test_find_conflicts_detects_same_time_across_different_pets(owner, now):
    rex = owner.get_pet("Rex")
    milo = owner.get_pet("Milo")
    rex.add_task(Task("Breakfast", now, category="feeding"))
    milo.add_task(Task("Vet checkup", now, category="appointment"))
    scheduler = Scheduler(owner)

    warnings = scheduler.find_conflicts()

    assert len(warnings) == 1
    assert "Rex" in warnings[0]
    assert "Milo" in warnings[0]


def test_find_conflicts_detects_same_pet_double_booking(owner, now):
    rex = owner.get_pet("Rex")
    rex.add_task(Task("Walk", now, category="walk"))
    rex.add_task(Task("Pill", now, category="medication"))
    scheduler = Scheduler(owner)

    warnings = scheduler.find_conflicts()

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Pill" in warnings[0]


def test_find_conflicts_ignores_completed_tasks(owner, now):
    rex = owner.get_pet("Rex")
    milo = owner.get_pet("Milo")
    done = rex.add_task(Task("Old", now, category="feeding"))
    done.mark_complete()
    milo.add_task(Task("New", now, category="feeding"))
    scheduler = Scheduler(owner)

    assert scheduler.find_conflicts() == []


def test_find_conflicts_can_be_scoped_to_one_pet(owner, now):
    rex = owner.get_pet("Rex")
    milo = owner.get_pet("Milo")
    rex.add_task(Task("Breakfast", now, category="feeding"))
    milo.add_task(Task("Vet checkup", now, category="appointment"))
    scheduler = Scheduler(owner)

    assert scheduler.find_conflicts(pet_name="Rex") == []


def test_find_next_available_slot_returns_after_when_free(owner, now):
    scheduler = Scheduler(owner)
    assert scheduler.find_next_available_slot(after=now) == now


def test_find_next_available_slot_skips_occupied_times(owner, now):
    rex = owner.get_pet("Rex")
    rex.add_task(Task("Feed", now, category="feeding"))
    rex.add_task(Task("Walk", now + timedelta(minutes=30), category="walk"))
    scheduler = Scheduler(owner)

    slot = scheduler.find_next_available_slot(after=now, step=timedelta(minutes=30))

    assert slot == now + timedelta(hours=1)


def test_find_next_available_slot_ignores_completed_tasks(owner, now):
    rex = owner.get_pet("Rex")
    done = rex.add_task(Task("Feed", now, category="feeding"))
    done.mark_complete()
    scheduler = Scheduler(owner)

    assert scheduler.find_next_available_slot(after=now) == now


def test_find_next_available_slot_can_be_scoped_to_one_pet(owner, now):
    rex = owner.get_pet("Rex")
    milo = owner.get_pet("Milo")
    rex.add_task(Task("Feed Rex", now, category="feeding"))
    scheduler = Scheduler(owner)

    # Rex is busy at `now`, but Milo has nothing booked, so Milo's own
    # search should return `now` itself rather than skipping ahead.
    assert scheduler.find_next_available_slot(pet_name="Milo", after=now) == now
    assert scheduler.find_next_available_slot(pet_name="Rex", after=now) != now


def test_find_next_available_slot_returns_none_when_window_is_fully_booked(owner, now):
    rex = owner.get_pet("Rex")
    step = timedelta(minutes=30)
    window = timedelta(hours=1)
    t = now
    while t <= now + window:
        rex.add_task(Task("Busy", t, category="feeding"))
        t += step
    scheduler = Scheduler(owner)

    assert scheduler.find_next_available_slot(after=now, step=step, search_window=window) is None


def test_find_next_available_slot_rejects_non_positive_step(owner):
    scheduler = Scheduler(owner)

    with pytest.raises(ValueError, match="step must be positive"):
        scheduler.find_next_available_slot(step=timedelta(0))

    with pytest.raises(ValueError, match="step must be positive"):
        scheduler.find_next_available_slot(step=-timedelta(minutes=30))


def test_find_next_available_slot_rejects_negative_search_window(owner):
    scheduler = Scheduler(owner)

    with pytest.raises(ValueError, match="search_window cannot be negative"):
        scheduler.find_next_available_slot(search_window=-timedelta(minutes=1))


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


def test_complete_task_raises_if_already_completed_and_does_not_double_recur(owner, now):
    rex = owner.get_pet("Rex")
    task = rex.add_task(Task("Feed", now, frequency="daily", category="feeding"))
    scheduler = Scheduler(owner)

    scheduler.complete_task(task.task_id)
    with pytest.raises(ValueError):
        scheduler.complete_task(task.task_id)

    # Only one recurring occurrence should exist, not two.
    assert len(rex.tasks) == 2


def test_get_schedule_by_pet_groups_tasks_under_each_pet_name(owner, now):
    owner.get_pet("Rex").add_task(Task("Feed Rex", now, category="feeding"))
    owner.get_pet("Milo").add_task(Task("Feed Milo", now, category="feeding"))
    scheduler = Scheduler(owner)

    schedule = scheduler.get_schedule_by_pet(now=now)

    assert set(schedule.keys()) == {"Rex", "Milo"}
    assert schedule["Rex"][0].pet.name == "Rex"
    assert schedule["Milo"][0].pet.name == "Milo"
