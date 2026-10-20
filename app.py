import streamlit as st

from pawpal_system import Owner, Pet, Schedule, Task, format_time

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_ICONS = {"high": "🔴", "medium": "🟡", "low": "🟢"}

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# The Owner lives in session_state so pets and tasks survive Streamlit's re-runs.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner: Owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

# --- Add a pet -------------------------------------------------------------
st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
    add_pet_clicked = st.form_submit_button("Add pet")

if add_pet_clicked:
    if not pet_name.strip():
        st.error("Please enter a pet name.")
    else:
        try:
            owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
            st.success(f"Added {pet_name.strip()}.")
        except ValueError as err:
            st.error(str(err))

if owner.pets:
    st.write("Your pets:")
    st.table(
        [
            {"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)}
            for p in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

# --- Add a task ------------------------------------------------------------
st.subheader("Add a Task")
if not owner.pets:
    st.caption("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        target_pet = st.selectbox("For which pet?", [p.name for p in owner.pets])
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        col4, col5 = st.columns(2)
        with col4:
            use_preferred = st.checkbox("Set a preferred time")
            preferred = st.time_input("Preferred time")
        with col5:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        add_task_clicked = st.form_submit_button("Add task")

    if add_task_clicked:
        try:
            new_task = Task(
                title=task_title.strip() or "Untitled task",
                duration_minutes=int(duration),
                priority=priority,
                preferred_time=preferred.hour * 60 + preferred.minute if use_preferred else None,
                frequency=frequency,
            )
            # Check the slot against the current plan *before* adding, so the owner
            # hears about a clash right away instead of after generating a schedule.
            clash = None
            if new_task.preferred_time is not None:
                pet_obj = next(p for p in owner.pets if p.name == target_pet)
                clash = owner.generate_schedule().conflict_with(pet_obj, new_task, new_task.preferred_time)
            owner.add_task(target_pet, new_task)
            st.success(f"Added '{new_task.title}' to {target_pet}.")
            if clash:
                st.warning(
                    f"⚠️ {clash}\n\nThe task was still added. When you generate the schedule it will be "
                    "moved to the next free slot, or change its preferred time to avoid the clash."
                )
        except ValueError as err:
            st.error(str(err))

all_tasks = owner.get_all_tasks()
if owner.pets:
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        filter_pet = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with fcol2:
        filter_status = st.selectbox("Show status", ["pending", "done", "all"])
    with fcol3:
        sort_choice = st.selectbox("Sort by", ["Added order", "Preferred time"])
    shown_tasks = owner.filter_tasks(
        pet_name=None if filter_pet == "All pets" else filter_pet,
        status=filter_status,
    )
    if sort_choice == "Preferred time":
        # Schedule.sort_by_time works on tasks, so map each sorted task back to its pet.
        pet_of = {task.id: pet for pet, task in shown_tasks}
        shown_tasks = [
            (pet_of[t.id], t) for t in Schedule.sort_by_time([t for _, t in shown_tasks])
        ]
else:
    shown_tasks = []

if shown_tasks:
    st.write(f"Tasks ({len(shown_tasks)}):")
    st.table(
        [
            {
                "Pet": pet.name,
                "Task": task.title,
                "Minutes": task.duration_minutes,
                "Priority": f"{PRIORITY_ICONS[task.priority]} {task.priority}",
                "Preferred": format_time(task.preferred_time) if task.preferred_time is not None else "-",
                "Frequency": task.frequency,
            }
            for pet, task in shown_tasks
        ]
    )
elif owner.pets:
    st.info("No tasks match these filters.")

st.divider()

# --- Build the schedule ----------------------------------------------------
st.subheader("Build Schedule")
st.caption("Builds one plan across all of your pets' pending tasks.")

if st.button("Generate schedule"):
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        schedule = owner.generate_schedule()
        conflicts = schedule.find_conflicts()
        moved = [i for i in schedule.items if "moved" in i.reason]

        # Headline status: green only when the plan is clean.
        if conflicts or schedule.unscheduled:
            st.warning(
                f"Scheduled {len(schedule.items)} task(s) ({schedule.total_minutes} min), "
                "but some need your attention below."
            )
        else:
            st.success(f"All set! {len(schedule.items)} task(s) scheduled, {schedule.total_minutes} minutes in total.")

        m1, m2, m3 = st.columns(3)
        m1.metric("Scheduled", len(schedule.items))
        m2.metric("Minutes planned", schedule.total_minutes)
        m3.metric("Couldn't fit", len(schedule.unscheduled))

        st.table(
            [
                {
                    "Time": f"{format_time(i.start_time)}-{format_time(i.end_time)}",
                    "Pet": i.pet.name,
                    "Task": i.task.title,
                    "Priority": f"{PRIORITY_ICONS[i.task.priority]} {i.task.priority}",
                    "Why": i.reason,
                }
                for i in schedule.items
            ]
        )

        # Overlaps: say who/what/when, and what the owner can do about it.
        if conflicts:
            st.error(f"{len(conflicts)} scheduling conflict(s) found")
            for warning in conflicts:
                st.warning(warning, icon="⚠️")
            st.caption("Fix: change one task's preferred time or duration, then generate again.")

        # Not conflicts, but the owner's requested time wasn't honoured, so say so.
        for item in moved:
            st.info(
                f"{item.pet.name}'s '{item.task.title}' wanted "
                f"{format_time(item.task.preferred_time)} but that slot was taken; "
                f"it was moved to {format_time(item.start_time)}.",
                icon="🔀",
            )

        for pet, task in schedule.unscheduled:
            st.warning(
                f"Could not fit {pet.name}'s '{task.title}' ({task.duration_minutes} min). "
                "Shorten it, lower other tasks' durations, or widen the day.",
                icon="⏳",
            )

        with st.expander("Plan explained"):
            st.text(schedule.explain())
