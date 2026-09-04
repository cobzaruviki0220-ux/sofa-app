import streamlit as st
from datetime import datetime, timedelta
import requests
import json
import urllib.parse

st.set_page_config(page_title="SofaStreaks", page_icon="⚽", layout="wide")

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

def fetch_data(endpoint):
    target_url = f"https://api.sofascore.com/api/v1/{endpoint}"
    
    # 3 proxy-uri diferite prin care încercăm să ocolim blocajul
    proxies = [
        f"https://api.allorigins.win/raw?url={urllib.parse.quote(target_url)}",
        f"https://corsproxy.io/?{urllib.parse.quote(target_url)}",
        f"https://api.codetabs.com/v1/proxy?quest={urllib.parse.quote(target_url)}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    for p_url in proxies:
        try:
            res = requests.get(p_url, headers=headers, timeout=6)
            if res.status_code == 200 and res.text:
                # Verificăm dacă e JSON valid
                data = res.json()
                if data:
                    return data
        except Exception:
            continue
    return None

if st.button("🔎 Caută Meciuri & Streaks"):
    with st.spinner("Se interoghează serverele prin rute alternative..."):
        data_meciuri = fetch_data(f"sport/football/scheduled-events/{data_target}")
        
        if data_meciuri and "events" in data_meciuri:
            meciuri = data_meciuri["events"]
            st.success(f"S-au găsit {len(meciuri)} meciuri!")
            
            for ev in meciuri[:15]:
                match_id = ev.get("id")
                gazda = ev.get("homeTeam", {}).get("name", "N/A")
                oaspete = ev.get("awayTeam", {}).get("name", "N/A")
                liga = ev.get("tournament", {}).get("name", "Competiție")
                
                ts = ev.get("startTimestamp", 0)
                ora = datetime.fromtimestamp(ts).strftime('%H:%M') if ts else "--:--"
                
                data_streaks = fetch_data(f"event/{match_id}/team-events-streaks")
                streaks = []
                if data_streaks:
                    for cat in ['general', 'home', 'away']:
                        for item in data_streaks.get(cat, []):
                            nume = item.get("name")
                            val = item.get("value")
                            if nume:
                                streaks.append(f"{nume}: **{val}**")
                
                with st.expander(f"⏰ {ora} | {liga} — {gazda} vs {oaspete}"):
                    if streaks:
                        st.write("🔥 **Serii statistice (Streaks):**")
                        for s in streaks:
                            st.markdown(f"- {s}")
                    else:
                        st.write("Nu există serii speciale raportate.")
        else:
            st.error("Toate rutele alternative sunt momentan blocate de SofaScore. Încearcă din nou peste câteva minute.")
