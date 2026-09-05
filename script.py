import os
import re
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")


def obtenir_meteo():
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://www.meteociel.fr/obs/classement.php?all=1&u2=1"

    response = requests.get(url, headers=headers)
    response.encoding = "iso-8859-1"
    soup = BeautifulSoup(response.text, "html.parser")

    villes_temps = []

    # Extraction des couples (Ville, Température)
    for ligne in soup.find_all("tr"):
        cols = ligne.find_all("td")
        if len(cols) >= 2:
            txt = " ".join([c.get_text(strip=True) for c in cols])
            match = re.search(
                r"([A-Za-zÀ-ÿ0-9\s\'\-\(\)\.]+?)\s*(-?\d+[\.,]\d+)\s*°C", txt
            )
            if match:
                ville = match.group(1).strip()
                temp = float(match.group(2).replace(",", "."))
                villes_temps.append((ville, temp))

    if not villes_temps:
        print("Aucune donnée trouvée.")
        return

    # Tri pour obtenir le max et le min
    villes_temps.sort(key=lambda x: x[1])
    ville_min, temp_min = villes_temps[0]
    ville_max, temp_max = villes_temps[-1]

    msg = (
        f"🌡️ **Extrêmes Météo France**\n"
        f"🔥 **Max :** {temp_max} °C à {ville_max}\n"
        f"❄️ **Min :** {temp_min} °C à {ville_min}"
    )

    requests.post(WEBHOOK_URL, json={"content": msg})


if __name__ == "__main__":
    obtenir_meteo()
