import bs4
import config as cfg
import csv
from dataclasses import dataclass
import os
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
import time


def main():
    league_systems = [cfg.SERBIA_START_PAGE, cfg.MONTENEGRO_START_PAGE]
    export_files = [cfg.SERBIA_EXPORT_FILE_NAME, cfg.MONTENEGRO_EXPORT_FILE_NAME]

    driver = create_webdriver()

    for index, league_system in enumerate(league_systems):

        driver.get(league_system)
        webpage_content = get_webpage_content(driver)

        scrape_and_write_to_csv(filename=export_files[index], webpage_content=webpage_content, driver=driver)

        print('Data acquisition successfully completed!')

    driver.close()

    print('Scraping finished. Goodbye.')


@dataclass
class Link:
    '''Class that holds information about links that are to be scraped.

    Attributes:
        url (str): Full URL to link.
        id (str): ID extracted from link URL.
        href (str): Part of the URL that can be attached to the ROOT_LINK specified in config file.
        level (int): Level of the league on the league system pyramid, to which the URL redirects to.
        scraped (bool): Information if the league has been scraped or not.
    '''
    url: str
    id: str
    href: str
    level: int
    scraped: bool = False


def create_webdriver():
    '''Creates selenium webdriver.

    Returns:
        selenium.webdriver.chrome.webdriver.WebDriver: Webdriver used to navigate the webpage content.
    '''
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    #options.add_argument('--headless')
    driver = webdriver.Chrome(os.path.join(os.getcwd(), cfg.DRIVER_NAME), options=options)
    return driver


def get_webpage_content(driver):
    '''Scrapes the webpage using the BeautifulSoup module.

    Args:
        driver (selenium.webdriver.chrome.webdriver.WebDriver): Webdriver used to navigate the webpage content.

    Returns:
        bs4.BeautifulSoup: Scraped webpage content parsed by lxml parser.
    '''
    page_source = driver.page_source
    webpage_content = bs4.BeautifulSoup(page_source, 'lxml')
    return webpage_content


def scrape_and_write_to_csv(filename, webpage_content, driver):
    '''Creates new csv and writes scraped data inside.

    Args:
        filename (str): Name of the output file.
        webpage_content (bs4.BeautifulSoup): Scraped webpage content parsed by lxml parser.
        driver (selenium.webdriver.chrome.webdriver.WebDriver): Webdriver used to navigate the webpage content.
    '''
    links_to_scrape = [] # List of links that are to be scraped

    # Create new blank csv file with just the title row
    with open(filename, 'w') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(cfg.TITLE)

    with open(filename, 'a') as csvFile:
        writer = csv.writer(csvFile)
        # Find a list of urls leading to every season of the top level league
        menu = webpage_content.find('ul', {'class': 'page-menu-navs'})
        seasons_wrapper = menu.find('ul', {'class': 'dropdown-menu'})
        season_links = seasons_wrapper.find_all('a')
        for season_link in season_links:
            # Ongoing season has unfinished games within it, so it is not of interest
            if season_link.text.strip().replace('"', '') != cfg.ONGOING_SEASON:
                if season_link.text.strip().replace('"', '') == cfg.SEASON_CUTOFF:
                    break
                level = 1
                links_to_scrape = scrape_league_season(driver, writer, links_to_scrape, link=season_link, league_level=level)


