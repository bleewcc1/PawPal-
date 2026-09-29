"""
app.py -- Streamlit UI for PawPal+.

A thin display layer over pawpal_system.py: every list of tasks shown here
comes from a Scheduler method (get_upcoming_tasks, get_overdue_tasks,
sort_by_time, filter_tasks), conflict warnings come straight from
Scheduler.find_conflicts(), and the availability check comes from
Scheduler.find_next_available_slot(). No ranking/filtering logic is
reimplemented here -- that's what main.py and the pytest suite already
verified.
"""

from datetime import date, datetime, time
from pathlib import Path

import streamlit as st

from pawpal_system import CATEGORY_WEIGHT, DEFAULT_DATA_FILE, FREQUENCY_INTERVALS, Owner, Pet, Scheduler, Task

DATA_FILE = Path(DEFAULT_DATA_FILE)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ---------------------------------------------------------------------------
# Styling -- a playful hero banner (emoji-based: no external image URLs, so
# it always renders, even offline) plus lightweight card polish.
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    .pawpal-hero {
        background: linear-gradient(135deg, #ffb347 0%, #ff7f6b 50%, #f96d9b 100%);
        border-radius: 18px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.12);
    }
    .pawpal-hero h1 {
        margin: 0.25rem 0 0.1rem 0;
        font-size: 2.2rem;
    }
    .pawpal-hero p {
        margin: 0;
        opacity: 0.92;
        font-size: 1.05rem;
    }
    .pawpal-dogs {
        font-size: 2.1rem;
        letter-spacing: 0.4rem;
        animation: pawpal-bounce 2.2s ease-in-out infinite;
    }
    @keyframes pawpal-bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid rgba(49, 51, 63, 0.1);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
    }
    </style>
    <div class="pawpal-hero">
        <div class="pawpal-dogs">🐕 🐩 🦮 🐾</div>
        <h1>PawPal+</h1>
        <p>Smart pet care scheduling for happy, healthy pets</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def load_owner() -> Owner:
    if DATA_FILE.exists():
        return Owner.load_from_json(str(DATA_FILE))
    return Owner("My Household")


def save_owner(owner: Owner) -> None:
    owner.save_to_json(str(DATA_FILE))


