def generate_report(ilanlar: list, kriter: dict) -> str:
    if not ilanlar:
        return "❌ İlan bulunamadı."

    tip_map = {"kiralik": "Kiralık", "satilik": "Satılık", "her": "Kiralık & Satılık"}
    tip = tip_map.get(kriter.get("tip", ""), "")
    semt = kriter.get("semt", "Tüm Bakü")
    min_f = kriter.get("min_fiyat", 0)
    max_f = kriter.get("max_fiyat", 99999)
    oda = kriter.get("oda", "0")

    oda_text = f"{oda} otaqlı" if oda != "0" else "Tüm odalar"
    fiyat_text = f"{min_f} - {max_f} AZN" if max_f < 99999 else f"{min_f}+ AZN"

    fiyatlar = [i["fiyat_num"] for i in ilanlar if i.get("fiyat_num", 0) > 0]
    ort_fiyat = int(sum(fiyatlar) / len(fiyatlar)) if fiyatlar else 0
    min_fiyat = min(fiyatlar) if fiyatlar else 0
    max_fiyat_gercek = max(fiyatlar) if fiyatlar else 0

    rapor = f"""📊 *EMLAK ANALİZ RAPORU*
━━━━━━━━━━━━━━━━━━━━
🏙️ Bölge: *{semt}*
🏠 Tip: *{tip}*
🚪 Oda: *{oda_text}*
💰 Bütçe: *{fiyat_text}*
━━━━━━━━━━━━━━━━━━━━
📈 *FİYAT ANALİZİ*
- En düşük: *{min_fiyat} AZN*
- Ortalama: *{ort_fiyat} AZN*
- En yüksek: *{max_fiyat_gercek} AZN*
━━━━━━━━━━━━━━━━━━━━
🔍 *{len(ilanlar)} İLAN BULUNDU*\n\n"""

    for i, ilan in enumerate(ilanlar[:10], 1):
        rapor += f"*{i}. {ilan.get('baslik', 'Mənzil')}*\n"
        rapor += f"   💰 {ilan.get('fiyat', '-')} | 📍 {ilan.get('adres', '-')}\n"
        if ilan.get('alan'):
            rapor += f"   📐 {ilan.get('alan')}\n"
        rapor += f"   🔗 [İlana git]({ilan.get('link', 'https://bina.az')})\n\n"

    rapor += "━━━━━━━━━━━━━━━━━━━━\n"
    rapor += "🔔 /bildirim - Fiyat düşüşü bildirimi\n"
    rapor += "🔍 /ara - Yeni arama yap"

    return rapor