def scrape_league_season(driver, writer, links_to_scrape, link, league_level):
    '''Crawls through league seasons until it reaches the cutoff season.

    Args:
        driver (selenium.webdriver.chrome.webdriver.WebDriver): Webdriver used to navigate the webpage content.
        wrtier (csv.writer): Object that writes to output csv file.
        links_to_scrape (list): List of league URL content containing information which leagues have previously been scraped.
        link (str): Link of the first league to be scraped.
        level (int): Level of the league to be scraped on pyramid.

    Returns:
        list: List of league URL content containing information which leagues have previously been scraped.
    '''
    league_season = link.text.strip().replace('"', '')
    # Inner text of the a tag holds current league season
    scrape_link = cfg.ROOT_LINK + link['href']
    league_link = link['href']
    while league_level != cfg.LEVEL_CUTOFF:
        driver.get(scrape_link)
        # In case of a single matchday (playoffs) there is no multiple tables
        more_matchdays = True
        game_buttons = driver.find_elements_by_class_name('page-link')
        if not game_buttons:
            more_matchdays = False
        if more_matchdays:
            old_content = get_webpage_content(driver)
            driver.execute_script('arguments[0].click();', game_buttons[0])
        webpage_content = get_webpage_content(driver)
        if old_content != None:
            while(old_content == webpage_content):
                time.sleep(1)
                webpage_content = get_webpage_content(driver)
        league_name = webpage_content.find('h1', {'class': 'page-name'}).text.strip().replace('"', '')
        matchday = 1

        matchday_selector = webpage_content.find('select', {'id': 'kolo'})
        if not more_matchdays:
            matchday_count = 1
        else:
            matchday_count = len(matchday_selector.find_all('option'))

        # Previous matchday scrape data
        old_table_data = {}
        for i in range(0,matchday_count):
            match_selector = get_matches(old_table_data, more_matchdays, driver, webpage_content)
            for match in match_selector:
                row = match_to_csv_row(match, league_level, league_name, league_season, matchday)
                writer.writerow(row)
                print('Writing: ' + league_name + ' Season ' + league_season + ' Matchday ' + str(matchday))
            old_table_data = match_selector
            matchday = matchday + 1

        if all(scrape_link.id != league_link.split('/')[2] for scrape_link in links_to_scrape):
            links_to_scrape.append(Link(cfg.ROOT_LINK + league_link, league_link.split('/')[2], league_link, league_level, False))
        for link_to_scrape in links_to_scrape:
            if league_link.split('/')[2] == link_to_scrape.id:
                link_to_scrape.scraped = True
                break

        scrape_link, league_link, league_level = get_next_league(webpage_content, driver, links_to_scrape, scrape_link, league_level)

    return links_to_scrape


def get_matches(old_table_data, more_matchdays, driver, webpage_content):
    '''Scrapes match result data from the website.

    Args:
        old_table_data (bs4.element.Tag): Html element containing list of results from previous matchday/league.
        more_matchdays (bool): Contains information whether or not there is more matchdays, or is there only a single result table.
        driver (selenium.webdriver.chrome.webdriver.WebDriver): Webdriver used to navigate the webpage content.
        webpage_content (bs4.BeautifulSoup): Scraped webpage content parsed by lxml parser.

    Returns:
        bs4.element.Tag: Html element containing results of the matchday presented on the current webpage.
    '''
    match_selector = []

    game_buttons = driver.find_elements_by_class_name('page-link')
    if more_matchdays:
        try:
            driver.execute_script('arguments[0].click();', game_buttons[2])
        except StaleElementReferenceException as e:
            # In case the element didn't refresh in time, wait a bit
            time.sleep(2)
            game_buttons = driver.find_elements_by_class_name('page-link')
            driver.execute_script('arguments[0].click();', game_buttons[2])
        time.sleep(1)
        webpage_content = get_webpage_content(driver)
    tables = webpage_content.find_all('table', {'class': 'ssnet-results'})

    # Single matchday can have multiple tables
    if not more_matchdays:
        for table in tables:
            matches = table.find_all('tr', {'class': 'result-row'})
            for match in matches:
                match_selector.append(match)
    else:
        match_selector = tables[0].find_all('tr', {'class': 'result-row'})
        while old_table_data == match_selector:
            # If jquery didn't change the webpage in time, prevent old data from being written to csv
            time.sleep(1)
            webpage_content = get_webpage_content(driver)
            tables = webpage_content.find_all('table', {'class': 'ssnet-results'})
            match_selector = tables[0].find_all('tr', {'class': 'result-row'})

    return match_selector


