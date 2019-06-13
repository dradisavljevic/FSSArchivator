import bs4
import csv
import os
from selenium import webdriver
import time
import configuration as cfg

def main():
    scraped_leagues = []
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    #options.add_argument('--headless')
    driver = webdriver.Chrome(os.path.join(os.getcwd(), cfg.DRIVER_NAME), options=options)
    level = 1
    offset = 0

    link = cfg.ROOT_LINK+'/league/3855'
    league_link = '/league/3855'
    while level != 4:
        print(level)
        league_tabs, selenium_tabs, scraped_leagues = crawl(driver, link, scraped_leagues, league_link)
        for i in range(0,len(league_tabs)):
            next_league = league_tabs[i].find('a')
            selenium_tabs[i].click()
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
                            level = level + 1
                        else:
                            offset = offset - 1
                    elif next_league.text.strip().replace('"','')=='Liga višeg ranga':
                        offset = offset + 1
                    league_link=league['href']
                    link = cfg.ROOT_LINK+league_link
                    break
            if exit:
                break
            elif i == len(league_tabs)-1:
                league_link, link, level = dead_end_prevention(league_tabs, selenium_tabs, driver, level)
    level = 1
    driver.close()

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


def crawl(driver, link, scraped_leagues, league_link):
    driver.get(link)
    soup = get_soup(driver)
    print(soup.find('h1', {'class': 'page-name'}).text.strip().replace('"',''))
    scraped_leagues.append(league_link.split('/')[2])
    league_list = soup.find('div',{'class': 'league-nav'})
    league_tabs = league_list.find_all('li', {'role': 'presentation'})
    selenium_tabs = driver.find_elements_by_xpath('//*/a[@role="tab"]')
    return league_tabs, selenium_tabs, scraped_leagues


def get_soup(driver):
    page_source = driver.page_source
    soup = bs4.BeautifulSoup(page_source, 'lxml')
    return soup

if __name__ == '__main__':
    main()
