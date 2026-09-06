import streamlit as st
import pandas as pd
import numpy as np
import hashlib
from datetime import datetime, timedelta
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="WeatherAI",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# COUNTRY DATA
# ============================================================

COUNTRIES = [
    {"id": "ind", "name": "New Delhi", "country": "India", "flag": "🇮🇳",
     "type": "monsoon", "volatility": 0.72},

    {"id": "usa", "name": "New York", "country": "United States", "flag": "🇺🇸",
     "type": "coastal", "volatility": 0.45},

    {"id": "gbr", "name": "London", "country": "United Kingdom", "flag": "🇬🇧",
     "type": "temperate", "volatility": 0.55},

    {"id": "jpn", "name": "Tokyo", "country": "Japan", "flag": "🇯🇵",
     "type": "coastal", "volatility": 0.58},

    {"id": "aus", "name": "Sydney", "country": "Australia", "flag": "🇦🇺",
     "type": "coastal", "volatility": 0.48},

    {"id": "bra", "name": "São Paulo", "country": "Brazil", "flag": "🇧🇷",
     "type": "tropical", "volatility": 0.66},

    {"id": "are", "name": "Dubai", "country": "United Arab Emirates", "flag": "🇦🇪",
     "type": "desert", "volatility": 0.25},

    {"id": "zaf", "name": "Cape Town", "country": "South Africa", "flag": "🇿🇦",
     "type": "coastal", "volatility": 0.40},

    {"id": "can", "name": "Toronto", "country": "Canada", "flag": "🇨🇦",
     "type": "continental", "volatility": 0.58},

    {"id": "deu", "name": "Berlin", "country": "Germany", "flag": "🇩🇪",
     "type": "temperate", "volatility": 0.52},

    {"id": "fra", "name": "Paris", "country": "France", "flag": "🇫🇷",
     "type": "temperate", "volatility": 0.50},

    {"id": "sgp", "name": "Singapore", "country": "Singapore", "flag": "🇸🇬",
     "type": "tropical", "volatility": 0.62},

    {"id": "egy", "name": "Cairo", "country": "Egypt", "flag": "🇪🇬",
     "type": "desert", "volatility": 0.22},

    {"id": "mex", "name": "Mexico City", "country": "Mexico", "flag": "🇲🇽",
     "type": "mountain", "volatility": 0.64},

    {"id": "idn", "name": "Jakarta", "country": "Indonesia", "flag": "🇮🇩",
     "type": "tropical", "volatility": 0.78},

    {"id": "nor", "name": "Oslo", "country": "Norway", "flag": "🇳🇴",
     "type": "continental", "volatility": 0.50},
]

BASE_TEMP = {
    "desert": 35,
    "tropical": 30,
    "monsoon": 29,
    "coastal": 22,
    "temperate": 17,
    "continental": 12,
    "mountain": 14
}

COND_BIAS = {
    "desert": ["sun", "sun", "sun", "psun"],
    "tropical": ["psun", "rain", "storm", "sun"],
    "monsoon": ["rain", "storm", "psun", "cloud"],
    "coastal": ["psun", "cloud", "sun", "rain"],
    "temperate": ["cloud", "psun", "rain", "sun"],
    "continental": ["cloud", "psun", "sun", "rain"],
    "mountain": ["psun", "cloud", "sun", "rain"]
}

CONDITIONS = {
    "sun": ("☀️", "Clear"),
    "psun": ("🌤️", "Partly Cloudy"),
    "cloud": ("☁️", "Cloudy"),
    "rain": ("🌧️", "Rain"),
    "storm": ("⛈️", "Thunderstorms")
}

ALERT_BY_TYPE = {
    "desert": (
        "🔥 Extreme Heat Warning",
        "Daytime temperatures may exceed 40°C. Limit outdoor exposure between noon and 4 PM."
    ),
    "tropical": (
        "🌊 Flash Flood Watch",
        "Heavy convective rainfall may cause localized flooding in low-lying areas."
    ),
    "monsoon": (
        "🌧️ Heavy Rainfall Alert",
        "Monsoon trough activity may bring intense rainfall over the next 48 hours."
    ),
    "coastal": (
        "💨 Coastal Wind Advisory",
        "Onshore winds strengthening — small craft should exercise caution near the coast."
    ),
    "temperate": (
        "🌡️ Frontal Passage Notice",
        "A weather front will move through, bringing brief but noticeable temperature swings."
    ),
    "continental": (
        "🥶 Cold Snap Advisory",
        "Overnight temperatures dropping sharply — protect pipes and outdoor plants."
    ),
    "mountain": (
        "🏔️ Elevation Weather Notice",
        "Conditions may change rapidly at higher elevations — check before travel."
    )
}


