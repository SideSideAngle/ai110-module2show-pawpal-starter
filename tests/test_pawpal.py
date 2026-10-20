from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=30)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Morning walk", duration_minutes=30))

    assert len(pet.tasks) == 1
