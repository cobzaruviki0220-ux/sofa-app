import streamlit as st
from datetime import datetime, timedelta
import requests

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

def get_via_proxy(url):
    proxy_url = f"https://api.allorigins.win/get?url={requests.utils.quote(url)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(proxy_url, headers=headers, timeout=15)
        if r.status_code == 200:
            import json
            contents = r.json().get('contents')
            if contents:
                return json.loads(contents)
    except Exception:
        pass
    
    # Fallback direct
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def obtine_meciuri(data_str):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{data_str}"
    data = get_via_proxy(url)
    if data:
        return data.get("events", [])
    return []

def obtine_streaks(match_id):
    url = f"https://api.sofascore.com/api/v1/event/{match_id}/team-events-streaks"
    data = get_via_proxy(url)
    if data:
        streaks = []
        for cat in ['general', 'home', 'away']:
            for item in data.get(cat, []):
                name = item.get("name", "")
                value = item.get("value", "")
                if name:
                    streaks.append(f"{name}: **{value}**")
        return streaks
    return []

if st.button("🔎 Caută Meciuri & Streaks"):
    with st.spinner("Se preiau datele prin tunel proxy securizat..."):
        events = obtine_meciuri(data_target)
        if events:
            st.success(f"Am găsit {len(events)} meciuri!")
            for ev in events[:15]:
                match_id = ev.get("id")
                gazda = ev.get("homeTeam", {}).get("name", "N/A")
                oaspete = ev.get("awayTeam", {}).get("name", "N/A")
                liga = ev.get("tournament", {}).get("name", "Competiție")
                ora = datetime.fromtimestamp(ev.get("startTimestamp", 0)).strftime('%H:%M')
                
                streaks = obtine_streaks(match_id)
                
                with st.expander(f"⏰ {ora} | {liga} — {gazda} vs {oaspete}"):
                    if streaks:
                        st.write("🔥 **Serii statistice (Streaks):**")
                        for s in streaks:
                            st.markdown(f"- {s}")
                    else:
                        st.write("Nu există serii speciale sau SofaScore nu le-a furnizat încă.")
        else:
            st.warning("Proxy-ul nu a putut conecta SofaScore în acest moment. Reîncearcă apăsând din nou butonul.")
