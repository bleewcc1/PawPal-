from pawpal_system import Pet, Task


def test_add_task_sets_back_reference(now):
    pet = Pet("Rex", "Dog")
    task = Task("Feed", now)
    pet.add_task(task)
    assert task.pet is pet
    assert task in pet.tasks


def test_add_task_increases_pet_task_count(now):
    pet = Pet("Rex", "Dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feed", now))
    assert len(pet.tasks) == 1

    pet.add_task(Task("Walk", now))
    assert len(pet.tasks) == 2


def test_remove_task_drops_only_matching_id(now):
    pet = Pet("Rex", "Dog")
    keep = pet.add_task(Task("Feed", now))
    drop = pet.add_task(Task("Walk", now))
    pet.remove_task(drop.task_id)
    assert pet.tasks == [keep]


def test_get_tasks_can_exclude_completed(now):
    pet = Pet("Rex", "Dog")
    pending = pet.add_task(Task("Feed", now))
    done = pet.add_task(Task("Walk", now))
    done.mark_complete()

    assert pet.get_tasks(include_completed=True) == [pending, done]
    assert pet.get_tasks(include_completed=False) == [pending]


def test_to_dict_and_from_dict_round_trip_preserves_tasks(now):
    pet = Pet("Rex", "Dog", breed="Labrador", age=4)
    pet.add_task(Task("Feed", now, frequency="daily", category="feeding"))

    restored = Pet.from_dict(pet.to_dict())

    assert restored.name == pet.name
    assert restored.breed == pet.breed
    assert len(restored.tasks) == 1
    assert restored.tasks[0].description == "Feed"
    assert restored.tasks[0].pet is restored
