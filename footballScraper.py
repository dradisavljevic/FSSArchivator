import bs4
import csv
import os
from selenium import webdriver
import time

root_link = 'https://www.srbijasport.net'
identifier = 1
football_clubs = {}
title = ['Match Date', 'Match Time', 'Host Team ID', 'Host Team Name', 'Host Team URL', 'Guest Team ID', 'Guest Team Name', 'Guest Team URL', 'Goals Host', 'Goals Guest']

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
#options.add_argument('--headless')
driver = webdriver.Chrome(os.path.join(os.getcwd(), 'chromedriver'), options=options)
driver.get('https://www.srbijasport.net/league/3855/games')
game_buttons = driver.find_elements_by_class_name('page-link')
driver.execute_script('arguments[0].click();', game_buttons[0])
page_source = driver.page_source

soup = bs4.BeautifulSoup(page_source, 'lxml')


team_data = soup.find('tbody', {'class': 'data'})
team_names = team_data.find_all('td', {'class': 'tim'})

with open('data.csv', 'w') as writeFile:
    writer = csv.writer(writeFile)
    writer.writerow(title)

writeFile.close()

matchday_selector = soup.find('select', {'id': 'kolo'})
with open('data.csv', 'a') as csvFile:
    writer = csv.writer(csvFile)
    for i in range(0,len(matchday_selector.find_all('option'))+1):
        time.sleep(1)
        game_buttons = driver.find_elements_by_class_name('page-link')
        driver.execute_script('arguments[0].click();', game_buttons[2])

        match_selector = soup.find_all('tr', {'class': 'result-row'})

        for match in match_selector:
            match_date = match.find('a', {'class': 'game-date'})
            match_time = match.find('span', {'class': 'game-time'})
            host = match.find('td', {'class': 'team-host'})
            host_link = host.find('a')
            host_name = host_link.text
            host_url = host_link['href']
            if host_url not in football_clubs:
                football_clubs[host_url] = identifier
                identifier = identifier + 1
            host_id = football_clubs[host_url]
            guest = match.find('td', {'class': 'team-guest'})
            guest_link = guest.find('a')
            guest_name = guest_link.text
            guest_url = guest_link['href']
            if guest_url not in football_clubs:
                football_clubs[guest_url] = identifier
                identifier = identifier + 1
            guest_id = football_clubs[guest_url]
            goals_host = match.find('span', {'class': 'res-1'})
            goals_guest = match.find('span', {'class': 'res-2'})
            row = [match_date.text.strip().replace('"',''), match_time.text.strip().replace('"',''), host_id, host_name, root_link+host_url, guest_id, guest_name, root_link+guest_url, goals_host.text.strip().replace('"',''), goals_guest.text.strip().replace('"','')]
            writer.writerow(row)

csvFile.close()
driver.close()
