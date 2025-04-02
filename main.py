import requests
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

BOT_TOKEN = "7346851027:AAGrhGtOp_ZvSR89r3n--sFYy96ha9kmMFk"
CHAT_ID = "812555723"
VAULT_URL = "https://app.beefy.com/vault/velodrome-v2-msusd-usdce"
INVESTED_AMOUNT = 425.29

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, data=data)

async def extraer_datos():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        await page.goto(VAULT_URL, timeout=60000)
        await page.wait_for_selector("text=TVL", timeout=60000)
        try:
            tvl = await page.locator("[data-testid='tvl']").text_content()
            apy = await page.locator("[data-testid='apy']").text_content()
            daily = await page.locator("[data-testid='daily']").text_content()
            harvest = await page.locator("text=Last Harvest")
            harvest_text = await harvest.locator("xpath=..//following-sibling::*[1]").text_content()
        except:
            await browser.close()
            return None
        await browser.close()
        return {
            "tvl": tvl.strip(),
            "apy": apy.strip(),
            "daily": daily.strip(),
            "harvest": harvest_text.strip()
        }

async def monitorear_vault():
    datos = await extraer_datos()
    if not datos:
        enviar_telegram("⚠️ Sofía no pudo leer los datos del vault 😢")
        return
    try:
        apy_num = float(datos['apy'].replace('%', '').strip())
        rendimiento_dia = (apy_num / 100 / 365) * INVESTED_AMOUNT
        estado = "✅ Sofía dice que todo está bien 😎"
        if apy_num < 16 or "hour" in datos['harvest'] and float(datos['harvest'].split()[0]) > 4:
            estado = "⚠️ Sofía dice que estés pendiente 😐"
        if float(datos['tvl'].replace('$', '').replace(',', '')) < 110000:
            estado = "🚨 Sofía dice que hay que actuar YA 🔥"
    except:
        estado = "⚠️ Sofía no pudo procesar los datos"
        rendimiento_dia = 0
    mensaje = (
        f"{estado}\n"
        f"📊 *TVL:* {datos['tvl']}\n"
        f"💹 *APY:* {datos['apy']}\n"
        f"📆 *Daily:* {datos['daily']}\n"
        f"⛏️ *Último harvest:* {datos['harvest']}\n"
        f"📈 *Rendimiento estimado hoy:* ~${rendimiento_dia:.2f} 💵"
    )
    enviar_telegram(mensaje)

asyncio.run(monitorear_vault())