# ============================================================
# DETERMINISTIC RANDOM
# ============================================================

def seed_value(key):
    digest = hashlib.sha256(key.encode()).hexdigest()
    return int(digest[:8], 16)


def random_value(key):
    rng = np.random.default_rng(seed_value(key))
    return rng.random()


def clamp(value, low, high):
    return max(low, min(high, value))


# ============================================================
# GENERATE WEATHER DATA
# ============================================================

def generate_country_data(c):

    base = BASE_TEMP[c["type"]]
    bias = COND_BIAS[c["type"]]

    hourly = []

    for i in range(24):

        r = random_value(f'{c["id"]}-h-{i}')

        temp = round(
            base
            + np.sin((i / 24) * np.pi * 2 - np.pi / 2) * 5
            + (r - 0.5) * 2
        )

        precip = round(
            clamp(
                15
                + c["volatility"] * 40
                + np.sin(i / 4.3) * 20
                + (r - 0.5) * 20,
                0,
                96
            )
        )

        wind = round(
            clamp(
                8
                + c["volatility"] * 14
                + np.cos(i / 3.5) * 4,
                3,
                34
            )
        )

        humidity = round(
            clamp(
                40
                + c["volatility"] * 35
                + np.sin(i / 5.5) * 15,
                20,
                95
            )
        )

        if precip > 60:
            condition = "storm"
        elif precip > 35:
            condition = "rain"
        elif 6 <= i < 18:
            index = int(random_value(f'{c["id"]}-condition-{i}') * 2)
            condition = bias[index]
        else:
            condition = "cloud"

        if i == 0:
            hour_label = "Now"
        else:
            hour = ((i + 11) % 12) + 1
            period = "AM" if i < 12 else "PM"
            hour_label = f"{hour}{period}"

        hourly.append({
            "hour": hour_label,
            "temp": temp,
            "precip": precip,
            "wind": wind,
            "humidity": humidity,
            "condition": condition
        })

    # --------------------------------------------------------
    # 7 DAY FORECAST
    # --------------------------------------------------------

    daily = []

    day_names = [
        "Today",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun"
    ]

    today = datetime.now()

    for d in range(7):

        r = random_value(f'{c["id"]}-d-{d}')

        high = round(
            base
            + 2
            + np.sin(d / 1.6) * 3
            + (r - 0.5) * 2
        )

        low = round(
            high - 6 - c["volatility"] * 4
        )

        rain = round(
            clamp(
                15
                + c["volatility"] * 45
                + np.cos(d / 1.3) * 20,
                0,
                96
            )
        )

        wind = round(
            clamp(
                10
                + c["volatility"] * 12
                + np.sin(d / 2) * 5,
                5,
                32
            )
        )

        if rain > 60:
            condition = "storm"
        elif rain > 35:
            condition = "rain"
        else:
            condition = bias[d % len(bias)]

        date = today + timedelta(days=d)

        daily.append({
            "day": day_names[d],
            "date": date.strftime("%d %b"),
            "high": high,
            "low": low,
            "rain": rain,
            "wind": wind,
            "condition": condition
        })

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence_base = clamp(
        96 - c["volatility"] * 30,
        55,
        97
    )

    confidence_trend = []

    for i in range(7):

        r = random_value(f'{c["id"]}-c-{i}')

        confidence = round(
            clamp(
                confidence_base
                - (6 - i) * 1.5
                + (r - 0.5) * 8,
                40,
                98
            )
        )

        confidence_trend.append({
            "run": f"R{i + 1}",
            "confidence": confidence
        })

    confidence = confidence_trend[-1]["confidence"]

    if confidence >= 80:
        bust_risk = "Low"
    elif confidence >= 60:
        bust_risk = "Moderate"
    else:
        bust_risk = "High"

    previous_confidence = confidence_trend[-2]["confidence"]

    previous_temp = (
        daily[0]["high"]
        - round((random_value(c["id"] + "-previous") - 0.5) * 8)
    )

    temperature_change = daily[0]["high"] - previous_temp

    direction = "up" if temperature_change >= 0 else "down"

    bust = {
        "previous_temp": previous_temp,
        "previous_confidence": previous_confidence,
        "latest_temp": daily[0]["high"],
        "latest_confidence": confidence,
        "change": temperature_change,
        "direction": direction,
        "risk": bust_risk
    }

    # --------------------------------------------------------
    # CURRENT CONDITIONS
    # --------------------------------------------------------

    current_temp = hourly[0]["temp"]

    feels_like = (
        current_temp
        + round((random_value(c["id"] + "-feels") - 0.5) * 4)
    )

    uv = round(
        clamp(
            3
            + c["volatility"] * 2
            + (4 if c["type"] == "desert" else 0),
            1,
            11
        )
    )

    visibility = round(
        clamp(
            10 - c["volatility"] * 4,
            2,
            12
        )
    )

    current = {
        "temp": current_temp,
        "feels_like": feels_like,
        "condition": hourly[0]["condition"],
        "humidity": hourly[0]["humidity"],
        "wind": hourly[0]["wind"],
        "uv": uv,
        "visibility": visibility
    }

    # --------------------------------------------------------
    # ALERTS
    # --------------------------------------------------------

    alert_title, alert_body = ALERT_BY_TYPE[c["type"]]

    alerts = [
        {
            "title": alert_title,
            "body": alert_body,
            "type": "Official"
        },
        {
            "title": "🤖 Model Divergence Detected",
            "body": (
                f"Ensemble members disagree on timing for {c['name']}'s "
                "next system by several hours — confidence for that "
                "window is below average."
            ),
            "type": "AI"
        }
    ]

    return {
        "hourly": hourly,
        "daily": daily,
        "confidence": confidence,
        "confidence_trend": confidence_trend,
        "bust": bust,
        "current": current,
        "alerts": alerts
    }


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.weather-card {
    padding: 22px;
    border-radius: 22px;
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.10);
    backdrop-filter: blur(18px);
}

