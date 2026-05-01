# pip install playwright pandas
# playwright install

import random, time
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

N = 10  # número de observaciones

def safe_text(page, selector):
    try:
        return page.locator(selector).first.inner_text(timeout=3000)
    except:
        return None


def get_featured_item(page):
    try:
        section = page.locator("//h3[normalize-space()='Artículos destacados']")

        if section.count() == 0:
            return None, None

        first_item = page.locator(
            "//h3[normalize-space()='Artículos destacados']/following::li[1]"
        )

        spans = first_item.locator("span").all()

        item_name = None
        item_price = None

        for s in spans:
            text = s.inner_text().strip()

            if not text:
                continue

            # 🔥 ignorar basura
            if any(x in text.lower() for x in [
                "favoritos", "%", "•"
            ]):
                continue

            # precio
            if "$" in text and len(text) < 15:
                item_price = text

            # nombre (más limpio ahora)
            elif "$" not in text and 3 < len(text) < 60:
                item_name = text

            if item_name and item_price:
                break

        return item_name, item_price

    except:
        return None, None



def get_eta(page):
    try:
        return page.locator(
            "//p[.//span[contains(text(),'Llegada más temprana')]]/preceding-sibling::p[1]//span"
        ).inner_text(timeout=3000)
    except:
        return None

def get_restaurant_name(page):
    try:
        return page.locator("h1").first.inner_text()
    except:
        return None

def get_address(page):
    try:
        return page.locator(
            "//p[.//a[contains(text(),'Información')]]/following-sibling::p[1]//span"
        ).inner_text(timeout=3000)
    except:
        return None


def main():
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # visible para tu video-evidencia
        context = browser.new_context(locale="es-MX")
        page = context.new_page()

        # 1) Abre Uber Eats y fija una dirección manualmente en la UI
        page.goto("https://www.ubereats.com/", wait_until="domcontentloaded")
        input("Configura tu dirección en la página y presiona ENTER...")

        # 2) Captura lista de restaurantes visibles
        page.wait_for_timeout(4000)
        cards = page.locator("a[href*='/store/']").all()

        BASE = "https://www.ubereats.com"

        links = []
        for c in cards:
            href = c.get_attribute("href")
            if href:
                if href.startswith("/"):
                    href = BASE + href
                links.append(href)

        # eliminar duplicados
        links = list(set(links))

        # filtrar solo restaurantes (opcional pero recomendado)
        links = [l for l in links if "/store/" in l]

        # ahora sí mezclar
        random.shuffle(links)

        i = 0  # contador de observaciones válidas

        while i < N:
            if not links:
                break

            link = random.choice(links)
            page.goto(link, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)

            eta = get_eta(page)
            restaurant_name = get_restaurant_name(page)
            address = get_address(page)
            item_name, item_price = get_featured_item(page)

            if item_name is None or item_price is None:
                print("⏭️ Sin platillo válido, ignorando...")
                continue  # NO incrementa i

            rows.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "eta_text": eta,
                "sample_item_name_text": item_name,
                "sample_item_price_text": item_price,
                "restaurant_name_text": restaurant_name,
                "address_text": address
            })

            i += 1  # ✅ solo cuenta si es válido

            print(f"""
            ===== OBSERVACIÓN {i} =====
            Restaurante: {restaurant_name}
            Direccion: {address}
            ETA: {eta}
            Platillo destacado: {item_name}
            Precio: {item_price}
            Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            ============================
            """)

            time.sleep(random.uniform(2, 5))


        browser.close()

    df = pd.DataFrame(rows)
    df.to_csv("ubereats_dataset_raw.csv", index=False)
    print("Guardado en ubereats_dataset_raw.csv")

if __name__ == "__main__":
    main()
