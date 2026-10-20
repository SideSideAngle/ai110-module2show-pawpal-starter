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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

## Implementation Summary (Phase 2: Step 4)
So far, built the backend logic for Pawpal using the UML draft as a skeleton to start, filling in holes wherever needed like refinements and conflictions, etc. Also added tests which pass with no problems. Added a testing script in main.py to test the current implementations.