.big-temp {
    font-size: 64px;
    font-weight: 700;
    line-height: 1;
}

.small-muted {
    opacity: 0.65;
}

.metric {
    text-align: center;
    padding: 15px;
    border-radius: 15px;
}

.alert-box {
    padding: 18px;
    border-radius: 18px;
    margin-bottom: 12px;
}

.chat-user {
    padding: 12px;
    border-radius: 14px;
    margin: 8px 0;
}

.chat-ai {
    padding: 12px;
    border-radius: 14px;
    margin: 8px 0;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "dark" not in st.session_state:
    st.session_state.dark = True

if "selected_city" not in st.session_state:
    st.session_state.selected_city = "New Delhi"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "text": (
                "Hi! I'm your WeatherAI assistant. Ask me about "
                "the forecast, confidence levels, or what to expect today."
            )
        }
    ]


# ============================================================
# THEME
# ============================================================

if st.session_state.dark:

    st.markdown("""
    <style>
    .stApp {
        background:
        linear-gradient(
            160deg,
            #0B1120 0%,
            #121A33 55%,
            #0B1120 100%
        );
        color: #EEF1F8;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.06);
        padding: 15px;
        border-radius: 15px;
    }

    </style>
    """, unsafe_allow_html=True)

else:

    st.markdown("""
    <style>
    .stApp {
        background:
        linear-gradient(
            160deg,
            #EAF1FE 0%,
            #F7FAFF 55%,
            #FFFFFF 100%
        );
        color: #141B2E;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.75);
        padding: 15px;
        border-radius: 15px;
    }

    </style>
    """, unsafe_allow_html=True)


# ============================================================
# TOP BAR
# ============================================================

top1, top2, top3 = st.columns([2, 3, 1])

with top1:

    st.markdown(
        "# 🌦️ WeatherAI"
    )

with top2:

    st.caption(
        "AI-powered weather intelligence • Forecast confidence • Bust detection"
    )

with top3:

    if st.button(
        "☀️ Light" if st.session_state.dark else "🌙 Dark",
        use_container_width=True
    ):
        st.session_state.dark = not st.session_state.dark
        st.rerun()


# ============================================================
# LOCATION SELECTOR
# ============================================================

st.markdown("### 📍 Select Location")

city_names = [
    f'{c["flag"]} {c["name"]} — {c["country"]}'
    for c in COUNTRIES
]

selected_display = next(
    (
        x for x in city_names
        if st.session_state.selected_city in x
    ),
    city_names[0]
)

selected = st.selectbox(
    "Location",
    city_names,
    index=city_names.index(selected_display)
)

st.session_state.selected_city = selected.split(" — ")[0].split(" ", 1)[1]

country = next(
    c for c in COUNTRIES
    if c["name"] == st.session_state.selected_city
)

