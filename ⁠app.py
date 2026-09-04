import streamlit as st
from datetime import datetime, timedelta
import asyncio
from playwright.async_api import async_playwright

st.set_page_config(page_title="SofaStreaks", page_icon="⚽", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; background-color: #007AFF; color: white; }
    div[data-testid="stExpander"] { border-radius: 10px; background-color: #f8f9fa; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ SofaScore Streaks")
st.write("Scanare meciuri pe 3 zile")

azi = datetime.now()
optiuni_zile = {
    f"Azi ({azi.strftime('%d.%m')})": azi.strftime('%Y-%m-%d'),
    f"Mâine ({(azi + timedelta(days=1)).strftime('%d.%m')})": (azi + timedelta(days=1)).strftime('%Y-%m-%d'),
    f"Poimâine ({(azi + timedelta(days=2)).strftime('%d.%m')})": (azi + timedelta(days=2)).strftime('%Y-%m-%d')
}

zi_selectata = st.radio("Alege ziua:", list(optiuni_zile.keys()), horizontal=True)
data_target = optiuni_zile[zi_selectata]

async def extrage_streaks(data_str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
        )
        page = await context.new_page()
        
        await page.goto(f"https://www.sofascore.com/football/{data_str}", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        
        links = await page.eval_on_selector_all('a[href*="/match/"]', 'elements => elements.map(e => e.getAttribute("href"))')
        match_ids = list(set([l.split('/')[-1] for l in links if l and l.split('/')[-1].isdigit()]))
        
        rezultate = []
        for m_id in match_ids[:20]: 
            api_url = f"https://api.sofascore.com/api/v3/event/{m_id}/streaks"
            res = await page.evaluate(f'async () => {{ let r = await fetch("{api_url}"); return r.status === 200 ? await r.json() : null; }}')
            if res and 'general' in res:
                rezultate.append({"id": m_id, "streaks": res['general']})
                
        await browser.close()
        return rezultate

if st.button("🔎 Caută Meciuri", use_container_width=True):
    with st.spinner(f"Se analizează meciurile..."):
        meciuri = asyncio.run(extrage_streaks(data_target))
        
        if not meciuri:
            st.warning("Nu s-au găsit date sau serverul a fost blocat temporar.")
        else:
            for meci in meciuri:
                with st.expander(f"🏟️ Meci ID: {meci['id']}"):
                    for s in meci['streaks']:
                        nume = s.get('name', '')
                        val = s.get('value', '')
                        
                        if any(k in nume for k in ["Both teams", "Over 2.5", "Without a win", "Conceded"]):
                            st.markdown(f"🔥 **{nume}**: `{val}`")
                        else:
                            st.write(f"• {nume}: {val}")
