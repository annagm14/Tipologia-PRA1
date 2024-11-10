from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup

class Scraper:

    def __init__(self, url, chrome_driver_path):
        self.url = url
        self.chrome_driver_path = chrome_driver_path
        self.driver = None

    def _init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Per a executar sense interfície gràfica
        chrome_service = Service(self.chrome_driver_path)
        self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    def scrape_clubs(self):
        if not self.driver:
            self._init_driver()

        try:
            # Carregar la pàgina
            self.driver.get(self.url)
            time.sleep(3)  # Esperar que la pàgina carregui

            print("Títol de la pàgina actual:", self.driver.title)

            # Fer la crida AJAX per obtenir les dades
            response = self.driver.execute_script("""
                var xhr = new XMLHttpRequest();
                xhr.open('GET', 'https://www.basquetcatala.cat/clubs/ajax', false); // Crida síncrona
                xhr.send();
                return xhr.responseText; // Retorna el text de resposta
            """)

            # Parsejar el JSON obtingut
            data = json.loads(response)

            # Filtrar les columnes que volem
            columns_to_keep = [
                "id", "clubCode", "name", "shortName", "alfabeticOrder", "direction",
                "town", "province", "telephone", "fax", "mail", "mail2", "president",
                "contact", "telephoneCR", "telephoneMobileCR", "web"
            ]
            filtered_data = [
                {key: club[key] for key in columns_to_keep if key in club}
                for club in data
            ]

            # Guardar les dades en un arxiu CSV
            self.save_to_csv(filtered_data, "clubs_data.csv")

            # Crear DataFrame de pandas per obtenir els ids dels clubs
            df = pd.DataFrame(data)
            ids = df['id']

            return ids

        except Exception as e:
            print("Error:", e)
            return None, None

        finally:
            self.driver.quit()

    def save_to_csv(self, data, filename):
        try:
            # Comprovem si hi ha dades per escriure
            if not data:
                print("No hi ha dades per guardar.")
                return

            # Obrim el fitxer per escriure
            with open(filename, mode="w", newline='', encoding="utf-8") as file:
                writer = csv.writer(file)

                # Obtenim les claus per a les capçaleres (suponem que totes les dades tenen la mateixa estructura)
                headers = data[0].keys() if len(data) > 0 else []
                writer.writerow(headers)

                # Escrivim les files de dades
                for item in data:
                    writer.writerow(item.values())

            print(f"Dades guardades a {filename}")

        except Exception as e:
            print(f"Error al guardar el fitxer CSV: {e}")

    def scrape_teams(self,base_url, ids):
        all_clubs_data = []

        # Iterem sobre cada id dels clubs
        for club_id in ids:
            club_url = f"{base_url}{club_id}"
            print(f"Accessing {club_url}")
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,\
                */*;q=0.8",
                "Accept-Encoding": "gzip, deflate, sdch, br",
                "Accept-Language": "en-US,en;q=0.8",
                "Cache-Control": "no-cache",
                "dnt": "1",
                "Pragma": "no-cache",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
            }

            response = requests.get(club_url, headers=headers)

            if response.status_code == 200:
                # Parsejem la pàgina amb BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # Trobem els equips filtrant per la classe
                teams_section = soup.find("div", class_="col-md-8 notranslate")

                if teams_section:
                    teams = teams_section.find_all("div", class_="table-responsive")

                    # Extraiem cada equip i els seus detalls
                    for team_div in teams:
                        category = team_div.get_text(strip=True).split('|')[0].strip()
                        team_links = team_div.find_all("a", class_="c-0")

                        for team_link in team_links:
                            team_name = team_link.get_text(strip=True)
                            team_id = team_link['href'].split('/')[-1]

                            # Guardem les dades en un diccionari
                            team_data = {
                                "club_id": club_id,
                                "category": category,
                                "team_name": team_name,
                                "team_id": team_id
                            }
                            all_clubs_data.append(team_data)
                else:
                    print(f"No teams found for club {club_id}")
            else:
                print(f"Failed to access {club_url} with status code {response.status_code}")

            # Per evitar sobrecarregar el servidor deixem dos segons entre cada request.
            time.sleep(2)

        # Guardem les dades en un .csv
        self.save_to_csv(all_clubs_data, "club_teams_data.csv")


url_clubs = "https://www.basquetcatala.cat/clubs"
base_clubs_url = "https://www.basquetcatala.cat/club/"
chrome_driver_path = "/opt/homebrew/bin/chromedriver"  # Substitueix amb el camí al teu chrome driver

parser = Scraper(url_clubs, chrome_driver_path)
ids = parser.scrape_clubs()
parser.scrape_teams(base_clubs_url, ids)