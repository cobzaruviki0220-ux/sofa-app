import streamlit as st
from datetime import datetime, timedelta
import json
import urllib.parse
from curl_cffi import requests

# Configurare pagină Streamlit
st.set_page_config(page_title="SofaStreaks", page_icon="⚽", layout="wide")

st.markdown("""
<style>
.stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #007AFF; color: white; font-weight: bold; }
div[data-testid="stExpander"] { border-radius: 8px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ SofaScore Streaks Tracker")
st.write("Scanare avansată meciuri și serii statistice (Streaks)")

# Selectare dată
azi = datetime.now()
optiuni_zile = {
    f"Azi ({azi.strftime('%d.%m')})": azi.strftime('%Y-%m-%d'),
    f"Mâine ({(azi + timedelta(days=1)).strftime('%d.%m')})": (azi + timedelta(days=1)).strftime('%Y-%m-%d'),
    f"Poimâine ({(azi + timedelta(days=2)).strftime('%d.%m')})": (azi + timedelta(days=2)).strftime('%Y-%m-%d')
}

zi_selectata = st.selectbox("Alege ziua:", list(optiuni_zile.keys()))
data_target = optiuni_zile[zi_selectata]

# Antete complete pentru mimarea unui browser real
HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

def cerere_multi_fallback(url_target):
    """
    Execută cererea prin 3 metode consecutive pentru a garanta trecerea de protecțiile anti-bot:
    1. Direct prin curl_cffi (impersonate Chrome)
    2. Proxy public AllOrigins
    3. Proxy public CorsProxy.io
    """
    # Metoda 1: Direct cu curl_cffi
    try:
        r = requests.get(url_target, headers=HEADERS_BROWSER, impersonate="chrome120", timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    # Metoda 2: Proxy AllOrigins
    try:
        encoded_url = urllib.parse.quote(url_target)
        proxy_url = f"https://api.allorigins.win/get?url={encoded_url}"
        r = requests.get(proxy_url, timeout=10)
        if r.status_code == 200:
            raw_contents = r.json().get('contents')
            if raw_contents:
                return json.loads(raw_contents)
    except Exception:
        pass

    # Metoda 3: Proxy CorsProxy
    try:
        proxy_url = f"https://corsproxy.io/?{urllib.parse.quote(url_target)}"
        r = requests.get(proxy_url, headers=HEADERS_BROWSER, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    return None

def obtine_meciuri(data_str):
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{data_str}"
    data = cerere_multi_fallback(url)
    if data and isinstance(data, dict):
        return data.get("events", [])
    return []

def obtine_streaks(match_id):
    url = f"https://api.sofascore.com/api/v1/event/{match_id}/team-events-streaks"
    data = cerere_multi_fallback(url)
    streaks_gasite = []
    
    if data and isinstance(data, dict):
        for categorie in ['general', 'home', 'away']:
            grup_streaks = data.get(categorie, [])
            if isinstance(grup_streaks, list):
                for item in grup_streaks:
                    nume = item.get("name", "")
                    valoare = item.get("value", "")
                    if nume:
                        streaks_gasite.append(f"{nume}: **{valoare}**")
    return streaks_gasite

# Execuție la apăsarea butonului
if st.button("🔎 Caută Meciuri & Streaks"):
    with st.spinner("Se interoghează sursele de date SofaScore..."):
        evenimente = obtine_meciuri(data_target)
        
        if evenimente:
            st.success(f"S-au identificat {len(evenimente)} meciuri pentru data selectată!")
            
            # Afișăm primele 20 de meciuri
            for ev in evenimente[:20]:
                try:
                    match_id = ev.get("id")
                    gazda = ev.get("homeTeam", {}).get("name", "N/A")
                    oaspete = ev.get("awayTeam", {}).get("name", "N/A")
                    liga = ev.get("tournament", {}).get("name", "Competiție")
                    
                    timestamp = ev.get("startTimestamp", 0)
                    ora = datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else "--:--"
                    
                    streaks = obtine_streaks(match_id) if match_id else []
                    
                    with st.expander(f"⏰ {ora} | {liga} — {gazda} vs {oaspete}"):
                        if streaks:
                            st.write("🔥 **Serii statistice (Streaks):**")
                            for s in streaks:
                                st.markdown(f"- {s}")
                        else:
                            st.info("Nu există serii statistice raportate pentru acest meci.")
                except Exception:
                    continue
        else:
            st.error("Toate căile de conexiune au fost temporar blocate sau nu există meciuri programate. Încearcă din nou în câteva momente.")
