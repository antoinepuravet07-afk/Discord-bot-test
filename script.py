import os
import re
from datetime import datetime
import zoneinfo
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")


def obtenir_meteo():
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://www.meteociel.fr/obs/classement.php?all=1&u2=1&ma=1500"

    response = requests.get(url, headers=headers)
    response.encoding = "iso-8859-1"
    soup = BeautifulSoup(response.text, "html.parser")

    villes_dict = {}

    # Extraction des couples (Station, Température)
    for table in soup.find_all("table"):
        for ligne in table.find_all("tr"):
            cols = ligne.find_all("td")
            if len(cols) >= 2:
                nom_station = cols[0].get_text(strip=True)
                val_brute = cols[1].get_text(strip=True)

                match_temp = re.search(r"(-?\d{1,2}[\.,]\d+)\s*°C", val_brute)

                if (
                    match_temp
                    and 3 <= len(nom_station) <= 45
                    and not any(
                        m in nom_station
                        for m in ["ARPEGE", "ICON", "GFS", "Sondages", "Prévisions"]
                    )
                ):
                    temp = float(match_temp.group(1).replace(",", "."))
                    # Filtrage des doublons de station
                    if nom_station not in villes_dict:
                        villes_dict[nom_station] = temp

    if not villes_dict:
        print("Aucune donnée météo valide trouvée.")
        return

    # Tri par température
    villes_temps = list(villes_dict.items())
    villes_temps.sort(key=lambda x: x[1])

    # Top 5 des plus froides (distinctes)
    top5_min = villes_temps[:5]
    # Top 5 des plus chaudes (distinctes, plus chaude en premier)
    top5_max = sorted(villes_temps[-5:], key=lambda x: x[1], reverse=True)

    txt_max = "\n".join([f"{t:.1f} °C à {v}" for v, t in top5_max])
    txt_min = "\n".join([f"{t:.1f} °C à {v}" for v, t in top5_min])

    # Heure actuelle au format HHhMM (Heure de Paris)
    heure_actuelle = datetime.now(zoneinfo.ZoneInfo("Europe/Paris")).strftime("%HH%M")

    # Mise en forme du message Discord
    message = (
        f":fire: **Température maximale à {heure_actuelle} :**\n"
        f"{txt_max}\n\n"
        f":snowflake: **Température minimale à {heure_actuelle} :**\n"
        f"{txt_min}"
    )

    requests.post(WEBHOOK_URL, json={"content": message})


if __name__ == "__main__":
    obtenir_meteo()
