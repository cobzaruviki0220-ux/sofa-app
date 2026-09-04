import streamlit as st
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="SofaStreaks", page_icon="⚽", layout="wide")

st.markdown("""
<style>
.stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #007AFF; color: white; }
div[data-testid="stExpander"] { border-radius: 8px; }
.streak-tag { background-color: #2c2c2e; padding: 4px 8px; border-radius: 6px; margin: 2px; display: inline-block; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ SofaScore Streaks Tracker")
st.write("Scanare meciuri și serii statistice (Streaks)")

azi = datetime.now()
optiuni_zile = {
    f"Azi ({azi.strftime('%d.%m')})": azi.strftime('%Y-%m-%d'),
    f"Mâine ({(azi + timedelta(days=1)).strftime('%d.%m')})": (azi + timedelta(days=1)).strftime('%Y-%m-%d'),
    f"Poimâine ({(azi + timedelta(days=2)).strftime('%d.%m')})": (azi + timedelta(days=2)).strftime('%Y-%m-%d')
}

zi_selectata = st.selectbox("Alege ziua:", list(optiuni_zile.keys()))
data_target = optiuni_zile[zi_selectata]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def obtine_meciuri(data_str):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{data_str}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("events", [])
    return []

def obtine_streaks_meci(event_id):
    url = f"https://api.sofascore.com/api/v1/event/{event_id}/team-events-streaks"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        streaks = []
        # Preluăm seriile generale (general, home, away)
        for category in ['general', 'home', 'away']:
            for item in data.get(category, []):
                name = item.get("name", "")
                value = item.get("value", "")
                if name:
                    streaks.append(f"{name}: **{value}**")
        return streaks
    return []

if st.button("🔎 Caută Meciuri & Streaks"):
    with st.spinner("Se analizează meciurile și seriile statistice..."):
        events = obtine_meciuri(data_target)
        if events:
            st.success(f"Am găsit {len(events)} meciuri. Se procesează primele 15...")
            
            # Afișăm primele 15 meciuri cu seriile lor
            for ev in events[:15]:
                match_id = ev.get("id")
                gazda = ev.get("homeTeam", {}).get("name", "N/A")
                oaspete = ev.get("awayTeam", {}).get("name", "N/A")
                liga = ev.get("tournament", {}).get("name", "Competiție")
                ora = datetime.fromtimestamp(ev.get("startTimestamp", 0)).strftime('%H:%M')
                
                streaks = obtine_streaks_meci(match_id)
                
                with st.expander(f"⏰ {ora} | {liga} — {gazda} vs {oaspete}"):
                    if streaks:
                        st.write("🔥 **Serii statistice (Streaks):**")
                        for s in streaks:
                            st.markdown(f"- {s}")
                    else:
                        st.write("Nu există serii speciale raportate pentru acest meci.")
        else:
            st.warning("Nu s-au putut prelua meciurile pe această dată.")
