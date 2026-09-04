import streamlit as st
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Football Scores & Live", page_icon="⚽", layout="wide")

st.title("⚽ Fotbal Live & Program")
st.write("Scoruri și program meciuri prin surse alternative stabile")

# Selectare campionat
leagues = {
    "Premier League (Anglia)": "eng.1",
    "Serie A (Italia)": "ita.1",
    "La Liga (Spania)": "esp.1",
    "Champions League": "uefa.champions",
    "Bundesliga (Germania)": "ger.1"
}

liga_nume = st.selectbox("Alege competiția:", list(leagues.keys()))
liga_id = leagues[liga_nume]

azi = datetime.now()
optiuni_zile = {
    f"Azi ({azi.strftime('%d.%m')})": azi.strftime('%Y%m%d'),
    f"Mâine ({(azi + timedelta(days=1)).strftime('%d.%m')})": (azi + timedelta(days=1)).strftime('%Y%m%d'),
    f"Ieri ({(azi - timedelta(days=1)).strftime('%d.%m')})": (azi - timedelta(days=1)).strftime('%Y%m%d')
}

zi_selectata = st.selectbox("Alege ziua:", list(optiuni_zile.keys()))
data_target = optiuni_zile[zi_selectata]

def fetch_espn(league, date_str):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={date_str}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

if st.button("🔎 Caută Meciuri"):
    with st.spinner("Se preiau datele..."):
        data = fetch_espn(liga_id, data_target)
        events = data.get("events", []) if data else []
        
        if events:
            st.success(f"S-au găsit {len(events)} meciuri pentru {liga_nume}!")
            
            for ev in events:
                competitors = ev.get("competitions", [{}])[0].get("competitors", [])
                home_team, away_team = "Gazdă", "Oaspete"
                home_score, away_score = "-", "-"
                
                for comp in competitors:
                    if comp.get("homeAway") == "home":
                        home_team = comp.get("team", {}).get("displayName", "Gazdă")
                        home_score = comp.get("score", "0")
                    else:
                        away_team = comp.get("team", {}).get("displayName", "Oaspete")
                        away_score = comp.get("score", "0")
                
                status_type = ev.get("status", {}).get("type", {}).get("description", "Programat")
                clock = ev.get("status", {}).get("displayClock", "")
                
                detalii_stare = f"{status_type}"
                if clock and status_type != "FT":
                    detalii_stare = f"Minutul: {clock}"

                with st.expander(f"⚽ {home_team} {home_score} - {away_score} {away_team} [{detalii_stare}]"):
                    st.write(ul := f"Stare meci: **{status_type}**")
                    st.write(f"Competiție: {liga_nume}")
        else:
            st.warning("Nu s-au găsit meciuri programate pentru data și competiția selectată.")