if "owner" not in st.session_state:
    st.session_state.owner = load_owner()

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# ---------------------------------------------------------------------------
# Sidebar: manage pets
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("🐾 Pets")
    with st.form("add_pet_form", clear_on_submit=True):
        name = st.text_input("Name")
        species = st.text_input("Species")
        breed = st.text_input("Breed (optional)")
        age = st.number_input("Age (years)", min_value=0.0, step=1.0, value=0.0)
        if st.form_submit_button("Add Pet", width="stretch"):
            if not name:
                st.error("Pet name is required.")
            else:
                try:
                    owner.add_pet(Pet(name, species or "Unknown", breed=breed, age=age or None))
                    save_owner(owner)
                    st.success(f"🐶 Added {name} to the family!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    if owner.list_pets():
        for pet in owner.list_pets():
            st.write(f"- **{pet.name}** ({pet.species}) -- {len(pet.tasks)} task(s)")
    else:
        st.info("No pets yet. Add one above.")

if not owner.list_pets():
    st.warning("Add at least one pet in the sidebar to start scheduling tasks.")
    st.stop()

pet_names = [p.name for p in owner.list_pets()]

# ---------------------------------------------------------------------------
# Summary dashboard -- st.metric tiles built from Scheduler queries
# ---------------------------------------------------------------------------

pending_all = scheduler.filter_tasks(completed=False)
overdue_all = scheduler.get_overdue_tasks()
conflicts = scheduler.find_conflicts()

m1, m2, m3, m4 = st.columns(4)
m1.metric("🐾 Pets", len(owner.list_pets()))
m2.metric("📋 Pending Tasks", len(pending_all))
m3.metric("⏰ Overdue", len(overdue_all))
m4.metric("⚠️ Conflicts", len(conflicts))

# ---------------------------------------------------------------------------
# Conflict warnings -- Scheduler.find_conflicts(), never raises
# ---------------------------------------------------------------------------

for warning in conflicts:
    st.warning(f"⚠️ {warning}")

# ---------------------------------------------------------------------------
# Next available slot -- Scheduler.find_next_available_slot(), a capability
# beyond the basic sort/filter/conflict/recurrence requirements.
# ---------------------------------------------------------------------------

with st.container(border=True):
    st.subheader("📅 Next Available Slot")
    slot_pet = st.selectbox("Check availability for", pet_names, key="slot_pet")
    slot = scheduler.find_next_available_slot(pet_name=slot_pet)
    if slot is not None:
        st.info(
            f"🟢 Next open slot for **{slot_pet}**: {slot:%a, %b %d %I:%M %p} "
            "(scanned in 30-minute steps over the next 7 days)"
        )
    else:
        st.warning(f"No open slot found for {slot_pet} in the next 7 days.")

# ---------------------------------------------------------------------------
# Add a task
# ---------------------------------------------------------------------------

with st.container(border=True):
    st.subheader("➕ Add a Task")
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            pet_name = st.selectbox("Pet", pet_names)
            description = st.text_input("Description")
            category = st.selectbox("Category", [*CATEGORY_WEIGHT.keys(), "general"])
        with col2:
            task_date = st.date_input("Date", value=date.today())
            task_time = st.time_input("Time", value=time(hour=9, minute=0))
            frequency = st.selectbox("Frequency", list(FREQUENCY_INTERVALS.keys()))

        if st.form_submit_button("Add Task", width="stretch"):
            if not description:
                st.error("Description is required.")
            else:
                scheduled_time = datetime.combine(task_date, task_time)
                owner.get_pet(pet_name).add_task(
                    Task(description, scheduled_time, frequency=frequency, category=category)
                )
                save_owner(owner)
                st.success(f"✅ Added '{description}' for {pet_name}.")
                st.rerun()

# ---------------------------------------------------------------------------
# Task display helpers -- every list of tasks passed in here was already
# selected/ordered by a Scheduler method; this only renders it.
# ---------------------------------------------------------------------------

STATUS_ICONS = {"done": "✅ Done", "overdue": "⏰ Overdue", "pending": "🕒 Pending"}


def task_row(task: Task) -> dict:
    if task.completed:
        status = STATUS_ICONS["done"]
    elif task.is_overdue():
        status = STATUS_ICONS["overdue"]
    else:
        status = STATUS_ICONS["pending"]
    return {
        "Pet": task.pet.name,
        "Category": task.category.title(),
        "When": task.scheduled_time.strftime("%a, %b %d  %I:%M %p"),
        "Task": task.description,
        "Status": status,
    }


def render_tasks(tasks: list[Task], key_prefix: str) -> None:
    """Professional-looking sortable grid (st.dataframe) plus a simple
    completion control for whichever of these tasks are still pending."""
    if not tasks:
        st.info("Nothing here.")
        return

    st.dataframe([task_row(t) for t in tasks], width="stretch", hide_index=True)

    pending = [t for t in tasks if not t.completed]
    if not pending:
        return

    options = {f"{t.pet.name} -- {t.description} ({t.scheduled_time:%a %I:%M %p})": t.task_id for t in pending}
    col1, col2 = st.columns([4, 1])
    choice = col1.selectbox("Mark a task complete", list(options), key=f"{key_prefix}_select")
    if col2.button("Mark Done", key=f"{key_prefix}_btn", width="stretch"):
        try:
            scheduler.complete_task(options[choice])
            save_owner(owner)
            st.success("🎉 Nice work -- task marked complete!")
            st.rerun()
        except ValueError as e:
            st.error(str(e))


# ---------------------------------------------------------------------------
# Views -- each tab is a thin wrapper around one Scheduler query method
# ---------------------------------------------------------------------------

tab_priority, tab_time, tab_filter = st.tabs(["📋 Priority Schedule", "🕒 Sorted by Time", "🔍 Filter"])

with tab_priority:
    st.caption(
        "Scheduler.get_upcoming_tasks() / get_overdue_tasks(): overdue first, "
        "then category urgency (medication > appointment > feeding > walk), then soonest time."
    )
    now = datetime.now()
    ranked = scheduler.get_upcoming_tasks(now=now)
    overdue = [t for t in ranked if t.is_overdue(now)]
    upcoming = [t for t in ranked if not t.is_overdue(now)]

    st.markdown(f"#### ⏰ Overdue ({len(overdue)})")
    render_tasks(overdue, "priority_overdue")
    st.markdown(f"#### 🕒 Upcoming ({len(upcoming)})")
    render_tasks(upcoming, "priority_upcoming")

with tab_time:
    st.caption("Scheduler.sort_by_time(): pure chronological order, ignoring category.")
    pet_filter = st.selectbox("Pet", ["All"] + pet_names, key="time_pet_filter")
    tasks = scheduler.sort_by_time(pet_name=None if pet_filter == "All" else pet_filter)
    render_tasks(tasks, "time")

with tab_filter:
    st.caption("Scheduler.filter_tasks(pet_name=..., completed=...)")
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox("Pet", ["All"] + pet_names, key="filter_pet")
    with col2:
        status_filter = st.selectbox("Status", ["All", "Pending", "Completed"], key="filter_status")
    completed = {"All": None, "Pending": False, "Completed": True}[status_filter]
    tasks = scheduler.filter_tasks(pet_name=None if pet_filter == "All" else pet_filter, completed=completed)
    render_tasks(tasks, "filter")