data = generate_country_data(country)

current = data["current"]
condition = data["hourly"][0]["condition"]

weather_icon, weather_label = CONDITIONS[condition]


# ============================================================
# HERO SECTION
# ============================================================

st.markdown("---")

hero1, hero2 = st.columns([1.4, 1])

with hero1:

    st.markdown(
        f"""
        <div class="weather-card">

        <div style="font-size:20px;opacity:0.7">
        {country["flag"]} {country["name"]}, {country["country"]}
        </div>

        <div style="font-size:90px;margin-top:15px">
        {weather_icon}
        </div>

        <div class="big-temp">
        {current["temp"]}°C
        </div>

        <div style="font-size:22px;margin-top:10px">
        {weather_label}
        </div>

        <div class="small-muted">
        Feels like {current["feels_like"]}°C
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

with hero2:

    st.markdown("### 🌤️ Current Conditions")

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "💧 Humidity",
            f'{current["humidity"]}%'
        )

        st.metric(
            "💨 Wind",
            f'{current["wind"]} km/h'
        )

    with c2:
        st.metric(
            "☀️ UV Index",
            current["uv"]
        )

        st.metric(
            "👁️ Visibility",
            f'{current["visibility"]} km'
        )


# ============================================================
# HOURLY FORECAST
# ============================================================

st.markdown("---")
st.markdown("## ⏱️ 24-Hour Forecast")

hourly_df = pd.DataFrame(data["hourly"])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=hourly_df["hour"],
        y=hourly_df["temp"],
        mode="lines+markers",
        name="Temperature °C",
        line=dict(width=3)
    )
)

fig.update_layout(
    height=350,
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis_title="Time",
    yaxis_title="Temperature °C",
    template="plotly_dark" if st.session_state.dark else "plotly_white"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# WEATHER DETAILS CHART
# ============================================================

st.markdown("### 🌧️ Rain Probability & Wind")

chart_type = st.radio(
    "Select data",
    ["Rain Probability", "Wind Speed", "Humidity"],
    horizontal=True
)

fig2 = go.Figure()

if chart_type == "Rain Probability":

    fig2.add_trace(
        go.Bar(
            x=hourly_df["hour"],
            y=hourly_df["precip"],
            name="Rain Probability"
        )
    )

    fig2.update_layout(
        yaxis_title="Probability (%)"
    )

elif chart_type == "Wind Speed":

    fig2.add_trace(
        go.Scatter(
            x=hourly_df["hour"],
            y=hourly_df["wind"],
            mode="lines+markers",
            name="Wind"
        )
    )

    fig2.update_layout(
        yaxis_title="Wind km/h"
    )

else:

    fig2.add_trace(
        go.Scatter(
            x=hourly_df["hour"],
            y=hourly_df["humidity"],
            mode="lines+markers",
            name="Humidity"
        )
    )

    fig2.update_layout(
        yaxis_title="Humidity %"
    )

fig2.update_layout(
    height=320,
    margin=dict(l=10, r=10, t=20, b=10),
    template="plotly_dark" if st.session_state.dark else "plotly_white"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)


# ============================================================
# 7 DAY FORECAST
# ============================================================

st.markdown("---")
st.markdown("## 📅 7-Day Forecast")

cols = st.columns(7)

for i, day in enumerate(data["daily"]):

    icon, label = CONDITIONS[day["condition"]]

    with cols[i]:

        st.markdown(
            f"""
            <div class="weather-card" style="text-align:center">

            <b>{day["day"]}</b>

            <div style="font-size:35px;margin:12px">
            {icon}
            </div>

            <div style="font-size:22px;font-weight:bold">
            {day["high"]}°C
            </div>

            <div class="small-muted">
            {day["low"]}°C
            </div>

            <div style="margin-top:10px">
            🌧️ {day["rain"]}%
            </div>

            <div>
            💨 {day["wind"]} km/h
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# AI CONFIDENCE
# ============================================================

st.markdown("---")
st.markdown("## 🤖 AI Forecast Confidence")

conf1, conf2 = st.columns([1, 2])

with conf1:

    confidence = data["confidence"]

    if confidence >= 80:
        risk = "LOW"
        emoji = "🟢"
    elif confidence >= 60:
        risk = "MODERATE"
        emoji = "🟡"
    else:
        risk = "HIGH"
        emoji = "🔴"

    st.metric(
        "Model Confidence",
        f"{confidence}%",
        f"{emoji} {risk}"
    )

with conf2:

    confidence_df = pd.DataFrame(
        data["confidence_trend"]
    )

    fig3 = go.Figure()

    fig3.add_trace(
        go.Scatter(
            x=confidence_df["run"],
            y=confidence_df["confidence"],
            mode="lines+markers",
            name="Confidence",
            line=dict(width=3)
        )
    )

    fig3.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=20, b=10),
        yaxis_title="Confidence (%)",
        yaxis=dict(range=[40, 100]),
        template=(
            "plotly_dark"
            if st.session_state.dark
            else "plotly_white"
        )
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )


