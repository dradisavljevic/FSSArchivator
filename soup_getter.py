import bs4

def get_soup(driver):
    page_source = driver.page_source
    soup = bs4.BeautifulSoup(page_source, 'lxml')
    return soup
