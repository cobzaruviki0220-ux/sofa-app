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

st.title("⚽ SofaScore Streaks")
st.write("Scanare meciuri pe 3 zile")

azi = datetime.now()
optiuni_zile = {
    f"Azi ({azi.strftime('%d.%m')})": azi.strftime('%Y-%m-%d'),
    f"Mâine ({(azi + timedelta(days=1)).strftime('%d.%m')})": (azi + timedelta(days=1)).strftime('%Y-%m-%d'),
    f"Poimâine ({(azi + timedelta(days=2)).strftime('%d.%m')})": (azi + timedelta(days=2)).strftime('%Y-%m-%d')
}

zi_selectata = st.selectbox("Alege ziua:", list(optiuni_zile.keys()))
data_target = optiuni_zile[zi_selectata]

async def extrage_streaks(data_str):
    os.system("playwright install chromium")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1")
        page = await context.new_page()
        
        url = f"https://www.sofascore.com/football/{data_str}"
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        meciuri = []
        elements = await page.query_selector_all('a[href*="/match/"]')
        for el in elements:
            text = await el.inner_text()
            if text and "\n" in text:
                linii = [l.strip() for l in text.split("\n") if l.strip()]
                if len(linii) >= 2:
                    meciuri.append({"Echipa 1": linii[0], "Echipa 2": linii[1]})
        
        await browser.close()
        return meciuri

if st.button("🔎 Caută Meciuri"):
    with st.spinner("Se accesează SofaScore și se procesează meciurile..."):
        try:
            meciuri = asyncio.run(extrage_streaks(data_target))
            if meciuri:
                st.success(f"Am găsit {len(meciuri)} meciuri!")
                for m in meciuri[:15]:
                    st.write(f"⚽ **{m['Echipa 1']}** vs **{m['Echipa 2']}**")
            else:
                st.warning("Nu s-au găsit meciuri sau SofaScore a blocat cererea.")
        except Exception as e:
            st.error(f"Eroare la extragere: {e}")
