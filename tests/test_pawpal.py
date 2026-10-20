import pytest
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


def test_exact_duplicate_times_are_flagged_for_same_pet():
    mochi = Pet(name="Mochi", species="dog")
    schedule = _plan((mochi, "Walk", 480, 30), (mochi, "Feed", 480, 30))

    warnings = schedule.find_conflicts()

    assert len(warnings) == 1
    assert "Same-pet conflict" in warnings[0]
    assert "08:00-08:30" in warnings[0]


def test_planner_moves_a_duplicate_preferred_time_instead_of_double_booking():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_task("Mochi", Task(title="Walk", duration_minutes=30, preferred_time=480, priority="high"))
    owner.add_task("Mochi", Task(title="Feed", duration_minutes=30, preferred_time=480, priority="low"))

    schedule = owner.generate_schedule()

    starts = sorted(item.start_time for item in schedule.items)
    assert starts == [480, 510]
    assert any("moved to the earliest free slot" in item.reason for item in schedule.items)


def test_sort_by_time_returns_chronological_order():
    tasks = [
        Task(title="Evening", duration_minutes=10, preferred_time=18 * 60),
        Task(title="Morning", duration_minutes=10, preferred_time=8 * 60),
        Task(title="Noon", duration_minutes=10, preferred_time=12 * 60),
    ]

    ordered = Schedule.sort_by_time(tasks)

    assert [t.title for t in ordered] == ["Morning", "Noon", "Evening"]
    assert [t.title for t in tasks] == ["Evening", "Morning", "Noon"]  # input untouched


def test_sort_by_time_puts_unset_last_and_keeps_ties_in_order():
    tasks = [
        Task(title="Anytime", duration_minutes=10),
        Task(title="Second", duration_minutes=10, preferred_time=600),
        Task(title="First", duration_minutes=10, preferred_time=600),
        Task(title="Midnight", duration_minutes=10, preferred_time=0),
    ]

    ordered = Schedule.sort_by_time(tasks)

    assert [t.title for t in ordered] == ["Midnight", "Second", "First", "Anytime"]


def test_generated_schedule_items_are_in_chronological_order():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_task("Mochi", Task(title="Late", duration_minutes=30, preferred_time=17 * 60, priority="high"))
    owner.add_task("Mochi", Task(title="Early", duration_minutes=30, preferred_time=9 * 60, priority="low"))
    owner.add_task("Mochi", Task(title="Any", duration_minutes=30, priority="medium"))

    starts = [item.start_time for item in owner.generate_schedule().items]

    assert starts == sorted(starts)


def test_completing_daily_task_via_owner_schedules_it_for_tomorrow():
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    today = date(2026, 1, 1)
    task = Task(
        title="Walk", duration_minutes=30, priority="high", preferred_time=480,
        frequency="daily", due_date=today,
    )
    owner.add_task("Mochi", task)

    following = owner.complete_task("Mochi", task.id)

    assert following.due_date == date(2026, 1, 2)
    assert (following.title, following.duration_minutes, following.priority, following.preferred_time) == (
        "Walk", 30, "high", 480,
    )
    assert [t.id for t in pet.get_pending_tasks()] == [following.id]

    today_plan, tomorrow_plan = Schedule(day=today), Schedule(day=date(2026, 1, 2))
    today_plan.build(owner)
    tomorrow_plan.build(owner)
    assert today_plan.items == []
    assert [i.task.id for i in tomorrow_plan.items] == [following.id]


def test_generated_schedule_has_no_conflicts():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    for title in ("A", "B", "C"):
        owner.add_task("Mochi", Task(title=title, duration_minutes=30, preferred_time=480))

    assert owner.generate_schedule().find_conflicts() == []


# --- Empty and boundary states ------------------------------------------------


def test_pet_with_no_tasks_produces_an_empty_plan():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))

    schedule = owner.generate_schedule()

    assert schedule.items == [] and schedule.unscheduled == []
    assert schedule.explain() == "Nothing to schedule."


def test_completed_tasks_are_left_out_of_the_plan():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    task = Task(title="Vet visit", duration_minutes=60)
    owner.add_task("Mochi", task)
    owner.complete_task("Mochi", task.id)

    assert owner.generate_schedule().items == []


