import streamlit as st
from datetime import datetime, timedelta
from curl_cffi import requests

st.set_page_config(page_title="SofaStreaks", page_icon="⚽", layout="wide")

st.markdown("""
<style>
.stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #007AFF; color: white; }
div[data-testid="stExpander"] { border-radius: 8px; }
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com"
}

def obtine_meciuri(data_str):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{data_str}"
    try:
        r = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=12)
        if r.status_code == 200:
            res_json = r.json()
            return res_json.get("events", [])
    except Exception as e:
        st.error(f"Eroare rețea meciuri: {e}")
    return []

def obtine_streaks(match_id):
    url = f"https://api.sofascore.com/api/v1/event/{match_id}/team-events-streaks"
    try:
        r = requests.get(url, headers=HEADERS, impersonate="chrome120", timeout=12)
        if r.status_code == 200:
            data = r.json()
            streaks = []
            for cat in ['general', 'home', 'away']:
                for item in data.get(cat, []):
                    name = item.get("name", "")
                    value = item.get("value", "")
                    if name:
                        streaks.append(f"{name}: **{value}**")
            return streaks
    except Exception:
        pass
    return []

if st.button("🔎 Caută Meciuri & Streaks"):
    with st.spinner("Se preiau datele direct de pe SofaScore..."):
        events = obtine_meciuri(data_target)
        if events:
            st.success(f"S-au găsit {len(events)} meciuri în total!")
            
            # Luăm primele 25 de meciuri
            meciuri_procesate = 0
            for ev in events[:25]:
                match_id = ev.get("id")
                gazda = ev.get("homeTeam", {}).get("name", "Gazdă")
                oaspete = ev.get("awayTeam", {}).get("name", "Oaspete")
                liga = ev.get("tournament", {}).get("name", "Competiție")
                
                ts = ev.get("startTimestamp", 0)
                ora = datetime.fromtimestamp(ts).strftime('%H:%M') if ts else "--:--"
                
                streaks = obtine_streaks(match_id)
                
                with st.expander(f"⏰ {ora} | {liga} — {gazda} vs {oaspete}"):
                    if streaks:
                        st.write("🔥 **Serii statistice (Streaks):**")
                        for s in streaks:
                            st.markdown(f"- {s}")
                    else:
                        st.write("Nu există serii speciale (streaks) raportate pentru acest meci.")
                meciuri_procesate += 1
        else:
            st.warning("SofaScore nu a returnat niciun meci. Verifică dacă data este corectă sau încearcă din nou.")
