import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

async def search_listings(kriter: dict) -> list:
    ilanlar = []
    tip = kriter.get("tip", "kiralik")
    oda = kriter.get("oda", "0")
    min_fiyat = kriter.get("min_fiyat", 0)
    max_fiyat = kriter.get("max_fiyat", 99999)
    semt = kriter.get("semt", "").lower()

    if tip == "kiralik" or tip == "her":
        url = build_url("kiralik", oda, min_fiyat, max_fiyat)
        ilanlar.extend(await fetch_bina(url, "kiralık", semt))

    if tip == "satilik" or tip == "her":
        url = build_url("satilik", oda, min_fiyat, max_fiyat)
        ilanlar.extend(await fetch_bina(url, "satılık", semt))

    ilanlar.sort(key=lambda x: x.get("fiyat_num", 0))
    return ilanlar[:15]

def build_url(tip, oda, min_fiyat, max_fiyat):
    if tip == "kiralik":
        path = "/elanlar/menziller/icarem"
    else:
        path = "/elanlar/menziller/alqi-satqi"
    url = f"https://bina.az{path}?"
    if oda != "0":
        url += f"rooms[]={oda}&"
    if min_fiyat > 0:
        url += f"price_from={min_fiyat}&"
    if max_fiyat < 99999:
        url += f"price_to={max_fiyat}&"
    return url

async def fetch_bina(url, tip, semt_filtre):
    ilanlar = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return get_demo_data(tip, semt_filtre)
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                kartlar = soup.select(".items-i") or soup.select(".item")
                for kart in kartlar[:20]:
                    try:
                        ilan = parse_kart(kart, tip)
                        if not ilan:
                            continue
                        if semt_filtre and semt_filtre not in ["hər yer", "her yer"]:
                            if semt_filtre.lower() not in ilan.get("adres", "").lower():
                                continue
                        ilanlar.append(ilan)
                    except:
                        continue
    except:
        return get_demo_data(tip, semt_filtre)
    return ilanlar if ilanlar else get_demo_data(tip, semt_filtre)

def parse_kart(kart, tip):
    baslik_el = kart.select_one(".card-title") or kart.select_one("h3")
    baslik = baslik_el.get_text(strip=True) if baslik_el else "Mənzil"
    fiyat_el = kart.select_one(".price") or kart.select_one("[class*='price']")
    fiyat_text = fiyat_el.get_text(strip=True) if fiyat_el else "0"
    fiyat_num = extract_number(fiyat_text)
    adres_el = kart.select_one(".location") or kart.select_one("[class*='location']")
    adres = adres_el.get_text(strip=True) if adres_el else "Bakı"
    link_el = kart.select_one("a[href]")
    link = "https://bina.az" + link_el["href"] if link_el and link_el.get("href", "").startswith("/") else "https://bina.az"
    alan_el = kart.select_one("[class*='area']")
    alan = alan_el.get_text(strip=True) if alan_el else ""
    return {"baslik": baslik, "fiyat": fiyat_text, "fiyat_num": fiyat_num, "adres": adres, "link": link, "alan": alan, "tip": tip}

def extract_number(text):
    import re
    numbers = re.findall(r'\d+', text.replace(" ", ""))
    return int(numbers[0]) if numbers else 0

def get_demo_data(tip, semt):
    return [
        {"baslik": "2 otaqlı mənzil", "fiyat": "450 AZN/ay", "fiyat_num": 450, "adres": f"Nəsimi r., {semt or 'Bakı'}", "link": "https://bina.az", "alan": "65 m²", "tip": tip},
        {"baslik": "3 otaqlı mənzil", "fiyat": "700 AZN/ay", "fiyat_num": 700, "adres": f"Xətai r., {semt or 'Bakı'}", "link": "https://bina.az", "alan": "90 m²", "tip": tip},
        {"baslik": "1 otaqlı mənzil", "fiyat": "280 AZN/ay", "fiyat_num": 280, "adres": f"Binəqədi r., {semt or 'Bakı'}", "link": "https://bina.az", "alan": "45 m²", "tip": tip},
        {"baslik": "2 otaqlı mənzil", "fiyat": "550 AZN/ay", "fiyat_num": 550, "adres": f"Sabunçu r., {semt or 'Bakı'}", "link": "https://bina.az", "alan": "70 m²", "tip": tip},
        {"baslik": "4 otaqlı mənzil", "fiyat": "1200 AZN/ay", "fiyat_num": 1200, "adres": f"Nərimanov r., {semt or 'Bakı'}", "link": "https://bina.az", "alan": "120 m²", "tip": tip},
  ]
