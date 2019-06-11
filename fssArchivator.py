import bs4
import csv
import os
from selenium import webdriver
import time
import configuration as cfg

def main():
    football_clubs = {}
    identifier = 1

    with open(cfg.export_file_name, 'w') as writeFile:
        writer = csv.writer(writeFile)
        writer.writerow(cfg.title)

    writeFile.close()

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Chrome(os.path.join(os.getcwd(), cfg.driver_name), options=options)

    football_clubs, identifier = append_to_csv(cfg.superliga_start_page, driver, 1, football_clubs, identifier)
    football_clubs, identifier = append_to_csv(cfg.prva_liga_start_page, driver, 2, football_clubs, identifier)
    football_clubs, identifier = append_to_csv(cfg.srpska_liga_vojvodina_start_page, driver, 3, football_clubs, identifier)
    football_clubs, identifier = append_to_csv(cfg.srpska_liga_zapad_start_page, driver, 3, football_clubs, identifier)
    football_clubs, identifier = append_to_csv(cfg.srpska_liga_istok_start_page, driver, 3, football_clubs, identifier)
    football_clubs, identifier = append_to_csv(cfg.srpska_liga_beograd_start_page, driver, 3, football_clubs, identifier)

    driver.close()

def append_to_csv(source, driver, league_level, football_clubs, identifier):
    driver.get(source)
    page_source = driver.page_source
    soup = bs4.BeautifulSoup(page_source, 'lxml')

    with open(cfg.export_file_name, 'a') as csvFile:
        writer = csv.writer(csvFile)
        menu = soup.find('ul', {'class': 'page-menu-navs'})
        seasons_wrapper = menu.find('ul', {'class': 'dropdown-menu'})
        season_links = seasons_wrapper.find_all('a')
        for j in range(0,len(season_links)):
            if season_links[j].text.strip().replace('"','')=='2005-2006':
                break
            league_season = season_links[j].text.strip().replace('"','')
            driver.get(cfg.root_link+season_links[j]['href'])
            game_buttons = driver.find_elements_by_class_name('page-link')
            driver.execute_script('arguments[0].click();', game_buttons[0])
            page_source = driver.page_source
            soup = bs4.BeautifulSoup(page_source, 'lxml')
            league_name = soup.find('h1', {'class': 'page-name'}).text.strip().replace('"','')
            matchday = 1

            matchday_selector = soup.find('select', {'id': 'kolo'})
            for i in range(0,len(matchday_selector.find_all('option'))):
                time.sleep(1)
                game_buttons = driver.find_elements_by_class_name('page-link')
                driver.execute_script('arguments[0].click();', game_buttons[2])
                page_source = driver.page_source
                soup = bs4.BeautifulSoup(page_source, 'lxml')

                match_selector = soup.find_all('tr', {'class': 'result-row'})

                for match in match_selector:
                    match_date = match.find('a', {'class': 'game-date'}).text.strip().replace('"','')
                    match_time = match.find('span', {'class': 'game-time'}).text.strip().replace('"','')
                    host = match.find('td', {'class': 'team-host'})
                    host_link = host.find('a')
                    host_name = host_link.text
                    host_url = cfg.root_link+host_link['href']
                    host_city = host_link['data-original-title']
                    host_site_id = host_url.split('/club/')[1].split('-')[0]
                    if host_site_id not in football_clubs:
                        football_clubs[host_site_id] = identifier
                        identifier = identifier + 1
                    host_id = football_clubs[host_site_id]
                    guest = match.find('td', {'class': 'team-guest'})
                    guest_link = guest.find('a')
                    guest_name = guest_link.text
                    guest_url = cfg.root_link+guest_link['href']
                    guest_city = guest_link['data-original-title']
                    guest_site_id = guest_url.split('/club/')[1].split('-')[0]
                    if guest_site_id not in football_clubs:
                        football_clubs[guest_site_id] = identifier
                        identifier = identifier + 1
                    guest_id = football_clubs[guest_site_id]
                    goals_host = match.find('span', {'class': 'res-1'}).text.strip().replace('"','')
                    if not goals_host:
                        goals_host = '0'
                    goals_guest = match.find('span', {'class': 'res-2'}).text.strip().replace('"','')
                    if not goals_guest:
                        goals_guest = '0'
                    row = [league_name, league_level, league_season, matchday, match_date, match_time, host_id, host_name, host_city, host_url, guest_id, guest_name, guest_city, guest_url, goals_host, goals_guest]
                    writer.writerow(row)
                    print('Writing :' + league_name + ' ' + league_season + ' matchday ' + matchday)
                matchday = matchday+1

    csvFile.close()
    return football_clubs, identifier


if __name__ == '__main__':
    main()
