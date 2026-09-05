import os
import re
import requests
from bs4 import BeautifulSoup

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")


def obtenir_meteo():
    headers = {"User-Agent": "Mozilla/5.0"}
    # Ton lien météociel
    url = "https://www.meteociel.fr/obs/classement.php?all=1&u2=1"

    response = requests.get(url, headers=headers)
    response.encoding = "iso-8859-1"
    soup = BeautifulSoup(response.text, "html.parser")

    villes_temps = []

    # Regex plus précise pour attraper une température réaliste
    regex_temp = r"(-?\d{1,2}[\.,]\d+)\s*°C"

    tables = soup.find_all("table")
    for table in tables:
        for ligne in table.find_all("tr"):
            cols = ligne.find_all("td")
            if len(cols) >= 2:
                # Récupération de la station et de la valeur brute
                nom_station = cols[0].get_text(strip=True)
                val_brute = cols[1].get_text(strip=True)

                # -- FILTRES DE NETTOYAGE STRICTS --
                # 1. Vérifie que c'est bien une température
                match_temp = re.search(regex_temp, val_brute)
                if not match_temp:
                    continue

                # 2. Vérifie la longueur du nom (vrai ville = 5 à 30 car.)
                len_nom = len(nom_station)
                if len_nom < 5 or len_nom > 30:
                    continue

                # 3. Vérifie les mots-clés parasites (ARPEGE, ICON, GFS...)
                mots_parasites = ["ARPEGE", "ICON", "GFS", "Sondages"]
                if any(mot in nom_station for mot in mots_parasites):
                    continue

                # 4. Vérifie que le nom n'est pas tout en majuscules (par ex: UN LIEU DIT)
                if nom_station.isupper() and len_nom > 15:
                   continue

                # Extraction propre de la valeur numérique
                try:
                    temp_float = float(match_temp.group(1).replace(",", "."))
                    # Filtre additionnel : température incohérente en canicule sept.
                    # (ex: moins de -5°C ou plus de 45°C)
                    if not (-5 < temp_float < 45):
                        continue
                    
                    villes_temps.append((nom_station, temp_float))
                except ValueError:
                    continue

    if not villes_temps:
        print("Aucune donnée météo fiable trouvée sur la page.")
        return

    # Tri pour obtenir la plus basse et la plus haute parmi les vraies villes
    villes_temps.sort(key=lambda x: x[1])
    
    ville_min, temp_min = villes_temps[0]
    ville_max, temp_max = villes_temps[-1]

    # Message Discord
    msg = (
        f"🌡️ **Extrêmes Météo France** (Basés sur les relevés réels)\n\n"
        f"🔥 **Température Maximale :** {temp_max} °C à {ville_max}\n"
        f"❄️ **Température Minimale :** {temp_min} °C à {ville_min}"
    )

    # Envoi
    requests.post(WEBHOOK_URL, json={"content": msg})


if __name__ == "__main__":
    obtenir_meteo()