def match_to_csv_row(match, league_level, league_name, league_season, matchday):
    '''Converts the scraped match data to a csv row.

    Args:
        match (bs4.element.Tag): Html element containing information on the outcome of the single match.
        league_level (int): Leagues level in the league system.
        league_name (str): Name of the league.
        league_season (str): Season of the league.
        matchday (int): Matchday number of the curent match.

    Returns:
        list: Row to be added to a csv file containing scraped match information.
    '''
    match_date = match.find('a', {'class': 'game-date'}).text.strip().replace('"', '')
    match_time = match.find('span', {'class': 'game-time'}).text.strip().replace('"', '')
    host = match.find('td', {'class': 'team-host'})
    host_link = host.find('a')
    host_name = host_link.text
    host_url = cfg.ROOT_LINK + host_link['href']
    host_city = host_link['data-original-title']
    host_id = host_url.split('/club/')[1].split('-')[0]
    guest = match.find('td', {'class': 'team-guest'})
    guest_link = guest.find('a')
    guest_name = guest_link.text
    guest_url = cfg.ROOT_LINK + guest_link['href']
    guest_city = guest_link['data-original-title']
    guest_id = guest_url.split('/club/')[1].split('-')[0]
    goals_host = match.find('span', {'class': 'res-1'}).text.strip().replace('"', '')
    goals_guest = match.find('span', {'class': 'res-2'}).text.strip().replace('"', '')
    if goals_host == '' or goals_host == None:
        outcome = 'U'
    else:
        if (int(goals_host) > int(goals_guest)):
            outcome = 'H'
        elif (int(goals_guest) > int(goals_host)):
            outcome = 'G'
        else:
            outcome = 'D'
    half_time = match.find('a', {'data-toggle': 'popover'})
    if half_time is not None and half_time['data-content'].strip().replace('"', '')[0] == '(':
        goals_host_half_time = half_time['data-content'].strip().replace('"', '')[1]
        goals_guest_half_time = half_time['data-content'].strip().replace('"', '')[3]
    else:
        goals_host_half_time = None
        goals_guest_half_time = None
    if league_level == 0:
        level = 1
    else:
        level = league_level
    row = [
    league_name,
    level,
    league_season,
    matchday,
    match_date,
    match_time,
    host_id,
    host_name,
    host_city,
    host_url,
    guest_id,
    guest_name,
    guest_city,
    guest_url,
    goals_host,
    goals_guest,
    goals_host_half_time,
    goals_guest_half_time,
    outcome
    ]
    return row


def get_next_league(webpage_content, driver, links_to_scrape, scrape_link, league_level):
    '''Picks url of the next league for crawler to follow.

        Args:
            webpage_content (bs4.BeautifulSoup): Scraped webpage content parsed by lxml parser.
            driver (selenium.webdriver.chrome.webdriver.WebDriver): Webdriver used to navigate the webpage content.
            links_to_scrape (list): List of league URL content containing information which leagues have previously been scraped.
            scrape_link (str): Previously scraped leagues link.
            league_level (int): Level on the pyramid of the previously scraped league.

        Returns:
            str: URL of the next league to be scraped.
            str, NoneType: Part of the URL to the next league to be scraped.
            int: Level of the next league on the league system pyramid.
    '''
    webpage_content = get_webpage_content(driver)
    league_list = webpage_content.find('div', {'class': 'league-nav'})
    league_level_tabs = league_list.find_all('li', {'role': 'presentation'})
    league_level_tab_buttons = driver.find_elements_by_xpath('//*/a[@role="tab"]')

    # For each tab holding other league urls, add them to the list of leagues to be scraped
    for index, league_level_tab in enumerate(league_level_tabs):
        next_league = league_level_tab.find('a')
        if index != 0:
            # The first tab is already clicked on by default
            webdriver.ActionChains(driver).move_to_element(league_level_tab_buttons[index]).click(league_level_tab_buttons[index]).perform()
        webpage_content = get_webpage_content(driver)
        league_container = webpage_content.find('div', {'class': 'tab-content'})
        crawl_league_container = league_container.find('div', {'class': 'active'})
        leagues = crawl_league_container.find_all('a')
        for league in leagues:
            if next_league.text.strip().replace('"', '') == 'Niži rang':
                # If league from the tab is lower level than the current one
                next_league_level = league_level + 1
            elif next_league.text.strip().replace('"', '') == 'Liga višeg ranga':
                # If league from the tab is upper level than the current one
                next_league_level = league_level - 1
            else:
                next_league_level = league_level
            if all(scrape_link.id != league['href'].split('/')[2] for scrape_link in links_to_scrape):
                if next_league_level != cfg.LEVEL_CUTOFF:
                    links_to_scrape.append(Link(cfg.ROOT_LINK + league['href'], league['href'].split('/')[2], league['href'], next_league_level, False))
    next_link = None

    # Check through list of links to be scraped for the league with the lowest level
    for link in links_to_scrape:
        if link.scraped == False:
            if next_link != None and next_link.level>link.level:
                next_link = link
            elif next_link == None:
                next_link = link
    if next_link is not None:
        league_link = next_link.href
        scrape_link = next_link.url
        league_level = next_link.level
    else:
        # If there is no more leagues in the list, the task is fnished
        league_level = cfg.LEVEL_CUTOFF
        league_link = None

    return scrape_link, league_link, league_level


if __name__ == '__main__':
    main()
