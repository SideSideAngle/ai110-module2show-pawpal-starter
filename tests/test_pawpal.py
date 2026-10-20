from datetime import date

from pawpal_system import Owner, Pet, Schedule, Task


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


def test_completing_daily_task_creates_next_day_instance():
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Walk", duration_minutes=30, frequency="daily", due_date=date(2026, 1, 1))
    pet.add_task(task)

    following = pet.complete_task(task.id)

    assert task.completed is True
    assert following is not None and following is not task
    assert following.completed is False
    assert following.due_date == date(2026, 1, 2)
    assert following.id != task.id
    assert following in pet.tasks


def test_completing_weekly_task_creates_instance_seven_days_later():
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Bath", duration_minutes=20, frequency="weekly", due_date=date(2026, 1, 1))
    pet.add_task(task)

    following = pet.complete_task(task.id)

    assert following.due_date == date(2026, 1, 8)


def test_completing_once_task_creates_nothing():
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Vet visit", duration_minutes=60)
    pet.add_task(task)

    assert pet.complete_task(task.id) is None
    assert len(pet.tasks) == 1


def test_completing_twice_does_not_duplicate():
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Walk", duration_minutes=30, frequency="daily")
    pet.add_task(task)

    pet.complete_task(task.id)
    assert pet.complete_task(task.id) is None
    assert len(pet.tasks) == 2


def test_future_occurrence_is_not_in_todays_schedule():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    task = Task(title="Walk", duration_minutes=30, frequency="daily")
    owner.add_task("Mochi", task)

    owner.complete_task("Mochi", task.id)
    schedule = owner.generate_schedule()

    assert schedule.items == []
    assert schedule.unscheduled == []


def _plan(*entries):
    """Build a Schedule from (pet, title, start, minutes) tuples, bypassing the planner."""
    schedule = Schedule()
    for pet, title, start, minutes in entries:
        schedule.add_item(pet, Task(title=title, duration_minutes=minutes), start, "manual")
    return schedule


def test_same_pet_overlap_is_reported():
    mochi = Pet(name="Mochi", species="dog")
    schedule = _plan((mochi, "Walk", 480, 30), (mochi, "Feed", 495, 10))

    warnings = schedule.find_conflicts()

    assert len(warnings) == 1
    assert "Same-pet conflict" in warnings[0]
    assert "Walk" in warnings[0] and "Feed" in warnings[0]


def test_different_pet_overlap_is_reported():
    mochi, pixel = Pet(name="Mochi", species="dog"), Pet(name="Pixel", species="cat")
    schedule = _plan((mochi, "Walk", 480, 30), (pixel, "Breakfast", 480, 10))

    warnings = schedule.find_conflicts()

    assert len(warnings) == 1 and "between pets" in warnings[0]


def test_back_to_back_tasks_are_not_conflicts():
    mochi = Pet(name="Mochi", species="dog")
    assert _plan((mochi, "Walk", 480, 30), (mochi, "Feed", 510, 10)).find_conflicts() == []


def test_long_task_conflicts_with_every_overlapping_task():
    mochi = Pet(name="Mochi", species="dog")
    schedule = _plan((mochi, "Groom", 480, 120), (mochi, "A", 490, 5), (mochi, "B", 500, 5))

    # A and B don't overlap each other, but both overlap the long Groom task.
    assert len(schedule.find_conflicts()) == 2


def test_conflict_with_checks_before_adding_and_does_not_raise():
    mochi = Pet(name="Mochi", species="dog")
    schedule = _plan((mochi, "Walk", 480, 30))
    task = Task(title="Feed", duration_minutes=10)

    assert schedule.conflict_with(mochi, task, 490) is not None
    assert schedule.conflict_with(mochi, task, 510) is None
    assert len(schedule.items) == 1


def test_generated_schedule_has_no_conflicts():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    for title in ("A", "B", "C"):
        owner.add_task("Mochi", Task(title=title, duration_minutes=30, preferred_time=480))

    assert owner.generate_schedule().find_conflicts() == []
