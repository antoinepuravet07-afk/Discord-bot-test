import os
import time
from datetime import datetime
import zoneinfo
import requests
from bs4 import BeautifulSoup
import re

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def attendre_minute_cible(minute_cible):
    maintenant = datetime.now(zoneinfo.ZoneInfo("Europe/Paris"))
    if maintenant.minute < minute_cible:
        attente = (minute_cible - maintenant.minute) * 60 - maintenant.second
        if attente > 0:
            print(f"⏳ Attente de {attente} secondes pour atteindre la minute {minute_cible}...")
            time.sleep(attente)

def obtenir_meteo():
    print("-> Début de la fonction obtenir_meteo()")
    
    attendre_minute_cible(13)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    url = "https://www.meteociel.fr/obs/classement.php?all=1&u2=1&ma=800"

    max_retries = 3
    response = None

    for tentative in range(1, max_retries + 1):
        print(f"-> Connexion à l'URL (tentative {tentative}/{max_retries})...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                print("-> Succès ! Page récupérée avec succès.")
                break
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            print(f"⚠️ Échec de la tentative {tentative} : {e}")
            if tentative < max_retries:
                print("⏳ Pause de 10 secondes avant de réitérer...")
                time.sleep(10)

    if not response or response.status_code != 200:
        print("❌ Impossible de récupérer les données Météociel après plusieurs tentatives.")
        return

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
        print("❌ Aucune donnée météo valide trouvée.")
        return

    print(f"-> {len(villes_dict)} stations valides trouvées. Tri en cours...")

    villes_temps = list(villes_dict.items())
    villes_temps.sort(key=lambda x: x[1])

    top5_min = sorted(villes_temps[:5], key=lambda x: x[1], reverse=True)
    top5_max = sorted(villes_temps[-5:], key=lambda x: x[1], reverse=True)

    txt_max = "\n".join([f"{t:.1f} °C à {v}" for v, t in top5_max])
    txt_min = "\n".join([f"{t:.1f} °C à {v}" for v, t in top5_min])

    heure_pile = datetime.now(zoneinfo.ZoneInfo("Europe/Paris")).strftime("%Hh")

    message = (
        f"🔥 **Température maximale à {heure_pile} :**\n"
        f"{txt_max}\n\n"
        f"❄️ **Température minimale à {heure_pile} :**\n"
        f"{txt_min}"
    )

    print("-> Envoi du message sur le webhook Discord...")
    res_discord = requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
    print(f"-> Statut de l'envoi Discord : {res_discord.status_code}")

if __name__ == "__main__":
    obtenir_meteo()