# ============================================================
# FORECAST BUST DETECTION
# ============================================================

st.markdown("---")
st.markdown("## 🚨 Forecast Bust Detection")

bust = data["bust"]

b1, b2, b3, b4 = st.columns(4)

with b1:
    st.metric(
        "Previous Temperature",
        f'{bust["previous_temp"]}°C'
    )

with b2:
    st.metric(
        "Latest Temperature",
        f'{bust["latest_temp"]}°C'
    )

with b3:

    change_text = (
        f'+{bust["change"]}°C'
        if bust["change"] >= 0
        else f'{bust["change"]}°C'
    )

    st.metric(
        "Temperature Change",
        change_text
    )

with b4:

    risk = bust["risk"]

    if risk == "Low":
        risk_icon = "🟢"
    elif risk == "Moderate":
        risk_icon = "🟡"
    else:
        risk_icon = "🔴"

    st.metric(
        "Bust Risk",
        f"{risk_icon} {risk}"
    )

if bust["risk"] == "High":

    st.error(
        "🔴 High forecast-bust risk: "
        "the latest model conditions differ noticeably "
        "from the previous forecast."
    )

elif bust["risk"] == "Moderate":

    st.warning(
        "🟡 Moderate forecast-bust risk: "
        "some disagreement exists between forecast runs."
    )

else:

    st.success(
        "🟢 Low forecast-bust risk: "
        "the latest forecast remains relatively consistent."
    )


# ============================================================
# ALERTS
# ============================================================

st.markdown("---")
st.markdown("## ⚠️ Weather Alerts")

for alert in data["alerts"]:

    if alert["type"] == "Official":

        st.warning(
            f'**{alert["title"]}**\n\n'
            f'{alert["body"]}'
        )

    else:

        st.info(
            f'**{alert["title"]}**\n\n'
            f'{alert["body"]}'
        )


# ============================================================
# AI INSIGHTS
# ============================================================

st.markdown("---")
st.markdown("## 🧠 AI Weather Insights")

insight1, insight2, insight3 = st.columns(3)

with insight1:

    st.markdown("### 🌡️ Temperature")

    temp_change = data["daily"][0]["high"] - current["temp"]

    if temp_change > 0:
        st.write(
            f"Today's maximum temperature is expected "
            f"to be around **{data['daily'][0]['high']}°C**, "
            f"about **{temp_change}°C** above the current temperature."
        )
    else:
        st.write(
            f"Today's maximum temperature is expected "
            f"to remain around **{data['daily'][0]['high']}°C**."
        )


with insight2:

    st.markdown("### 🌧️ Rain")

    rain_probability = data["daily"][0]["rain"]

    if rain_probability >= 60:

        st.write(
            f"Rain probability is relatively high at "
            f"**{rain_probability}%**. Carry an umbrella "
            f"and monitor the latest forecast."
        )

    elif rain_probability >= 35:

        st.write(
            f"There is a **{rain_probability}%** chance of rain. "
            f"Conditions may change during the day."
        )

    else:

        st.write(
            f"Rain probability is relatively low at "
            f"**{rain_probability}%**."
        )


with insight3:

    st.markdown("### 🤖 Forecast Reliability")

    st.write(
        f"The current model confidence is "
        f"**{data['confidence']}%** with "
        f"**{data['bust']['risk']}** forecast-bust risk."
    )


# ============================================================
# WEATHER SUMMARY
# ============================================================

st.markdown("---")
st.markdown("## 📋 Weather Summary")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:

    st.markdown(
        f"""
        **Location:** {country["name"]}, {country["country"]}

        **Current:** {current["temp"]}°C — {weather_label}

        **Feels Like:** {current["feels_like"]}°C

        **Humidity:** {current["humidity"]}%

        **Wind:** {current["wind"]} km/h
        """
    )