def test_smaller_task_still_fits_after_a_larger_one_is_skipped():
    owner = Owner(name="Jordan", available_minutes=30)
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_task("Mochi", Task(title="A", duration_minutes=25, priority="high"))
    owner.add_task("Mochi", Task(title="B", duration_minutes=20, priority="medium"))
    owner.add_task("Mochi", Task(title="C", duration_minutes=5, priority="low"))

    schedule = owner.generate_schedule()

    assert sorted(i.task.title for i in schedule.items) == ["A", "C"]
    assert [t.title for _, t in schedule.unscheduled] == ["B"]


def test_task_that_does_not_fit_the_day_window_is_unscheduled():
    owner = Owner(name="Jordan", day_start=480, day_end=510)
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_task("Mochi", Task(title="Groom", duration_minutes=60))

    schedule = owner.generate_schedule()

    assert schedule.items == [] and len(schedule.unscheduled) == 1


def test_preferred_time_before_day_start_falls_back_to_day_start():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_task("Mochi", Task(title="Early walk", duration_minutes=30, preferred_time=6 * 60))

    assert owner.generate_schedule().items[0].start_time == owner.day_start


def test_preferred_time_that_would_run_past_day_end_is_moved():
    owner = Owner(name="Jordan")  # window is 08:00-20:00
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_task("Mochi", Task(title="Late walk", duration_minutes=30, preferred_time=19 * 60 + 50))

    item = owner.generate_schedule().items[0]

    assert item.start_time == owner.day_start
    assert item.end_time <= owner.day_end


# --- Validation ---------------------------------------------------------------


def test_task_rejects_invalid_values():
    for bad in (
        {"duration_minutes": 0},
        {"duration_minutes": -5},
        {"priority": "urgent"},
        {"frequency": "monthly"},
        {"preferred_time": -1},
        {"preferred_time": 24 * 60},
    ):
        kwargs = {"title": "X", "duration_minutes": 10, **bad}
        with pytest.raises(ValueError):
            Task(**kwargs)


def test_task_accepts_the_first_and_last_minute_of_the_day():
    assert Task(title="X", duration_minutes=1, preferred_time=0).preferred_time == 0
    assert Task(title="X", duration_minutes=1, preferred_time=1439).preferred_time == 1439


def test_duplicate_pet_name_is_rejected():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))

    with pytest.raises(ValueError):
        owner.add_pet(Pet(name="Mochi", species="cat"))


def test_edit_task_rolls_back_invalid_changes():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    task = Task(title="Walk", duration_minutes=30)
    owner.add_task("Mochi", task)

    with pytest.raises(ValueError):
        owner.edit_task("Mochi", task.id, duration_minutes=-5, title="Renamed")
    with pytest.raises(ValueError):
        owner.edit_task("Mochi", task.id, due_date=date(2030, 1, 1))

    assert task.duration_minutes == 30 and task.title == "Walk"


# --- Filtering ----------------------------------------------------------------


def _owner_with_done_and_pending():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))
    owner.add_pet(Pet(name="Pixel", species="cat"))
    done = Task(title="Done", duration_minutes=10)
    owner.add_task("Mochi", done)
    owner.add_task("Mochi", Task(title="Pending", duration_minutes=10))
    owner.add_task("Pixel", Task(title="Cat pending", duration_minutes=10))
    owner.complete_task("Mochi", done.id)
    return owner


def test_filter_tasks_by_status_and_pet():
    owner = _owner_with_done_and_pending()

    titles = lambda rows: sorted(t.title for _, t in rows)
    assert titles(owner.filter_tasks(status="done")) == ["Done"]
    assert titles(owner.filter_tasks(status="pending")) == ["Cat pending", "Pending"]
    assert titles(owner.filter_tasks()) == ["Cat pending", "Done", "Pending"]
    assert titles(owner.filter_tasks(pet_name="Pixel")) == ["Cat pending"]
    assert titles(owner.filter_tasks(pet_name="Mochi", status="pending")) == ["Pending"]


def test_filter_tasks_rejects_unknown_pet_or_status():
    owner = _owner_with_done_and_pending()

    with pytest.raises(ValueError):
        owner.filter_tasks(pet_name="Ghost")
    with pytest.raises(ValueError):
        owner.filter_tasks(status="someday")


def test_explain_includes_conflict_warnings():
    mochi = Pet(name="Mochi", species="dog")
    schedule = _plan((mochi, "Walk", 480, 30), (mochi, "Feed", 490, 10))

    assert "Warnings:" in schedule.explain()
