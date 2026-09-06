import os
import re
import time
from datetime import datetime
import zoneinfo
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")


def attendre_minute_cible(minute_cible=13):
    """Attend la minute cible si le script a démarré trop tôt."""
    tz = zoneinfo.ZoneInfo("Europe/Paris")
    maintenant = datetime.now(tz)

    if maintenant.minute < minute_cible:
        secondes_a_attendre = (minute_cible - maintenant.minute) * 60 - maintenant.second
        print(f"Démarrage anticipé ({maintenant.strftime('%Hh%M')}). Pause de {secondes_a_attendre}s jusqu'à {minute_cible} min...")
        time.sleep(secondes_a_attendre)


def obtenir_meteo():
    # Attente pour s'assurer que Météociel a fini de mettre à jour ses données
    attendre_minute_cible(13)

    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://www.meteociel.fr/obs/classement.php?all=1&u2=1&ma=1500"

    response = requests.get(url, headers=headers)
    response.encoding = "iso-8859-1"
    soup = BeautifulSoup(response.text, "html.parser")

    villes_dict = {}

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
                    if nom_station not in villes_dict:
                        villes_dict[nom_station] = temp

    if not villes_dict:
        print("Aucune donnée météo valide trouvée.")
        return

    # Tri global des températures
    villes_temps = list(villes_dict.items())
    villes_temps.sort(key=lambda x: x[1])

    # Top 5 des plus froides : inversé pour aller du moins froid au plus froid
    top5_min = sorted(villes_temps[:5], key=lambda x: x[1], reverse=True)
    
    # Top 5 des plus chaudes : du plus chaud au moins chaud
    top5_max = sorted(villes_temps[-5:], key=lambda x: x[1], reverse=True)

    txt_max = "\n".join([f"{t:.1f} °C à {v}" for v, t in top5_max])
    txt_min = "\n".join([f"{t:.1f} °C à {v}" for v, t in top5_min])

    # Formatage de l'heure pile (ex: 12h)
    heure_pile = datetime.now(zoneinfo.ZoneInfo("Europe/Paris")).strftime("%Hh")

    message = (
        f"🔥 **Température maximale à {heure_pile} :**\n"
        f"{txt_max}\n\n"
        f"❄️ **Température minimale à {heure_pile} :**\n"
        f"{txt_min}"
    )

    requests.post(WEBHOOK_URL, json={"content": message})


if __name__ == "__main__":
    obtenir_meteo()
