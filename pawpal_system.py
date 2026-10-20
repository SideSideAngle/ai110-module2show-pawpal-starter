from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import uuid4

# All times are stored as minutes from midnight (e.g. 8:30 AM = 510).

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")


def format_time(minutes: int) -> str:
    """Turn minutes from midnight into 'HH:MM'."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    preferred_time: Optional[int] = None  # minutes from midnight
    frequency: str = "once"  # "once" | "daily" | "weekly"
    completed: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        """Validate the task as soon as it is created."""
        self.validate()

    def validate(self) -> None:
        """Raise ValueError if duration, priority, frequency or preferred time is invalid."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.priority not in PRIORITY_SCORES:
            raise ValueError(f"priority must be one of {list(PRIORITY_SCORES)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")
        if self.preferred_time is not None and not 0 <= self.preferred_time < 24 * 60:
            raise ValueError("preferred_time must be minutes from midnight (0-1439)")

    def mark_complete(self) -> None:
        """Mark the task as done."""
        self.completed = True

    def reset(self) -> None:
        """Mark the task as not done, e.g. when a daily/weekly task comes around again."""
        self.completed = False

    def priority_score(self) -> int:
        """Return the numeric priority (low=1, medium=2, high=3) used for sorting."""
        return PRIORITY_SCORES[self.priority]


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet, rejecting a duplicate task id."""
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"{self.name} already has a task with id {task.id}")
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id, or raise ValueError if it isn't found."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[i]
                return
        raise ValueError(f"{self.name} has no task with id {task_id}")

    def get_task(self, task_id: str) -> Task:
        """Return the task with the given id, or raise ValueError if it isn't found."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise ValueError(f"{self.name} has no task with id {task_id}")

    def get_pending_tasks(self) -> list[Task]:
        """Return the tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class ScheduledItem:
    task: Task
    pet: Pet
    start_time: int  # minutes from midnight
    reason: str = ""

    @property
    def end_time(self) -> int:
        """Minutes from midnight when the task finishes (start time plus duration)."""
        return self.start_time + self.task.duration_minutes


@dataclass
class Schedule:
    """The 'brain': pulls every pet's tasks from the Owner and arranges them into a day."""

    day: date = field(default_factory=date.today)
    items: list[ScheduledItem] = field(default_factory=list)
    unscheduled: list[tuple[Pet, Task]] = field(default_factory=list)
    total_minutes: int = 0

    def build(self, owner: Owner) -> None:
        """Rebuild the schedule from all of the owner's pets' pending tasks.

        Highest priority goes first; ties are broken by earlier preferred time
        (tasks with no preference last), then shorter duration. A task is
        skipped if it would exceed the owner's available minutes or can't fit
        in the day window.
        """
        self.items.clear()
        self.unscheduled.clear()
        self.total_minutes = 0

        candidates = owner.get_all_tasks()
        candidates.sort(
            key=lambda pt: (
                -pt[1].priority_score(),
                pt[1].preferred_time is None,
                pt[1].preferred_time or 0,
                pt[1].duration_minutes,
            )
        )

        for pet, task in candidates:
            if self.total_minutes + task.duration_minutes > owner.available_minutes:
                self.unscheduled.append((pet, task))
                continue
            start, reason = self._place(task, owner)
            if start is None:
                self.unscheduled.append((pet, task))
                continue
            self.add_item(pet, task, start, reason)

    def add_item(self, pet: Pet, task: Task, start_time: int, reason: str) -> None:
        """Add a task to the plan at the given start time and keep items sorted by time."""
        self.items.append(ScheduledItem(task, pet, start_time, reason))
        self.items.sort(key=lambda item: item.start_time)
        self.total_minutes += task.duration_minutes

    def explain(self) -> str:
        """Return a readable plan listing each task's time and reason, plus tasks that didn't fit."""
        if not self.items and not self.unscheduled:
            return "Nothing to schedule."
        lines = [f"Plan for {self.day.isoformat()} ({self.total_minutes} min scheduled):"]
        for item in self.items:
            lines.append(
                f"  {format_time(item.start_time)}-{format_time(item.end_time)}  "
                f"{item.pet.name}: {item.task.title} [{item.task.priority}] - {item.reason}"
            )
        if self.unscheduled:
            lines.append("Could not fit:")
            for pet, task in self.unscheduled:
                lines.append(
                    f"  {pet.name}: {task.title} [{task.priority}, {task.duration_minutes} min]"
                )
        return "\n".join(lines)

    def _first_free(self, duration: int, earliest: int, latest_end: int) -> Optional[int]:
        """Earliest start >= `earliest` where `duration` minutes are free before `latest_end`."""
        start = earliest
        for item in self.items:  # kept sorted by start_time
            if item.end_time <= start:
                continue
            if item.start_time >= start + duration:
                break
            start = item.end_time
        return start if start + duration <= latest_end else None

    def _place(self, task: Task, owner: Owner) -> tuple[Optional[int], str]:
        """Pick a start time for `task`, preferring its preferred_time if that slot is open."""
        duration = task.duration_minutes
        if task.preferred_time is not None and task.preferred_time >= owner.day_start:
            if self._first_free(duration, task.preferred_time, owner.day_end) == task.preferred_time:
                return task.preferred_time, "scheduled at its preferred time"
            start = self._first_free(duration, owner.day_start, owner.day_end)
            if start is not None:
                return start, "preferred time was taken, moved to the earliest free slot"
            return None, ""
        start = self._first_free(duration, owner.day_start, owner.day_end)
        return start, "earliest free slot by priority"


@dataclass
class Owner:
    name: str
    available_minutes: int = 480
    day_start: int = 8 * 60  # minutes from midnight
    day_end: int = 20 * 60  # minutes from midnight
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet, rejecting one whose name is already taken."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"A pet named {pet.name} already exists")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove the pet with the given name, or raise ValueError if there isn't one."""
        pet = self._get_pet(pet_name)
        self.pets.remove(pet)

    def add_task(self, pet_name: str, task: Task) -> None:
        """Add a task to the named pet."""
        self._get_pet(pet_name).add_task(task)

    def edit_task(self, pet_name: str, task_id: str, **changes) -> None:
        """Update fields on a pet's task, rolling back if the new values are invalid."""
        task = self._get_pet(pet_name).get_task(task_id)
        editable = {"title", "duration_minutes", "priority", "preferred_time", "frequency", "completed"}
        unknown = set(changes) - editable
        if unknown:
            raise ValueError(f"Cannot edit field(s): {sorted(unknown)}")
        old = {key: getattr(task, key) for key in changes}
        for key, value in changes.items():
            setattr(task, key, value)
        try:
            task.validate()
        except ValueError:
            for key, value in old.items():  # roll back on invalid input
                setattr(task, key, value)
            raise

    def remove_task(self, pet_name: str, task_id: str) -> None:
        """Remove a task from the named pet."""
        self._get_pet(pet_name).remove_task(task_id)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Every pending task across all pets, paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.get_pending_tasks()]

    def generate_schedule(self) -> Schedule:
        """Build and return a Schedule covering all of this owner's pets."""
        schedule = Schedule()
        schedule.build(self)
        return schedule

    def _get_pet(self, pet_name: str) -> Pet:
        """Return the pet with the given name, or raise ValueError if there isn't one."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        raise ValueError(f"No pet named {pet_name}")
