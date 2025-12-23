import streamlit as st
import datetime
import json
from pathlib import Path
import requests

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Nina’s Main Character Dashboard",
    page_icon="💗",
    layout="wide"
)

# -------------------------------------------------
# Files for persistence
# -------------------------------------------------
TODOS_FILE = Path("todos.json")
SETTINGS_FILE = Path("settings.json")

VIBES = [
    "Soft grind",
    "Locked in",
    "CEO mode",
    "Golden retriever energy",
    "Cozy & calm",
    "Unhinged (but productive)"
]

# -------------------------------------------------
# Helper functions (save / load)
# -------------------------------------------------
def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

# -------------------------------------------------
# Weather emoji mapping (dramatic edition)
# -------------------------------------------------
def weather_emoji(short_forecast: str, temp_f=None) -> str:
    s = (short_forecast or "").lower()

    # Condition-based emojis
    if "thunder" in s or "t-storm" in s or "storm" in s:
        return "⛈️"
    if "tornado" in s:
        return "🌪️"
    if "snow" in s or "flurr" in s or "sleet" in s or "ice" in s or "freezing" in s:
        return "❄️"
    if "hail" in s:
        return "🧊"
    if "rain" in s or "showers" in s or "drizzle" in s:
        return "🌧️"
    if "fog" in s or "haze" in s or "mist" in s or "smoke" in s:
        return "🌫️"
    if "wind" in s or "breezy" in s or "gust" in s:
        return "💨"
    if "cloud" in s or "overcast" in s:
        return "☁️"
    if "sun" in s or "clear" in s or "fair" in s:
        # temp-based drama for sunny
        if temp_f is not None and temp_f >= 85:
            return "🔥"
        return "☀️"

    # Temp-based fallback drama
    if temp_f is not None:
        if temp_f <= 32:
            return "🥶"
        if temp_f >= 90:
            return "🔥"

    return "🌤️"

# -------------------------------------------------
# Weather.gov (NO API KEY) - multi-period forecast
# -------------------------------------------------
def get_nyc_forecast_periods(n_periods: int = 3):
    headers = {"User-Agent": "NinaDashboard/1.0 (contact@example.com)"}
    lat, lon = 40.7128, -74.0060

    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    r = requests.get(points_url, headers=headers, timeout=10)
    if r.status_code != 200:
        return None, "Could not load weather location"

    points_data = r.json()
    forecast_url = points_data["properties"]["forecast"]

    r = requests.get(forecast_url, headers=headers, timeout=10)
    if r.status_code != 200:
        return None, "Could not load forecast"

    forecast_data = r.json()
    periods = forecast_data["properties"]["periods"]

    cleaned = []
    for p in periods[:n_periods]:
        cleaned.append({
            "name": p.get("name", "Forecast"),
            "temp": p.get("temperature"),
            "temp_unit": p.get("temperatureUnit", "F"),
            "short": p.get("shortForecast", ""),
            "wind": p.get("windSpeed", ""),
            "detail": p.get("detailedForecast", "")
        })
    return cleaned, None

# -------------------------------------------------
# Init session state
# -------------------------------------------------
if "todos" not in st.session_state:
    st.session_state.todos = load_json(TODOS_FILE, [])

if "settings" not in st.session_state:
    st.session_state.settings = load_json(SETTINGS_FILE, {"vibe": VIBES[0]})

# -------------------------------------------------
# Header
# -------------------------------------------------
st.title("💗 Nina’s Main Character Dashboard")

now = datetime.datetime.now()
st.caption(f"{now.strftime('%A, %B %d, %Y')} • {now.strftime('%I:%M %p')}")

left, right = st.columns([1, 2], gap="large")

# -------------------------------------------------
# LEFT COLUMN: Compact Weather Cards + Vibe
# -------------------------------------------------
with left:
    st.subheader("NYC Weather")

    periods, err = get_nyc_forecast_periods(n_periods=3)
    if err:
        st.warning(err)
    else:
        cols = st.columns(3, gap="small")
        for idx, p in enumerate(periods):
            emo = weather_emoji(p["short"], p["temp"])
            with cols[idx]:
                st.markdown(f"### {emo} {p['name']}")
                if p["temp"] is not None:
                    st.metric("Temp", f"{p['temp']}°{p['temp_unit']}")
                st.caption(p["short"])
                st.caption(f"Wind {p['wind']}")
                with st.expander("Details"):
                    st.write(p["detail"])

    st.write("")
    st.subheader("Today’s Vibe")

    saved_vibe = st.session_state.settings.get("vibe", VIBES[0])
    default_index = VIBES.index(saved_vibe) if saved_vibe in VIBES else 0

    vibe = st.selectbox("Choose your energy", VIBES, index=default_index)

    if vibe != st.session_state.settings.get("vibe"):
        st.session_state.settings["vibe"] = vibe
        save_json(SETTINGS_FILE, st.session_state.settings)

    st.write(f"✨ Current vibe: **{vibe}**")

# -------------------------------------------------
# RIGHT COLUMN: To-Do List
# -------------------------------------------------
with right:
    st.subheader("To-Do List")

    new_task = st.text_input("Add a task", placeholder="e.g., Finish CenterSquare memo")

    col_add, col_clear_all, col_clear_done = st.columns([1, 1, 1])

    with col_add:
        if st.button("Add 💗", use_container_width=True):
            if new_task.strip():
                st.session_state.todos.append({"task": new_task.strip(), "done": False})
                save_json(TODOS_FILE, st.session_state.todos)
                st.rerun()

    with col_clear_all:
        if st.button("Clear all", use_container_width=True):
            st.session_state.todos = []
            save_json(TODOS_FILE, st.session_state.todos)
            st.rerun()

    with col_clear_done:
        if st.button("Clear completed", use_container_width=True):
            st.session_state.todos = [t for t in st.session_state.todos if not t["done"]]
            save_json(TODOS_FILE, st.session_state.todos)
            st.rerun()

    st.write("")

    if not st.session_state.todos:
        st.info("No tasks yet. Add one and be iconic.")
    else:
        for i, t in enumerate(st.session_state.todos):
            c1, c2, c3 = st.columns([0.12, 0.78, 0.10])

            with c1:
                done = st.checkbox("", value=t["done"], key=f"done_{i}")
                if done != t["done"]:
                    st.session_state.todos[i]["done"] = done
                    save_json(TODOS_FILE, st.session_state.todos)

            with c2:
                st.write(("✅ " if done else "⬜️ ") + t["task"])

            with c3:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.todos.pop(i)
                    save_json(TODOS_FILE, st.session_state.todos)
                    st.rerun()

st.divider()
st.caption("Built by Nina 💗")
