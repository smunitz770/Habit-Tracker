from calendar import monthrange
from datetime import date, timedelta

import streamlit as st
from supabase import create_client


# -----------------------------
# Auth (simple password)
# -----------------------------
password = st.text_input("Enter password", type="password")

if password != "#Mhabittracker770":
    st.stop()


# -----------------------------
# Supabase setup
# -----------------------------
SUPABASE_URL = "https://ftexhuhrywsmtwjquqqx.supabase.co"
SUPABASE_KEY = "sb_publishable_EdrvbNWZNO3lOZuQeFPCxg_Vc6Ieo-X"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------
# Data
# -----------------------------
def load_data() -> dict[str, str]:
    response = supabase.table("habit_days").select("*").execute()

    data = {}
    for row in response.data:
        data[row["day"]] = row["status"]

    return data


def set_day_status(data: dict[str, str], day: date, status: str) -> None:
    day_str = day.isoformat()

    if status == "none":
        supabase.table("habit_days").delete().eq("day", day_str).execute()
    else:
        supabase.table("habit_days").upsert({
            "day": day_str,
            "status": status
        }).execute()


# -----------------------------
# Core logic
# -----------------------------
def tracking_start(data: dict[str, str]) -> date:
    if not data:
        return date.today()
    return min(date.fromisoformat(k) for k in data.keys())


def explicit_status(data: dict[str, str], day: date) -> str:
    return data.get(day.isoformat(), "none")


def effective_status(data: dict[str, str], day: date) -> str:
    # Missing days are treated as wins in logic only.
    return data.get(day.isoformat(), "win")