with summary_col2:

    today_forecast = data["daily"][0]

    st.markdown(
        f"""
        **Today's High:** {today_forecast["high"]}°C

        **Today's Low:** {today_forecast["low"]}°C

        **Rain Probability:** {today_forecast["rain"]}%

        **Forecast Confidence:** {data["confidence"]}%

        **Bust Risk:** {data["bust"]["risk"]}
        """
    )


# ============================================================
# WEATHER AI ASSISTANT
# ============================================================

st.markdown("---")
st.markdown("## 💬 WeatherAI Assistant")

st.caption(
    "Ask about today's weather, rain, temperature, wind, "
    "confidence or forecast-bust risk."
)


def weather_ai_response(question, weather_data, location):

    q = question.lower()

    current_weather = weather_data["current"]
    today = weather_data["daily"][0]
    confidence = weather_data["confidence"]
    bust = weather_data["bust"]

    if (
        "temperature" in q
        or "temp" in q
        or "hot" in q
        or "cold" in q
    ):

        return (
            f"🌡️ The current temperature in "
            f"**{location}** is **{current_weather['temp']}°C** "
            f"and it feels like **{current_weather['feels_like']}°C**. "
            f"Today's expected high is **{today['high']}°C** "
            f"and low is **{today['low']}°C**."
        )

    if (
        "rain" in q
        or "raining" in q
        or "umbrella" in q
        or "precipitation" in q
    ):

        return (
            f"🌧️ Today's rain probability for **{location}** "
            f"is approximately **{today['rain']}%**. "
            f"The current condition is **{CONDITIONS[current_weather['condition']][1]}**."
        )

    if (
        "wind" in q
        or "windy" in q
    ):

        return (
            f"💨 The current wind speed is approximately "
            f"**{current_weather['wind']} km/h**. "
            f"Today's forecast wind speed is around "
            f"**{today['wind']} km/h**."
        )

    if (
        "humidity" in q
        or "moisture" in q
    ):

        return (
            f"💧 Current humidity in **{location}** is "
            f"**{current_weather['humidity']}%**."
        )

    if (
        "confidence" in q
        or "reliable" in q
        or "accuracy" in q
    ):

        return (
            f"🤖 The current forecast confidence is "
            f"**{confidence}%**. "
            f"The estimated forecast-bust risk is "
            f"**{bust['risk']}**."
        )

    if (
        "bust" in q
        or "forecast error" in q
        or "forecast risk" in q
    ):

        return (
            f"🚨 The current forecast-bust risk is "
            f"**{bust['risk']}**. "
            f"The temperature difference between the "
            f"previous and latest forecast is "
            f"**{bust['change']}°C**."
        )

    if (
        "weather" in q
        or "condition" in q
        or "today" in q
    ):

        return (
            f"🌦️ In **{location}**, the current weather is "
            f"**{CONDITIONS[current_weather['condition']][1]}** "
            f"with a temperature of **{current_weather['temp']}°C**. "
            f"Today's high is **{today['high']}°C**, "
            f"with a **{today['rain']}%** rain probability."
        )

    if (
        "hello" in q
        or "hi" in q
        or "hey" in q
    ):

        return (
            "👋 Hello! I'm WeatherAI. "
            "Ask me about temperature, rain, wind, "
            "humidity, forecast confidence or bust risk."
        )

    return (
        f"🤖 I can help you understand the forecast for "
        f"**{location}**. Try asking:\n\n"
        f"- What is the temperature?\n"
        f"- Will it rain today?\n"
        f"- What is the wind speed?\n"
        f"- What is the forecast confidence?\n"
        f"- What is the forecast-bust risk?"
    )


# Display previous messages

for message in st.session_state.messages:

    with st.chat_message(
        message["role"],
        avatar="🤖" if message["role"] == "assistant" else "👤"
    ):

        st.markdown(message["text"])


# Chat input

prompt = st.chat_input(
    "Ask WeatherAI something..."
)

if prompt:

    # User message
    st.session_state.messages.append(
        {
            "role": "user",
            "text": prompt
        }
    )

    with st.chat_message(
        "user",
        avatar="👤"
    ):

        st.markdown(prompt)

    # AI response
    response = weather_ai_response(
        prompt,
        data,
        country["name"]
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "text": response
        }
    )

    with st.chat_message(
        "assistant",
        avatar="🤖"
    ):

        st.markdown(response)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        opacity:0.65;
        padding:20px;
    ">
        🌦️ <b>WeatherAI</b><br>
        AI-powered weather intelligence dashboard<br>
        <small>
        Forecast data in this demo is simulated for demonstration purposes.
        </small>
    </div>
    """,
    unsafe_allow_html=True
)
