import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta, date
import holidays
import time

DATA_FILE = "data/storage.json"


# ---------------------------
# Initialize storage
# ---------------------------
def init_storage():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        data = {
            "trips": [],
            "members": {},
            "expenses": {},
            "settings": {
                "weekend_days": ["Saturday", "Sunday"],
                "holidays": []
            }
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trip Manager",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_storage()
data = load_data()
settings = data.setdefault(
    "settings",
    {
        "week_off_days": ["Saturday", "Sunday"],
        "states": [],
        "holiday_year": datetime.today().year,
        "holidays": {}
    }
)

save_data(data)

with st.sidebar:
    st.markdown(
        """
        <style>
        .sidebar-title {
            padding: 16px;
            border-radius: 16px;
            background: linear-gradient(135deg, #111827, #1f2937);
            color: white;
            text-align: center;
            margin-bottom: 15px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
            <div class="sidebar-title">
                <h2 style="margin-bottom:0;"> Trip Expense Manager</h2>
            </div>
            """,
        unsafe_allow_html=True
    )

    menu = st.radio(
        "📌 Navigate",
        [
            "🏕️ Create Trip",
            "👥 Add Members",
            "💰 Add Expense",
            "📊 Dashboard",
            "⚙️ Settings"
        ]
    )

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.metric("Trips", len(data["trips"]))

    with c2:
        st.metric(
            "Members",
            sum(len(v) for v in data["members"].values())
        )

    total_expense = sum(
        expense["amount"]
        for trip in data["expenses"].values()
        for expense in trip
    )

    st.metric(
        "Total Expenses",
        f"₹ {total_expense:,.2f}"
    )

# ---------------------------
# Create Trip
# ---------------------------
if menu == "🏕️ Create Trip":
    trip_action = st.segmented_control(
        "Trip",
        ["➕ Create Trip", "⚙️ Manage Trips"],
        default="➕ Create Trip",
        label_visibility="collapsed"
    )

    if trip_action == "➕ Create Trip":
        # Initialize session state
        if "trip_start" not in st.session_state:
            st.session_state.trip_start = datetime.today().date()

        if "trip_duration" not in st.session_state:
            st.session_state.trip_duration = 1

        if "trip_end" not in st.session_state:
            st.session_state.trip_end = (
                    st.session_state.trip_start +
                    timedelta(days=st.session_state.trip_duration - 1)
            )


        def duration_changed():
            st.session_state.trip_end = (
                    st.session_state.trip_start +
                    timedelta(days=st.session_state.trip_duration - 1)
            )


        def end_date_changed():
            days = (
                           st.session_state.trip_end -
                           st.session_state.trip_start
                   ).days + 1

            st.session_state.trip_duration = max(1, days)


        def start_date_changed():
            st.session_state.trip_end = (
                    st.session_state.trip_start +
                    timedelta(days=st.session_state.trip_duration - 1)
            )


        trip_name = st.text_input("Trip Name")

        include_holidays = st.radio(
            "🎉 Consider Public Holidays?",
            ["Yes", "No"],
            horizontal=True,
            index=1
        )

        trip_states = []

        if include_holidays == "Yes":
            trip_states = st.multiselect(
                "🗺️ States Covered in this Trip",
                options=settings.get("states", []),
                help="Select the states you will visit to include public holidays."
            )

        col1, col2 = st.columns(2)

        with col1:
            st.date_input(
                "Start Date",
                key="trip_start",
                on_change=start_date_changed
            )

        with col2:
            st.date_input(
                "End Date",
                key="trip_end",
                min_value=st.session_state.trip_start,
                on_change=end_date_changed
            )

        st.slider(
            "Trip Duration (days)",
            min_value=1,
            max_value=30,
            key="trip_duration",
            on_change=duration_changed
        )

        week_off_days = settings.get(
            "week_off_days",
            ["Saturday", "Sunday"]
        )

        weekend_days = 0
        weekday_days = 0

        current = st.session_state.trip_start

        while current <= st.session_state.trip_end:

            day_name = current.strftime("%A")

            if day_name in week_off_days:
                weekend_days += 1
            else:
                weekday_days += 1

            current += timedelta(days=1)

        # -----------------------------
        # Calculate Public Holidays
        # -----------------------------
        holiday_lookup = {}

        for state in trip_states:
            state_holidays = settings.get("holidays", {}).get(state, [])
            for holiday in state_holidays:
                date = holiday["date"]
                if date not in holiday_lookup:
                    holiday_lookup[date] = []
                holiday_lookup[date].append(
                    f"{holiday['name']} ({state})"
                )

        holiday_count = 0
        holiday_rows = []

        current = st.session_state.trip_start

        while current <= st.session_state.trip_end:
            key = str(current)
            if key in holiday_lookup:
                holiday_count += 1

                for holiday in holiday_lookup[key]:
                    holiday_rows.append({
                        "Date": current.strftime("%d %b %Y"),
                        "Day": current.strftime("%A"),
                        "Holiday": holiday
                    })

            current += timedelta(days=1)

        with st.expander("✈️ Trip Overview", expanded=True):
            st.write(
                f"**📅 Travel:** "
                f"{st.session_state.trip_start.strftime('%d %b %Y')} "
                f"→ "
                f"{st.session_state.trip_end.strftime('%d %b %Y')}"
            )

            if include_holidays == "Yes":
                st.write(
                    f"**🗺️ States:** {', '.join(trip_states)}"
                )

            st.divider()

            total_working_days = (
                weekday_days - holiday_count
                if include_holidays == "Yes"
                else weekday_days
            )

            if include_holidays == "Yes":

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("🗓️ Total Days", st.session_state.trip_duration)

                with col2:
                    st.metric("💼 Working Days", total_working_days)

                with col3:
                    st.metric("🏖️ Weekends", weekend_days)

                with col4:
                    st.metric("🎉 Holidays", holiday_count)

            else:

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("🗓️ Total Days", st.session_state.trip_duration)

                with col2:
                    st.metric("💼 Working Days", weekday_days)

                with col3:
                    st.metric("🏖️ Weekends", weekend_days)

        if holiday_rows:
            with st.expander(f"🎉 Holidays During Trip ({holiday_count})", expanded=True):
                holiday_df = pd.DataFrame(holiday_rows)
                st.dataframe(
                    holiday_df,
                    width='stretch',
                    hide_index=True
                )

        if st.button("Create Trip"):
            if not trip_name:
                st.error("Please enter a trip name.")

            elif include_holidays == "Yes" and len(trip_states) == 0:
                st.error("Please select at least one state.")

            else:
                trip_id = str(len(data["trips"]) + 1)

                data["trips"].append({
                    "trip_id": trip_id,
                    "trip_name": trip_name,
                    "start_date": str(st.session_state.trip_start),
                    "end_date": str(st.session_state.trip_end),
                    "states": trip_states
                })

                data["members"][trip_id] = []
                data["expenses"][trip_id] = []

                save_data(data)
                st.success("✅ Trip created successfully!")

    elif trip_action == "⚙️ Manage Trips":
        if not data["trips"]:
            st.warning("No trips available")

        else:
            trip_options = ["-- Select a Trip --"] + [
                trip["trip_name"] for trip in data["trips"]
            ]

            selected_trip_name = st.selectbox(
                "Select Trip",
                trip_options,
                index=0,
                key="manage_trip"
            )

            if selected_trip_name != "-- Select a Trip --":
                trip = next(
                    t for t in data["trips"]
                    if t["trip_name"] == selected_trip_name
                )

                trip_id = trip["trip_id"]

                st.divider()

                new_name = st.text_input(
                    "Trip Name",
                    value=trip["trip_name"],
                    key="edit_name"
                )

                new_start = st.date_input(
                    "Start Date",
                    value=pd.to_datetime(trip["start_date"]).date(),
                    key="edit_start"
                )

                new_end = st.date_input(
                    "End Date",
                    value=pd.to_datetime(trip["end_date"]).date(),
                    min_value=new_start,
                    key="edit_end"
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("💾 Update Trip", width='stretch'):
                        trip["trip_name"] = new_name
                        trip["start_date"] = str(new_start)
                        trip["end_date"] = str(new_end)

                        save_data(data)
                        st.success("✅ Trip updated successfully!")
                        st.rerun()

                with col2:
                    confirm = st.checkbox(
                        "Confirm delete",
                        key="delete_confirm"
                    )

                    if st.button(
                            "🗑️ Delete Trip",
                            width='stretch'
                    ):
                        if confirm:
                            data["trips"] = [
                                t for t in data["trips"]
                                if t["trip_id"] != trip_id
                            ]

                            data["members"].pop(trip_id, None)
                            data["expenses"].pop(trip_id, None)

                            save_data(data)
                            st.success("✅ Trip deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Please confirm deletion.")

# ---------------------------
# Add Members
# -------------------------
elif menu == "👥 Add Members":
    st.header("👥 Trip Members")

    if not data["trips"]:
        st.warning("No trips available. Please create a trip first.")

    else:
        trip_options = ["-- Select Trip --"] + [
            t["trip_name"] for t in data["trips"]
        ]

        selected_trip = st.selectbox(
            "Select Trip",
            trip_options,
            index=0
        )

        if selected_trip == "-- Select Trip --":
            st.info("Please select a trip to continue.")
            st.stop()

        trip_map = {t["trip_name"]: t["trip_id"] for t in data["trips"]}

        trip_id = trip_map[selected_trip]
        members = data["members"].get(trip_id, [])

        # ==========================
        # Add Member Card
        # ==========================
        with st.container(border=True):

            st.subheader("➕ Add New Member")

            col1, col2 = st.columns([4, 1])

            with col1:
                member_name = st.text_input(
                    "Member Name",
                    placeholder="Enter member name",
                    label_visibility="collapsed"
                )

            with col2:
                add_member = st.button(
                    "Add",
                    width='stretch'
                )

            if add_member:

                member_name = member_name.strip()

                if not member_name:
                    st.error("Please enter a member name.")

                elif member_name in members:
                    st.warning("Member already exists.")

                else:
                    data["members"][trip_id].append(member_name)
                    save_data(data)
                    st.success(
                        f"{member_name} added successfully.",
                    )

        # ==========================
        # Members Overview
        # ==========================
        with st.container(border=True):

            c1, c2 = st.columns([4, 1])

            with c1:
                st.subheader("👥 Members")

            with c2:
                st.metric("Total", len(members))

            if members:

                # Store which row is being edited
                if "editing_member" not in st.session_state:
                    st.session_state.editing_member = None

                for idx, member in enumerate(members):

                    # ----------------------------
                    # NORMAL ROW
                    # ----------------------------
                    if st.session_state.editing_member != idx:

                        c1, c2, c3 = st.columns([8, 1, 1])

                        with c1:
                            st.write(f"**{idx + 1}. {member}**")

                        with c2:
                            if st.button("✏️", key=f"edit_{idx}"):
                                st.session_state.editing_member = idx
                                st.rerun()

                        with c3:
                            if st.button("🗑️", key=f"delete_{idx}"):
                                data["members"][trip_id].pop(idx)
                                save_data(data)

                                st.success("Member deleted successfully.")
                                st.rerun()

                    # ----------------------------
                    # INLINE EDIT ROW
                    # ----------------------------
                    else:

                        c1, c2, c3, c4 = st.columns([6, 1, 1, 1])

                        with c1:
                            new_name = st.text_input(
                                "Member Name",
                                value=member,
                                key=f"edit_name_{idx}",
                                label_visibility="collapsed"
                            )

                        with c2:
                            if st.button("✔️", key=f"save_{idx}"):

                                new_name = new_name.strip()

                                if not new_name:
                                    st.warning("Name cannot be empty.")

                                elif (
                                        new_name in data["members"][trip_id]
                                        and new_name != member
                                ):
                                    st.warning("Member already exists.")

                                else:
                                    data["members"][trip_id][idx] = new_name
                                    save_data(data)

                                    st.session_state.editing_member = None

                                    st.success("Member updated successfully.")
                                    st.rerun()

                        with c3:
                            if st.button("❌", key=f"cancel_{idx}"):
                                st.session_state.editing_member = None
                                st.rerun()

                        with c4:
                            if st.button("🗑️", key=f"delete_edit_{idx}"):
                                data["members"][trip_id].pop(idx)
                                save_data(data)

                                st.session_state.editing_member = None

                                st.success("Member deleted successfully.")
                                st.rerun()

            else:
                st.info("No members have been added yet.")

# ---------------------------
# Add Expense
# ---------------------------
elif menu == "💰 Add Expense":
    st.header("💰 Add Expense")

    if not data["trips"]:
        st.warning("No trips available")
    else:
        trip_options = ["-- Select Trip --"] + [
            t["trip_name"] for t in data["trips"]
        ]

        selected_trip = st.selectbox(
            "Select Trip",
            trip_options,
            index=0
        )

        if selected_trip == "-- Select Trip --":
            st.info("Please select a trip to continue.")
            st.stop()

        trip_map = {t["trip_name"]: t["trip_id"] for t in data["trips"]}
        trip_id = trip_map[selected_trip]

        members = data["members"].get(trip_id, [])

        if not members:
            st.warning("Add members first")
        else:
            st.subheader("➕ Add Expense")
            with st.form("expense_form", clear_on_submit=True):

                col1, col2 = st.columns(2)

                with col1:
                    desc = st.text_input(
                        "Description",
                        placeholder="Hotel / Food / Taxi"
                    )

                with col2:
                    trip = next(
                        t for t in data["trips"]
                        if t["trip_id"] == trip_id
                    )

                    trip_start = pd.to_datetime(trip["start_date"]).date()
                    trip_end = pd.to_datetime(trip["end_date"]).date()

                    default_date = datetime.today().date()

                    # If today is outside the trip, use the trip start date
                    if default_date < trip_start or default_date > trip_end:
                        default_date = trip_start

                    expense_date = st.date_input(
                        "Expense Date",
                        value=default_date,
                        min_value=trip_start,
                        max_value=trip_end,
                        help=f"Select a date between {trip_start.strftime('%d %b %Y')} and {trip_end.strftime('%d %b %Y')}"
                    )

                col3, col4 = st.columns(2)

                with col3:
                    amount = st.number_input(
                        "Amount (₹)",
                        min_value=0,
                        step=10
                    )

                with col4:
                    paid_by = st.selectbox(
                        "Paid By",
                        ["-- Select Member --"] + members,
                        index=0
                    )

                c1, c2 = st.columns(2)

                with c1:
                    add_clicked = st.form_submit_button(
                        "➕ Add Expense",
                        use_container_width=True,
                        type="primary"
                    )

                with c2:
                    cancel_clicked = st.form_submit_button(
                        "❌ Cancel",
                        use_container_width=True
                    )

            if add_clicked:

                if paid_by == "-- Select Member --":
                    st.error("Please select the member who paid the expense.")

                elif not desc.strip():
                    st.error("Please enter description.")

                elif amount <= 0:
                    st.error("Amount should be greater than zero.")

                else:

                    data["expenses"][trip_id].append({
                        "description": desc.strip(),
                        "amount": amount,
                        "paid_by": paid_by,
                        "date": expense_date.strftime("%Y-%m-%d")
                    })

                    save_data(data)

                    st.success("✅ Expense added successfully.")
                    st.rerun()

            if cancel_clicked:
                st.rerun()

            # ==========================
            # Expense Overview
            # ==========================
            expenses = data["expenses"].get(trip_id, [])
            st.subheader("💳 Expense History")

            if expenses:

                expense_df = pd.DataFrame(expenses)

                expense_df["date"] = pd.to_datetime(
                    expense_df["date"],
                    errors="coerce"
                )

                # Remove invalid dates if any
                expense_df = expense_df.dropna(subset=["date"])

                expense_df.insert(
                    0,
                    "Sl.No",
                    range(1, len(expense_df) + 1)
                )

                expense_df["Display Date"] = expense_df["date"].apply(
                    lambda x: x.strftime("%d %b %Y")
                )

                # -------------------------
                # Filters
                # -------------------------
                f1, f2, f3, f4 = st.columns(4)

                with f1:
                    member_filter = st.selectbox(
                        "Paid By",
                        ["All"] + members
                    )

                with f2:
                    search = st.text_input(
                        "Search Description"
                    )

                with f3:
                    from_date = st.date_input(
                        "From Date",
                        value=trip_start,
                        min_value=trip_start,
                        max_value=trip_end
                    )

                with f4:
                    to_date = st.date_input(
                        "To Date",
                        value=trip_end,
                        min_value=trip_start,
                        max_value=trip_end
                    )

                filtered_df = expense_df.copy()

                filtered_df = filtered_df[
                    (filtered_df["date"].dt.date >= from_date) &
                    (filtered_df["date"].dt.date <= to_date)
                    ]

                if member_filter != "All":
                    filtered_df = filtered_df[
                        filtered_df["paid_by"] == member_filter
                        ]

                if search:
                    filtered_df = filtered_df[
                        filtered_df["description"].str.contains(
                            search,
                            case=False,
                            na=False
                        )
                    ]

                filtered_df = filtered_df[
                    [
                        "Sl.No",
                        "Display Date",
                        "description",
                        "amount",
                        "paid_by"
                    ]
                ]

                filtered_df.columns = [
                    "Sl.No",
                    "Date",
                    "Description",
                    "Amount (₹)",
                    "Paid By"
                ]

                st.dataframe(
                    filtered_df,
                    width='stretch',
                    hide_index=True,
                    column_config={
                        "Sl.No": st.column_config.NumberColumn(
                            "Sl.No",
                            width="small"
                        ),
                        "description": "Description",
                        "amount": st.column_config.NumberColumn(
                            "Amount (₹)",
                            format="₹ %.2f"
                        ),
                        "paid_by": "Paid By",
                        "date": "Date"
                    }
                )

                st.divider()

                # ==========================
                # Edit / Delete
                # ==========================
                st.subheader("✏️ Edit / Delete Expense")

                expense_no = st.selectbox(
                    "Select Expense",
                    ["Select"] + expense_df["Sl.No"].tolist()
                )

                if expense_no != "Select":

                    idx = expense_no - 1

                    expense = expenses[idx]

                    desc = st.text_input(
                        "Description",
                        value=expense["description"],
                        key="edit_desc"
                    )

                    amount = st.number_input(
                        "Amount",
                        value=float(expense["amount"]),
                        key="edit_amount"
                    )

                    paid_by = st.selectbox(
                        "Paid By",
                        members,
                        index=members.index(expense["paid_by"]),
                        key="edit_paid_by"
                    )

                    expense_date = st.date_input(
                        "Expense Date",
                        value=pd.to_datetime(expense["date"]).date(),
                        key="edit_date"
                    )

                    c1, c2 = st.columns(2)

                    with c1:

                        if st.button(
                                "💾 Update Expense",
                                use_container_width=True
                        ):
                            expenses[idx] = {
                                "description": desc.strip(),
                                "amount": amount,
                                "paid_by": paid_by,
                                "date": expense_date.strftime("%Y-%m-%d")
                            }

                            save_data(data)
                            st.success("Expense updated successfully.")
                            st.rerun()

                    with c2:

                        confirm = st.checkbox(
                            "Confirm Delete"
                        )

                        if st.button(
                                "🗑️ Delete Expense",
                                use_container_width=True
                        ):

                            if confirm:
                                expenses.pop(idx)

                                save_data(data)

                                st.success("Expense deleted successfully.")
                                st.rerun()
                            else:
                                st.error(
                                    "Please confirm deletion."
                                )

            else:
                st.info("No expenses available.")

# ---------------------------
# Dashboard
# ---------------------------
elif menu == "📊 Dashboard":
    st.header("📊 Trip Dashboard")

    if not data["trips"]:
        st.warning("No trips available")
    else:
        trip_map = {t["trip_name"]: t["trip_id"] for t in data["trips"]}
        selected_trip = st.selectbox("Select Trip", list(trip_map.keys()))
        trip_id = trip_map[selected_trip]

        expenses = data["expenses"].get(trip_id, [])
        members = data["members"].get(trip_id, [])

        if expenses:
            df = pd.DataFrame(expenses)

            st.subheader("Expenses")
            st.dataframe(df)

            total = df["amount"].sum()
            st.metric("Total Expense", f"₹ {total}")

            if members:
                share = total / len(members)
                st.subheader("Split Summary")
                st.write(f"Each member owes: ₹ {share:.2f}")

                summary = {m: share for m in members}
                st.json(summary)
        else:
            st.info("No expenses yet")

# ---------------------------
# Settings
# ---------------------------
elif menu == "⚙️ Settings":
    st.header("⚙️ Settings")

    # -----------------------------
    # Initialize Settings
    # -----------------------------
    if "settings" not in data:
        data["settings"] = {
            "week_off_days": ["Saturday", "Sunday"],
            "state": "Karnataka",
            "holidays": []
        }
        save_data(data)

    settings = data["settings"]

    # -----------------------------
    # Weekly Off Days
    # -----------------------------
    st.subheader("📅 Weekly Off Days")

    week_days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    selected_weekoffs = []

    cols = st.columns(4)

    for i, day in enumerate(week_days):
        with cols[i % 4]:
            if st.checkbox(
                    day,
                    value=day in settings.get(
                        "week_off_days",
                        ["Saturday", "Sunday"]
                    ),
                    key=f"weekoff_{day}"
            ):
                selected_weekoffs.append(day)

    st.divider()

    # -----------------------------
    # Public Holidays
    # -----------------------------
    st.subheader("🏖️ Public Holidays")

    state_map = {
        "Andhra Pradesh": "AP",
        "Assam": "AS",
        "Bihar": "BR",
        "Chhattisgarh": "CG",
        "Delhi": "DL",
        "Goa": "GA",
        "Gujarat": "GJ",
        "Haryana": "HR",
        "Himachal Pradesh": "HP",
        "Jharkhand": "JH",
        "Karnataka": "KA",
        "Kerala": "KL",
        "Madhya Pradesh": "MP",
        "Maharashtra": "MH",
        "Odisha": "OR",
        "Punjab": "PB",
        "Rajasthan": "RJ",
        "Tamil Nadu": "TN",
        "Telangana": "TG",
        "Uttar Pradesh": "UP",
        "Uttarakhand": "UK",
        "West Bengal": "WB"
    }

    selected_states = st.multiselect(
        "States to Load Holidays",
        options=list(state_map.keys()),
        default=settings.get("states", ["Karnataka"])
    )

    holiday_year = st.number_input(
        "Holiday Year",
        min_value=2024,
        max_value=2035,
        value=settings.get("holiday_year", datetime.today().year)
    )

    holiday_data = {}

    if selected_states:

        with st.spinner("Loading holidays..."):

            for state in selected_states:
                cal = holidays.country_holidays(
                    "IN",
                    subdiv=state_map[state],
                    years=holiday_year
                )

                holiday_data[state] = [
                    {
                        "date": str(d),
                        "name": name
                    }
                    for d, name in sorted(cal.items())
                ]

        total = sum(len(v) for v in holiday_data.values())

        st.success(
            f"Loaded {total} holidays from {len(selected_states)} state(s)."
        )

        for state in selected_states:
            with st.expander(f"📅 {state} ({len(holiday_data[state])})"):
                st.dataframe(
                    pd.DataFrame(holiday_data[state]),
                    width='stretch'
                )

    # -----------------------------
    # Save
    # -----------------------------
    if st.button("💾 Save Settings", width='stretch'):
        settings["week_off_days"] = selected_weekoffs
        settings["holiday_year"] = holiday_year
        settings["states"] = selected_states
        settings["holidays"] = holiday_data

        data["settings"] = settings

        save_data(data)

        st.success("✅ Settings saved successfully!")
