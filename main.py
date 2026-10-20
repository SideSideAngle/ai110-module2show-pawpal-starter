from pawpal_system import Owner, Pet, Task


def at(hour: int, minute: int = 0) -> int:
    """Clock time as minutes from midnight."""
    return hour * 60 + minute


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=240)

    mochi = Pet(name="Mochi", species="dog", age=4)
    pixel = Pet(name="Pixel", species="cat", age=2)
    owner.add_pet(mochi)
    owner.add_pet(pixel)

    owner.add_task("Mochi", Task("Morning walk", 30, "high", preferred_time=at(8)))
    owner.add_task("Mochi", Task("Training session", 20, "medium", preferred_time=at(17, 30)))
    owner.add_task("Pixel", Task("Breakfast", 10, "high", preferred_time=at(8)))
    owner.add_task("Pixel", Task("Brush fur", 15, "low", preferred_time=at(12)))
    owner.add_task("Pixel", Task("Play time", 25, "medium"))

    schedule = owner.generate_schedule()

    print("=" * 50)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 50)
    print(schedule.explain())


if __name__ == "__main__":
    main()
