import bs4
import csv
import os
import selenium
from selenium import webdriver
import time
import configuration as cfg

def main():
    football_clubs = {}
    identifier = 1
    scraped_leagues = []

    with open(cfg.EXPORT_FILE_NAME, 'w') as writeFile:
        writer = csv.writer(writeFile)
        writer.writerow(cfg.TITLE)

    writeFile.close()

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    #options.add_argument('--headless')
    driver = webdriver.Chrome(os.path.join(os.getcwd(), cfg.DRIVER_NAME), options=options)

    driver.get(cfg.SUPERLIGA_START_PAGE)
    soup = get_soup(driver)

    with open(cfg.EXPORT_FILE_NAME, 'a') as csvFile:
        writer = csv.writer(csvFile)
        menu = soup.find('ul', {'class': 'page-menu-navs'})
        seasons_wrapper = menu.find('ul', {'class': 'dropdown-menu'})
        season_links = seasons_wrapper.find_all('a')
        for j in range(0,len(season_links)):
            if season_links[j].text.strip().replace('"','')=='2005-2006':
                break
            level = 1
            offset = 0
            football_clubs, identifier, scraped_leagues = scrape_match(season_links[j], driver, level, football_clubs, identifier, writer, scraped_leagues, offset)
    csvFile.close()

    driver.close()

def scrape_match(link, driver, league_level, football_clubs, identifier, writer, scraped_leagues, offset):
    league_season = link.text.strip().replace('"','')
    scrape_link = cfg.ROOT_LINK+link['href']
    league_link = link['href']
    while league_level != 4:
        driver.get(scrape_link)
        more_matchdays = True
        game_buttons = driver.find_elements_by_class_name('page-link')
        if not game_buttons:
            more_matchdays = False
        if more_matchdays:
            driver.execute_script('arguments[0].click();', game_buttons[0])
        soup = get_soup(driver)
        league_name = soup.find('h1', {'class': 'page-name'}).text.strip().replace('"','')
        matchday = 1

        matchday_selector = soup.find('select', {'id': 'kolo'})
        if not more_matchdays:
            matchday_count = 1
        else:
            matchday_count = len(matchday_selector.find_all('option'))
        for i in range(0,matchday_count):
            time.sleep(1)
            if more_matchdays:
                game_buttons = driver.find_elements_by_class_name('page-link')
                driver.execute_script('arguments[0].click();', game_buttons[2])
                soup = get_soup(driver)
            tables = soup.find_all('table', {'class': 'ssnet-results'})
            if not more_matchdays:
                for table in tables:
                    matches = table.find_all('tr', {'class': 'result-row'})
                    for match in matches:
                        match_selector.append(match)
            else:
                match_selector = tables[0].find_all('tr', {'class': 'result-row'})
            for match in match_selector:
                match_date = match.find('a', {'class': 'game-date'}).text.strip().replace('"','')
                match_time = match.find('span', {'class': 'game-time'}).text.strip().replace('"','')
                host = match.find('td', {'class': 'team-host'})
                host_link = host.find('a')
                host_name = host_link.text
                host_url = cfg.ROOT_LINK+host_link['href']
                host_city = host_link['data-original-title']
                host_site_id = host_url.split('/club/')[1].split('-')[0]
                if host_site_id not in football_clubs:
                    football_clubs[host_site_id] = identifier
                    identifier = identifier + 1
                host_id = football_clubs[host_site_id]
                guest = match.find('td', {'class': 'team-guest'})
                guest_link = guest.find('a')
                guest_name = guest_link.text
                guest_url = cfg.ROOT_LINK+guest_link['href']
                guest_city = guest_link['data-original-title']
                guest_site_id = guest_url.split('/club/')[1].split('-')[0]
                if guest_site_id not in football_clubs:
                    football_clubs[guest_site_id] = identifier
                    identifier = identifier + 1
                guest_id = football_clubs[guest_site_id]
                goals_host = match.find('span', {'class': 'res-1'}).text.strip().replace('"','')
                goals_guest = match.find('span', {'class': 'res-2'}).text.strip().replace('"','')
                row = [league_name, league_level, league_season, matchday, match_date, match_time, host_id, host_name, host_city, host_url, guest_id, guest_name, guest_city, guest_url, goals_host, goals_guest]
                writer.writerow(row)
                print('Writing: ' + league_name + ' Season ' + league_season + ' Matchday ' + str(matchday))
            matchday = matchday + 1
        scraped_leagues.append(league_link.split('/')[2])
        soup = get_soup(driver)
        league_list = soup.find('div',{'class': 'league-nav'})
        league_tabs = league_list.find_all('li', {'role': 'presentation'})
        selenium_tabs = driver.find_elements_by_xpath('//*/a[@role="tab"]')

        for j in range(0,len(league_tabs)):
            next_league = league_tabs[j].find('a')
            if j != 0:
                selenium_tabs[j].send_keys(selenium.webdriver.common.keys.Keys.SPACE)
            soup = get_soup(driver)
            league_container = soup.find('div', {'class': 'tab-content'})
            crawl_league_container = league_container.find('div', {'class': 'active'})
            leagues = crawl_league_container.find_all('a')
            exit = False
            for league in leagues:
                if league['href'].split('/')[2] not in scraped_leagues:
                    exit = True
                    if next_league.text.strip().replace('"','')=='Niži rang':
                        if offset == 0:
                            league_level = league_level + 1
                        else:
                            offset = offset - 1
                    elif next_league.text.strip().replace('"','')=='Liga višeg ranga':
                        offset = offset + 1
                    league_link=league['href']
                    scrape_link = cfg.ROOT_LINK+league_link
                    break
            if exit:
                break
            elif j == len(league_tabs)-1:
                league_link, scrape_link, league_level = dead_end_prevention(league_tabs, selenium_tabs, driver, league_level)
                break
    return football_clubs, identifier, scraped_leagues

def get_soup(driver):
    page_source = driver.page_source
    soup = bs4.BeautifulSoup(page_source, 'lxml')
    return soup

def dead_end_prevention(league_tabs, selenium_tabs, driver, level):
    for i in range(0,len(league_tabs)):
        next_league = league_tabs[i].find('a')
        if next_league.text.strip().replace('"','')=='Ostala takmičenja':
            selenium_tabs[i].click()
            break
    soup = get_soup(driver)
    league_container = soup.find('div', {'class': 'tab-content'})
    crawl_league_container = league_container.find('div', {'class': 'active'})
    leagues = crawl_league_container.find_all('a')
    exit = False
    for league in leagues:
        driver.get(cfg.ROOT_LINK+league['href'])
        soup = get_soup(driver)
        league_list = soup.find('div',{'class': 'league-nav'})
        league_tabs = league_list.find_all('li', {'role': 'presentation'})
        selenium_tabs = driver.find_elements_by_xpath('//*/a[@role="tab"]')
        for i in range(0,len(league_tabs)):
            next_league = league_tabs[i].find('a')
            if next_league.text.strip().replace('"','')=='Niži rang':
                selenium_tabs[i].click()
                soup = get_soup(driver)
                league_container = soup.find('div', {'class': 'tab-content'})
                crawl_league_container = league_container.find('div', {'class': 'active'})
                leagues = crawl_league_container.find_all('a')
                league_link=leagues[0]['href']
                link = cfg.ROOT_LINK+league_link
                level = level + 1
                exit = True
                break
        if exit:
            break
    return league_link, link, level


if __name__ == '__main__':
    main()
