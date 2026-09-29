import pytest

from pawpal_system import Owner, Pet, Task


def test_add_pet_rejects_duplicate_name(owner):
    with pytest.raises(ValueError):
        owner.add_pet(Pet("Rex", "Dog"))


def test_get_all_tasks_aggregates_across_every_pet(owner, now):
    rex = owner.get_pet("Rex")
    milo = owner.get_pet("Milo")
    rex.add_task(Task("Feed Rex", now))
    rex.add_task(Task("Walk Rex", now))
    milo.add_task(Task("Feed Milo", now))

    all_tasks = owner.get_all_tasks()

    assert len(all_tasks) == 3
    assert {t.pet.name for t in all_tasks} == {"Rex", "Milo"}


def test_get_all_tasks_reflects_new_pets_added_later(owner, now):
    assert owner.get_all_tasks() == []

    fido = Pet("Fido", "Dog")
    fido.add_task(Task("Feed Fido", now))
    owner.add_pet(fido)

    assert len(owner.get_all_tasks()) == 1


def test_remove_pet_drops_its_tasks_from_get_all_tasks(owner, now):
    owner.get_pet("Rex").add_task(Task("Feed Rex", now))
    owner.get_pet("Milo").add_task(Task("Feed Milo", now))

    owner.remove_pet("Rex")

    assert [t.pet.name for t in owner.get_all_tasks()] == ["Milo"]


def test_save_and_load_round_trip(owner, now, tmp_path):
    owner.get_pet("Rex").add_task(Task("Feed Rex", now, frequency="daily", category="feeding"))
    path = tmp_path / "pawpal.json"

    owner.save(str(path))
    restored = Owner.load(str(path))

    assert restored.name == owner.name
    assert {p.name for p in restored.list_pets()} == {"Rex", "Milo"}
    assert len(restored.get_all_tasks()) == 1
    assert restored.get_all_tasks()[0].description == "Feed Rex"
