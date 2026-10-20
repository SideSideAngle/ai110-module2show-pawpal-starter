from pawpal_system import Owner, Pet, Schedule, Task, format_time, time_sort_key


def at(hour: int, minute: int = 0) -> int:
    """Clock time as minutes from midnight."""
    return hour * 60 + minute


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=240)

    mochi = Pet(name="Mochi", species="dog", age=4)
    pixel = Pet(name="Pixel", species="cat", age=2)
    owner.add_pet(mochi)
    owner.add_pet(pixel)

    # Added deliberately out of time order so the sorting is visible.
    owner.add_task("Mochi", Task("Training session", 20, "medium", preferred_time=at(17, 30)))
    owner.add_task("Pixel", Task("Play time", 25, "medium"))
    owner.add_task("Pixel", Task("Brush fur", 15, "low", preferred_time=at(12)))
    owner.add_task("Mochi", Task("Morning walk", 30, "high", preferred_time=at(8)))
    owner.add_task("Pixel", Task("Breakfast", 10, "high", preferred_time=at(8)))
    owner.add_task("Mochi", Task("Evening meal", 10, "high", preferred_time=at(18)))

    # Complete one task per pet so the status filter has something to find.
    owner.pets[0].get_pending_tasks()[0].mark_complete()  # Mochi: Training session
    owner.pets[1].get_pending_tasks()[1].mark_complete()  # Pixel: Brush fur

    def show(heading: str, pairs) -> None:
        print(f"\n{heading}")
        for pet, task in pairs:
            when = format_time(task.preferred_time) if task.preferred_time is not None else "--:--"
            state = "done" if task.completed else "pending"
            print(f"  {when}  {pet.name:<6} {task.title:<17} [{state}]")

    print("=" * 50)
    print("Sorting and filtering demo")
    print("=" * 50)
    show("All tasks, in the order they were added:", owner.filter_tasks())
    by_time = Schedule.sort_by_time([t for _, t in owner.filter_tasks()])
    owners = {t.id: p for p, t in owner.filter_tasks()}
    show("All tasks, sorted by time (no-time tasks last):", [(owners[t.id], t) for t in by_time])
    show("Pending only:", owner.filter_tasks(status="pending"))
    show("Done only:", owner.filter_tasks(status="done"))
    show("Pixel only:", owner.filter_tasks(pet_name="Pixel"))
    show(
        "Mochi, pending, sorted by time:",
        sorted(owner.filter_tasks("Mochi", "pending"), key=lambda pt: time_sort_key(pt[1])),
    )
    print()

    schedule = owner.generate_schedule()

    print("=" * 50)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 50)
    print(schedule.explain())


    print("=" * 50)
    print("Conflict detection demo (hand-placed items)")
    print("=" * 50)
    manual = Schedule()
    manual.add_item(mochi, Task("Vet call", 30), at(9), "manual")
    manual.add_item(mochi, Task("Grooming", 20), at(9, 15), "manual")
    manual.add_item(pixel, Task("Medicine", 10), at(9, 20), "manual")
    warning = manual.conflict_with(pixel, Task("Nap check", 10), at(9, 25))
    print(f"Before adding 'Nap check' at 09:25 -> {warning}")
    print(manual.explain())

    print()
    print("=" * 50)
    print("Same-start-time demo (two tasks at exactly 10:00)")
    print("=" * 50)
    same_time = Schedule()
    same_time.add_item(mochi, Task("Give medicine", 15, "high"), at(10), "manual")
    same_time.add_item(pixel, Task("Clean litter box", 15, "medium"), at(10), "manual")
    found = same_time.find_conflicts()
    print(same_time.explain())
    assert len(found) == 1, f"expected exactly one warning, got {found}"
    assert "10:00-10:15" in found[0]
    print("\nOK: the schedule flagged the double-booked 10:00 slot.")


if __name__ == "__main__":
    main()
