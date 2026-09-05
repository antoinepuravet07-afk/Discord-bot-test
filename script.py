import os
import re
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")


def Obtenir_meteo():
    headers = {"User-Agent": "Mozilla/5.0"}

    # Maxima
    r_max = requests.get(
        "https://www.meteociel.fr/obs/classement.php?all=1&mode=25",
        headers=headers,
    )
    r_max.encoding = "iso-8859-1"
    soup_max = BeautifulSoup(r_max.text, "html.parser")

    # Minima
    r_min = requests.get(
        "https://www.meteociel.fr/obs/classement.php?all=1&mode=26",
        headers=headers,
    )
    r_min.encoding = "iso-8859-1"
    soup_min = BeautifulSoup(r_min.text, "html.parser")

    def extraire(soup):
        for ligne in soup.find_all("tr"):
            cols = ligne.find_all("td")
            if len(cols) >= 3:
                txt = " ".join([c.get_text(strip=True) for c in cols])
                m = re.search(
                    r"([A-Za-zÀ-ÿ0-9\s\'\-\(\)\.]+?)\s*(-?\d+[\.,]\d+)\s*°C", txt
                )
                if m:
                    return m.group(1).strip(), m.group(2).replace(",", ".")
        return "Inconnu", "N/A"

    v_max, t_max = extraire(soup_max)
    v_min, t_min = extraire(soup_min)

    msg = f"🌡️ **Météo France (Extrêmes)**\n🔥 Max : **{t_max} °C** à {v_max}\n❄️ Min : **{t_min} °C** à {v_min}"
    requests.post(WEBHOOK_URL, json={"content": msg})


if __name__ == "__main__":
    Obtenir_meteo()
