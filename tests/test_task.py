from datetime import timedelta

from pawpal_system import Task


def test_mark_complete_flips_flag(now):
    task = Task("Feed", now)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_is_overdue_true_when_scheduled_time_in_past(now):
    task = Task("Feed", now - timedelta(hours=1))
    assert task.is_overdue(now) is True


def test_is_overdue_false_when_scheduled_time_in_future(now):
    task = Task("Feed", now + timedelta(hours=1))
    assert task.is_overdue(now) is False


def test_completed_task_is_never_overdue(now):
    task = Task("Feed", now - timedelta(hours=1))
    task.mark_complete()
    assert task.is_overdue(now) is False


def test_next_occurrence_none_for_one_off_task(now):
    task = Task("Vet visit", now, frequency="once")
    assert task.next_occurrence() is None


def test_next_occurrence_advances_by_frequency_interval(now):
    task = Task("Breakfast", now, frequency="daily")
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.scheduled_time == now + timedelta(days=1)
    assert nxt.completed is False
    assert nxt.description == task.description
    assert nxt.category == task.category


def test_priority_key_ranks_overdue_before_upcoming(now):
    overdue = Task("Feed", now - timedelta(hours=1), category="walk")
    upcoming = Task("Pill", now + timedelta(hours=1), category="medication")
    assert overdue.priority_key(now) < upcoming.priority_key(now)


def test_priority_key_ranks_medication_before_walk_when_both_upcoming(now):
    medication = Task("Pill", now + timedelta(hours=5), category="medication")
    walk = Task("Walk", now + timedelta(hours=1), category="walk")
    # Category urgency outranks a later-but-still-upcoming walk.
    assert medication.priority_key(now) < walk.priority_key(now)


def test_priority_key_breaks_ties_by_soonest_time(now):
    sooner = Task("Pill A", now + timedelta(hours=1), category="medication")
    later = Task("Pill B", now + timedelta(hours=2), category="medication")
    assert sooner.priority_key(now) < later.priority_key(now)