def daterange(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def calculate_current_streak(data: dict[str, str]) -> int:
    start = tracking_start(data)
    today = date.today()

    streak = 0
    current = today
    while current >= start:
        if effective_status(data, current) == "fail":
            break
        streak += 1
        current -= timedelta(days=1)

    return streak


def calculate_longest_streak(data: dict[str, str]) -> int:
    start = tracking_start(data)
    end = date.today()

    longest = 0
    current = 0

    for day in daterange(start, end):
        if effective_status(data, day) == "fail":
            current = 0
        else:
            current += 1
            longest = max(longest, current)

    return longest


def count_period(data: dict[str, str], start: date, end: date) -> tuple[int, int]:
    wins = 0
    fails = 0

    for day in daterange(start, end):
        if effective_status(data, day) == "fail":
            fails += 1
        else:
            wins += 1

    return wins, fails


def current_month_range(view_day: date | None = None) -> tuple[date, date]:
    ref = view_day or date.today()
    start = ref.replace(day=1)
    end = ref.replace(day=monthrange(ref.year, ref.month)[1])
    return start, end


def total_range(data: dict[str, str]) -> tuple[date, date]:
    start = tracking_start(data)
    end = date.today()
    return start, end


# -----------------------------
# Calendar helpers
# -----------------------------
def build_month_weeks(year: int, month: int) -> list[list[int | None]]:
    first_weekday = date(year, month, 1).weekday()  # Mon=0
    days_in_month = monthrange(year, month)[1]

    weeks: list[list[int | None]] = []
    week: list[int | None] = [None] * 7

    day_num = 1
    for i in range(first_weekday, 7):
        week[i] = day_num
        day_num += 1
    weeks.append(week)

    while day_num <= days_in_month:
        week = []
        for _ in range(7):
            if day_num <= days_in_month:
                week.append(day_num)
                day_num += 1
            else:
                week.append(None)
        weeks.append(week)

    return weeks


def month_title(d: date) -> str:
    return d.strftime("%B %Y")


def prev_month(d: date) -> date:
    month = d.month - 1
    year = d.year
    if month == 0:
        month = 12
        year -= 1
    return d.replace(year=year, month=month, day=1)


def next_month(d: date) -> date:
    month = d.month + 1
    year = d.year
    if month == 13:
        month = 1
        year += 1
    return d.replace(year=year, month=month, day=1)


# -----------------------------
# Styling
# -----------------------------
st.set_page_config(page_title="Daily Habit Tracker", layout="centered")

st.markdown(
    """
<style>
    .main {
        background-color: #f4f6f8;
    }

    .block-container {
        max-width: 760px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #24324a;
    }

    div.stButton > button {
        height: 58px;
        width: 100% !important;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        font-size: 15px;
        font-weight: 600;
        box-shadow: none;
    }

    .hero-card {
        background: #e8f5e9;
        border-radius: 24px;
        padding: 38px 24px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.05);
        margin: 8px 0 18px 0;
    }

    .hero-number {
        font-size: 64px;
        line-height: 1;
        font-weight: 700;
        color: #111111;
        margin-bottom: 8px;
    }

    .hero-label {
        font-size: 18px;
        color: #6b7280;
    }

    .stat-card {
        border-radius: 20px;
        padding: 20px 18px;
        min-height: 120px;
    }

    .stat-label {
        font-size: 14px;
        color: #5f6b7a;
        margin-bottom: 12px;
    }

    .stat-value {
        font-size: 42px;
        line-height: 1;
        font-weight: 700;
        color: #111111;
    }

    .calendar-wrap {
        background: transparent;
        margin-top: 10px;
    }

    .month-subtext {
        text-align: center;
        font-size: 13px;
        color: #7b8794;
        margin-top: -6px;
        margin-bottom: 14px;
    }

    .weekday {
        text-align: center;
        font-size: 12px;
        color: #7b8794;
        margin-bottom: 4px;
        font-weight: 600;
    }

    .day-tile {
        border-radius: 14px;
        text-align: center;
        padding: 14px 0;
        margin: 4px 0;
        font-size: 14px;
        font-weight: 600;
        color: #334155;
    }

    .editor-card {
        background: #ffffff;
        border-radius: 22px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
        margin-top: 20px;
    }

    .legend {
        display: flex;
        gap: 18px;
        justify-content: center;
        align-items: center;
        margin: 6px 0 10px 0;
        font-size: 13px;
        color: #6b7280;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 999px;
        display: inline-block;
    }

    .element-container:has(.day-win-marker) + div button {
        background-color: #dcfce7 !important;
        color: #166534 !important;
        border: 1px solid #bbf7d0 !important;
    }

    .element-container:has(.day-fail-marker) + div button {
        background-color: #fee2e2 !important;
        color: #991b1b !important;
        border: 1px solid #fecaca !important;
    }

    .element-container:has(.day-empty-marker) + div button {
        background-color: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #e5e7eb !important;
    }

    .element-container:has(.day-win-marker.day-today-marker) + div button {
        border: 2px solid #111111 !important;
    }

    .element-container:has(.day-fail-marker.day-today-marker) + div button {
        border: 2px solid #111111 !important;
    }

    .element-container:has(.day-empty-marker.day-today-marker) + div button {
        border: 2px solid #111111 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Session state
# -----------------------------
if "view_month" not in st.session_state:
    st.session_state.view_month = date.today().replace(day=1)

if "editor_date" not in st.session_state:
    st.session_state.editor_date = date.today()

if "editor_status" not in st.session_state:
    st.session_state.editor_status = "none"

# -----------------------------
# Load data and compute stats
# -----------------------------
data = load_data()

today = date.today()
month_start, month_end = current_month_range(today)
total_start, total_end = total_range(data)

current_streak = calculate_current_streak(data)
longest_streak = calculate_longest_streak(data)

total_wins, total_fails = count_period(data, total_start, total_end)

# -----------------------------
# Header
# -----------------------------
st.title("Daily Habit Tracker")

st.markdown(
    f"""
<div class="hero-card">
    <div class="hero-number">{current_streak}</div>
    <div class="hero-label">Current Streak</div>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Today actions
# -----------------------------
st.subheader("Today")

today_col1, today_col2 = st.columns(2, gap="large")

with today_col1:
    if st.button("Win", use_container_width=True, key="today_win"):
        set_day_status(data, today, "win")
        st.rerun()

with today_col2:
    if st.button("Fail", use_container_width=True, key="today_fail"):
        set_day_status(data, today, "fail")
        st.rerun()

st.divider()

# -----------------------------
# Stats
# -----------------------------
row1_col1, row1_col2 = st.columns(2, gap="large")

with row1_col1:
    st.markdown(
        f"""
<div class="stat-card" style="background:#e3f2fd;">
    <div class="stat-label">Longest Streak</div>
    <div class="stat-value">{longest_streak}</div>
</div>
""",
        unsafe_allow_html=True,
    )

with row1_col2:
    st.markdown(
        f"""
<div class="stat-card" style="background:#fdecea;">
    <div class="stat-label">Total Fails</div>
    <div class="stat-value">{total_fails}</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

row2_col1 = st.columns(1)[0]

with row2_col1:
    st.markdown(
        f"""
<div class="stat-card" style="background:#e8f5e9;">
    <div class="stat-label">Total Wins</div>
    <div class="stat-value">{total_wins}</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.divider()

# -----------------------------
# Calendar header
# -----------------------------
nav_left, nav_center, nav_right = st.columns([1, 2, 1])

with nav_left:
    if st.button("◀", key="prev_month_nav"):
        st.session_state.view_month = prev_month(st.session_state.view_month)
        st.rerun()

with nav_center:
    st.markdown(
        f"<h3 style='text-align:center; margin-bottom:0;'>{month_title(st.session_state.view_month)}</h3>",
        unsafe_allow_html=True,
    )


with nav_right:
    if st.button("▶", key="next_month_nav"):
        st.session_state.view_month = next_month(st.session_state.view_month)
        st.rerun()

st.markdown(
    """
<div class="legend">
    <div class="legend-item"><span class="legend-dot" style="background:#e8f5e9;"></span>Win</div>
    <div class="legend-item"><span class="legend-dot" style="background:#fdecea;"></span>Fail</div>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Calendar
# -----------------------------


def next_status(current: str) -> str:
    if current == "none":
        return "win"
    if current == "win":
        return "fail"
    return "none"


view_year = st.session_state.view_month.year
view_month_num = st.session_state.view_month.month
weeks = build_month_weeks(view_year, view_month_num)

weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
weekday_cols = st.columns(7)
for idx, label in enumerate(weekday_labels):
    weekday_cols[idx].markdown(
        f"<div class='weekday'>{label}</div>",
        unsafe_allow_html=True,
    )

for week in weeks:
    cols = st.columns(7)
    for i, day_num in enumerate(week):
        if day_num is None:
            cols[i].markdown("<div style='height:58px;'></div>",
                             unsafe_allow_html=True)
            continue

        day_obj = date(view_year, view_month_num, day_num)
        status = explicit_status(data, day_obj)
        is_future = day_obj > today

        marker_classes = []

        if status == "win":
            marker_classes.append("day-win-marker")
        elif status == "fail":
            marker_classes.append("day-fail-marker")
        else:
            marker_classes.append("day-empty-marker")

        if day_obj == today:
            marker_classes.append("day-today-marker")

        cols[i].markdown(
            f"<div class='{' '.join(marker_classes)}'></div>",
            unsafe_allow_html=True,
        )

        if cols[i].button(
            str(day_num),
            key=f"day_{day_obj.isoformat()}",
            use_container_width=True,
            disabled=is_future,
        ):
            new_status = next_status(status)
            set_day_status(data, day_obj, new_status)
            st.session_state.view_month = day_obj.replace(day=1)
            st.rerun()
