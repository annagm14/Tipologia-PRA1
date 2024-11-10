from scraper import Scraper

if __name__ == "__main__":
    url_clubs = "https://www.basquetcatala.cat/clubs"
    base_clubs_url = "https://www.basquetcatala.cat/club/"
    chrome_driver_path = "/opt/homebrew/bin/chromedriver"  # Substitueix amb el camí al teu chrome driver

    parser = Scraper(url_clubs, chrome_driver_path)
    ids = parser.scrape_clubs()
    parser.scrape_teams(base_clubs_url, ids)