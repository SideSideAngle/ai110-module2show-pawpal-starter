# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

- **Multi-pet care tracking:** one owner, any number of pets, each with its own tasks.
- **Task details:** duration, priority (low/medium/high), optional preferred time, and frequency (once/daily/weekly), validated when created.
- **Priority-based scheduling:** highest priority is placed first; ties go to the earlier preferred time, then the shorter task.
- **Preferred times honoured:** a task gets its preferred time if that slot is free. Otherwise it moves to the earliest free slot within the owner's day.
- **Time budget:** tasks that exceed the owner's available minutes or don't fit the day are listed as unscheduled instead of being dropped silently.
- **Sorting and filtering:** sort tasks by preferred time (tasks with none go last); filter by pet and by pending/done/all.
- **Conflict detection:** warns about overlapping tasks, labelled as same-pet or between pets, and checks a new task's time against the plan as it is added.
- **Recurring tasks:** completing a daily or weekly task creates the next occurrence, counted from its due date.
- **Explained plans:** every scheduled task carries a reason, and the plan can be printed as readable text.
- **Tests:** an automated pytest suite covers the scheduling behaviour.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

Running main.py:
==================================================
Today's Schedule for Jordan
==================================================
Plan for 2026-10-19 (100 min scheduled):
  08:00-08:10  Pixel: Breakfast [high] - scheduled at its preferred time
  08:10-08:40  Mochi: Morning walk [high] - preferred time was taken, moved to the earliest free slot
  08:40-09:05  Pixel: Play time [medium] - earliest free slot by priority
  12:00-12:15  Pixel: Brush fur [low] - scheduled at its preferred time
  17:30-17:50  Mochi: Training session [medium] - scheduled at its preferred time

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

def sort_by_time(tasks: list[Task]) -> list[Task]:
        """Return a new list of tasks ordered by preferred time, earliest first.

        Tasks with no preferred time go last. The input list is not modified, and
        tasks with equal times keep their original relative order.
        """
        return sorted(tasks, key=time_sort_key)

def filter_tasks(
        self, pet_name: Optional[str] = None, status: str = "all"
    ) -> list[tuple[Pet, Task]]:
        """Tasks paired with their pet, optionally limited to one pet and/or a status.

        `status` is "pending", "done" or "all". Raises ValueError for an unknown
        status or pet name.
        """
        if status not in ("pending", "done", "all"):
            raise ValueError("status must be one of ['pending', 'done', 'all']")
        pets = [self._get_pet(pet_name)] if pet_name is not None else self.pets
        return [
            (pet, task)
            for pet in pets
            for task in pet.tasks
            if status == "all" or task.completed == (status == "done")
        ]

 def conflict_with(self, pet: Pet, task: Task, start_time: int) -> Optional[str]:
        """Check whether placing `task` at `start_time` would overlap the plan.

        Returns a warning for the first overlapping item found, or None if the
        slot is free. Read-only: nothing is added, so call it before add_item to
        decide whether to proceed. Never raises. Linear in the number of items.
        """
        candidate = ScheduledItem(task, pet, start_time)
        for item in self.items:
            if item.start_time < candidate.end_time and candidate.start_time < item.end_time:
                return self._describe_overlap(item, candidate)
        return None

 def next_occurrence(self) -> Optional[Task]:
        """Return a fresh, pending copy due one period later, or None for a "once" task.

        The next due date is counted from this task's due date (not today), so a
        late completion doesn't shift the cadence.
        """
        days = RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        return replace(
            self,
            completed=False,
            due_date=self.due_date + timedelta(days=days),
            id=uuid4().hex,
        )

## 📸 Demo Walkthrough

Start the app with `streamlit run app.py`. The page is one scrolling screen, top to bottom:

**Main UI features**

- **Owner:** a text box for the owner's name. Everything you enter is kept for the session, so it survives Streamlit's reruns.
- **Add a Pet:** a form for name, species (dog, cat, other) and age. A table of your pets (with task counts) updates below it. Duplicate or blank names are rejected with an error message.
- **Add a Task:** pick a pet, then set a title, duration (1-240 min), priority (low, medium, high), an optional preferred time and a frequency (once, daily, weekly). If the preferred time clashes with the current plan, you get a warning right away.
- **Task list:** filter by pet and by status (pending, done, all), and sort by added order or preferred time. Priorities are marked 🔴 high, 🟡 medium, 🟢 low.
- **Build Schedule:** the "Generate schedule" button builds one plan across all pets. You see a summary banner, metrics (scheduled, minutes planned, couldn't fit), a time-ordered table with a "Why" column, any warnings, and a "Plan explained" expander.

**Example workflow**

1. **Add a pet.** In "Add a Pet", enter `Mochi`, choose `dog`, set age 3 and click *Add pet*. Mochi appears in the pets table. Add a second pet, `Pixel` the cat, the same way.
2. **Add tasks.** In "Add a Task", choose Mochi and enter "Morning walk", 30 minutes, high priority. Tick *Set a preferred time* and set 08:00. Click *Add task*. Then add "Breakfast" for Pixel (10 min, high, preferred 08:00). If you see a warning about 08:00 already being taken, the task was still added.
3. **Review the tasks.** Set *Sort by* to "Preferred time" and *Show pet* to a single pet to check what you entered. Tasks without a preferred time are listed last.
4. **Generate today's schedule.** Click *Generate schedule*. The table lists each task with its start-end time, pet, priority and the reason it was placed there, for example "scheduled at its preferred time" or "preferred time was taken, moved to the earliest free slot".
5. **Read the warnings.** A blue note says if a task was moved from the time you asked for. A yellow warning says if a task didn't fit in the day. A red conflict count (with the details) appears if two tasks overlap. Adjust a task's time or duration, add it again if needed, and regenerate.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

## Implementation Summary (Phase 2: Step 4)
So far, built the backend logic for Pawpal using the UML draft as a skeleton to start, filling in holes wherever needed like refinements and conflictions, etc. Also added tests which pass with no problems. Added a testing script in main.py to test the current implementations.

## Testing PawPal+

python -m pytest
Tests cover wide variety of cases for conflicts, resolution, method functionality checking, all to ensure cases are handled cleanly.

===================================================== test session starts ======================================================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Shahzaib\CodePath\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 32 items                                                                                                              

tests\test_pawpal.py ................................                                                                     [100%]

====================================================== 32 passed in 0.16s ======================================================

Confidence Level: 4
