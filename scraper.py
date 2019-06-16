import csv
from match_scraper import scrape_match
import os
from selenium import webdriver
from soup_getter import get_soup
import config as cfg


def scrape():
    league_systems = [cfg.SERBIA_START_PAGE, cfg.MONTENEGRO_START_PAGE]
    export_files = [cfg.SERBIA_EXPORT_FILE_NAME, cfg.MONTENEGRO_EXPORT_FILE_NAME]

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    #options.add_argument('--headless')
    driver = webdriver.Chrome(os.path.join(os.getcwd(), cfg.DRIVER_NAME), options=options)

    for k in range(0, len(league_systems)):
        football_clubs = {}
        identifier = 1
        scraped_leagues = []
        links_to_scrape = []

        with open(export_files[k], 'w') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerow(cfg.TITLE)

        writeFile.close()

        driver.get(league_systems[k])
        soup = get_soup(driver)

        with open(export_files[k], 'a') as csvFile:
            writer = csv.writer(csvFile)
            menu = soup.find('ul', {'class': 'page-menu-navs'})
            seasons_wrapper = menu.find('ul', {'class': 'dropdown-menu'})
            season_links = seasons_wrapper.find_all('a')
            for j in range(0,len(season_links)):
                if season_links[j].text.strip().replace('"', '') != cfg.ONGOING_SEASON:
                    if season_links[j].text.strip().replace('"', '') == cfg.SEASON_CUTOFF:
                        break
                    level = 1
                    offset = 0
                    football_clubs, identifier, scraped_leagues, links_to_scrape =\
                     scrape_match(season_links[j], driver, level, football_clubs, identifier, writer, scraped_leagues, offset, links_to_scrape)
        csvFile.close()
        print('Data acquisition successfully completed!')
    driver.close()


if __name__ == '__main__':
    scrape()
