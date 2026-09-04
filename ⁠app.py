import streamlit as st
from datetime import datetime, timedelta
import asyncio
from playwright.async_api import async_playwright
import os

st.set_page_config(page_title="SofaStreaks", page_icon="⚽", layout="wide")

st.markdown("""
<style>
.stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #007AFF; color: white; }
div[data-testid="stExpander"] { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ SofaScore Streaks Tracker")
st.write("Scanare meciuri și serii statistice în timp real")

azi = datetime.now()
optiuni_zile = {
    f"Azi ({azi.strftime('%d.%m')})": azi.strftime('%Y-%m-%d'),
    f"Mâine ({(azi + timedelta(days=1)).strftime('%d.%m')})": (azi + timedelta(days=1)).strftime('%Y-%m-%d'),
    f"Poimâine ({(azi + timedelta(days=2)).strftime('%d.%m')})": (azi + timedelta(days=2)).strftime('%Y-%m-%d')
}

zi_selectata = st.selectbox("Alege ziua:", list(optiuni_zile.keys()))
data_target = optiuni_zile[zi_selectata]

async def extrage_streaks_playwright(data_str):
    os.system("playwright install chromium")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            viewport={'width': 390, 'height': 844}
        )
        page = await context.new_page()
        
        # Deschidem pagina principală pentru a stabili cookie-urile valide
        await page.goto(f"https://www.sofascore.com/football/{data_str}", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Preluăm lista meciurilor prin fetch efectuat de browser
        events_json = await page.evaluate(f"""
            async () => {{
                try {{
                    const res = await fetch('https://api.sofascore.com/api/v1/sport/football/scheduled-events/{data_str}');
                    return await res.json();
                }} catch (e) {{
                    return {{ events: [] }};
                }}
            }}
        """)
        
        events = events_json.get("events", [])
        meciuri_rezultat = []
        
        # Procesăm meciurile găsite
        for ev in events[:15]:
            match_id = ev.get("id")
            gazda = ev.get("homeTeam", {}).get("name", "N/A")
            oaspete = ev.get("awayTeam", {}).get("name", "N/A")
            liga = ev.get("tournament", {}).get("name", "Competiție")
            ora = datetime.fromtimestamp(ev.get("startTimestamp", 0)).strftime('%H:%M')
            
            # Preluăm seriile statistice pentru meciul curent
            streaks_json = await page.evaluate(f"""
                async () => {{
                    try {{
                        const res = await fetch('https://api.sofascore.com/api/v1/event/{match_id}/team-events-streaks');
                        return await res.json();
                    }} catch (e) {{
                        return {{}};
                    }}
                }}
            """)
            
            lista_streaks = []
            for category in ['general', 'home', 'away']:
                for item in streaks_json.get(category, []):
                    name = item.get("name", "")
                    value = item.get("value", "")
                    if name:
                        lista_streaks.append(f"{name}: **{value}**")
            
            meciuri_rezultat.append({
                "ora": ora,
                "liga": liga,
                "gazda": gazda,
                "oaspete": oaspete,
                "streaks": lista_streaks
            })
            
        await browser.close()
        return meciuri_rezultat

if st.button("🔎 Caută Meciuri & Streaks"):
    with st.spinner("Se preiau meciurile și seriile statistice de pe SofaScore..."):
        try:
            meciuri = asyncio.run(extrage_streaks_playwright(data_target))
            if meciuri:
                st.success(f"Am găsit {len(meciuri)} meciuri!")
                for m in meciuri:
                    with st.expander(f"⏰ {m['ora']} | {m['liga']} — {m['gazda']} vs {m['oaspete']}"):
                        if m['streaks']:
                            st.write("🔥 **Serii statistice (Streaks):**")
                            for s in m['streaks']:
                                st.markdown(f"- {s}")
                        else:
                            st.write("Nu există serii speciale raportate pentru acest meci.")
            else:
                st.warning("Nu s-au putut prelua meciurile. Reîncearcă în câteva momente.")
        except Exception as e:
            st.error(f"Eroare întâmpinată: {e}")
