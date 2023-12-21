import requests
from bs4 import BeautifulSoup
from typing import Any, cast, List
from bs4.element import Tag
import csv
from datetime import datetime
def print_property(obj: Any):
    print('type:', type(obj))
    print('dir:', dir(obj))

# get domain from url
def get_domain(url: str) -> str:
    return url.split('/')[2]

def get_main_domain(url: str) -> str:
    domain = get_domain(url)
    return '.'.join(domain.split('.')[-2:])

def handle_detik(url: str) -> [str, str]:
    # strip url query
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # title is in h1.detail__title
    title = soup.find('h1', class_='detail__title').text.strip()
    htmlClass = 'detail__body-text itp_bodycontent'
    # only get first level of p
    paragraphs = list(filter(lambda p: len(p.text) > 0,
                       cast(Tag, soup.find('div', class_=htmlClass)).find_all(['p', 'ul', 'ol'], recursive=False)
                       ))
    flattenedText = ""
    for p in paragraphs:
        # ignore p if 
        # 1. p has any attribute
        # 2. p starts with \r \n or \t
        text = p.text.strip()
        if (len(p.attrs) > 0 
            or text.startswith('\r') 
            or text.startswith('\n') 
            or text.startswith('\t')
            or text.startswith('Simak selengkapnya')
            or p.select_one('div.detail__multiple') is not None
            or p.select_one('div.sisip_video_ds') is not None
            or text.startswith('Simak Video')
            or text.startswith('Simak juga Video')
            or text.startswith('[Gambas')
            or text.startswith('Lihat juga Video')
            or text.startswith('Lihat Video')
            or text.startswith('Baca selengkapnya')
            or 'halaman selanjutnya' in text.lower()
            or 'halaman berikutnya' in text.lower()
        ):
            continue
        else:
            flattenedText += text + '\n\n'
    # button property dtr-act="button selanjutnya"
    next_button = soup.find('a', attrs={'dtr-act': 'button selanjutnya'})
    while next_button is not None:
        next_url = next_button['href']
        response = requests.get(next_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = list(filter(lambda p: len(p.text) > 0,
                           cast(Tag, soup.find('div', class_=htmlClass)).find_all(['p', 'ul', 'ol'], recursive=False)
                           ))
        for p in paragraphs:
            text = p.text.strip()
            if (len(p.attrs) > 0 
                or text.startswith('\r') 
                or text.startswith('\n') 
                or text.startswith('\t')
                or text.startswith('Simak selengkapnya')
                or p.select_one('div.detail__multiple') is not None
                or p.select_one('div.sisip_video_ds') is not None
                or text.startswith('Simak Video')
                or text.startswith('Simak juga Video')
                or text.startswith('[Gambas')
                or text.startswith('Lihat juga Video')
                or text.startswith('Lihat Video')
                or text.startswith('Baca selengkapnya')
                or 'halaman selanjutnya' in text.lower()
                or 'halaman berikutnya' in text.lower()
            ):
                continue
            else:
                flattenedText += text + '\n\n'
        next_button = soup.find('a', attrs={'dtr-act': 'button selanjutnya'})
    return [title, flattenedText]

def handle_kompas(url: str) -> [str, str]:
    url = url.split('?')[0]
    response = requests.get(url + '?page=all')
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1', class_='read__title').text.strip()
    cssSelector="div.read__content > .clearfix"
    # paragraphs = list(filter(lambda p: len(p.text) > 0,
    #                    cast(Tag, soup.select_one(cssSelector)).find_all('p', recursive=False)))
    # p, ul, and ol
    paragraphs = list(filter(lambda p: len(p.text) > 0,
                       cast(Tag, soup.select_one(cssSelector)).find_all(['p', 'ul', 'ol'], recursive=False)))
    flattenedText = ""
    for p in paragraphs:
        text = p.text.strip()
        if (
            len(p.attrs) > 0 or text.startswith('\r') or text.startswith('\n') or text.startswith('\t')
            or text.startswith('Baca juga')
        ):
            continue
        else:
            flattenedText += text + '\n\n'
    if len(flattenedText.strip().strip('\n').strip('\t').strip('\r')) == 0:
        raise Exception('Empty content')
    return [title, flattenedText]
    
def cnn_indonesia_handler(url: str) -> [str, str]:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    titleCssSelector = 'h1.mb-2.leading-9'
    title = soup.select_one(titleCssSelector).text.strip()
    contentCssSelector = 'div.detail-text'
    paragraphs = list(filter(lambda p: len(p.text) > 0,
                       cast(Tag, soup.select_one(contentCssSelector)).find_all(['p', 'ul', 'ol'], recursive=False)))
    flattenedText = ""
    for p in paragraphs:
        text = p.text.strip()
        if (
            len(p.attrs) > 0 or text.startswith('\r') or text.startswith('\n') or text.startswith('\t')
            or text.startswith('[Gambas')
            ):
            continue
        else:
            flattenedText += text + '\n\n'
    if len(flattenedText.strip().strip('\n').strip('\t').strip('\r')) == 0:
        raise Exception('Empty content')
    return [title, flattenedText]
    
def generic_handler(url: str) -> str:
    # get text from body p
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = list(filter(lambda p: len(p.text.strip()) > 100 and len(p.text.split()) > 7,
                          cast(Tag, soup.body).find_all('p')))
    flattenedText = ""
    for p in paragraphs:
        if p.text.startswith('\r') or p.text.startswith('\n') or p.text.startswith('\t'):
            continue
        else:
            flattenedText += p.text + '\n\n'

    if len(flattenedText.strip().strip('\n').strip('\t').strip('\r')) == 0:
        raise Exception('Empty content')
    return flattenedText

def csv_writer(filename: str, data: List[any]) -> bool:
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['title', 'content'])
        for row in data:
            writer.writerow(row)

def csv_writer_discovery(filename: str, data: List[any]):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['title', 'author', 'published', 'url', 'content'])
        for row in data:
            writer.writerow(row)

if __name__ == '__main__':
    # Manual Input
    print("WARNING: please install BeautifulSoup4 and requests (pip) first")
    choice = input('Automatic? (y/n): ')
    if choice.lower() == 'n':
        url = input('URL: ')

        # if url not start with http:// or https://, add http://
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url
        
        main_domain = get_main_domain(url)
        if main_domain == 'detik.com':
            print()
            print(handle_detik(url))
        elif main_domain == 'kompas.com':
            print()
            print(handle_kompas(url))
        elif main_domain == 'cnnindonesia.com':
            print()
            print(cnn_indonesia_handler(url))
        else:
            print("Using generic handler")
            print(generic_handler(url))
    elif choice.lower() == 'y':
        print("Pick Portal:")
        print("1. Detik")
        print("2. Kompas")
        print("3. CNN Indonesia")
        print("4. Search By Topic (Google)")
        choice = input("Your choice: ")
        if choice == '1':
            how_many = input("How many news do you want to pick? ")
            homepage = requests.get('https://news.detik.com/indeks')
            soup = BeautifulSoup(homepage.text, 'html.parser')
            # list-content
            articleSelector = '.list-content > article h3 > a'
            nextPageSelector = 'a.pagination__item'
            nextPageText = 'Next'
            contents = []
            nextPage = soup.find('a', string=nextPageText)
            while len(contents) < int(how_many) and nextPage is not None:
                links = list(
                    map ( lambda a: a['href'],
                    filter(lambda a: a['href'].startswith('https://news.detik.com/')
                           , soup.select(articleSelector))
                    )
                )
                for link in links:
                    if len(contents) >= int(how_many):
                        break
                    try:
                        contents.append(handle_detik(link))
                    except Exception as e:
                        print(e)
                        print(f'Error on {link}')
                if len(contents) >= int(how_many):
                    break
                nextPage = soup.find('a', string=nextPageText)
                nextPageUrl = nextPage['href']
                nextPageResponse = requests.get(nextPageUrl)
                soup = BeautifulSoup(nextPageResponse.text, 'html.parser')

            # write to csv
            currentTimestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f'detik_{how_many}_{currentTimestamp}.csv'
            csv_writer(filename, contents)
            print(f'File {filename} created')
        elif choice == '2':
            how_many = input("How many news do you want to pick? ")
            homepage = requests.get('https://indeks.kompas.com/')
            soup = BeautifulSoup(homepage.text, 'html.parser')
            # list-content
            articleSelector = '.article__list__title a'
            nextPageSelector = 'a.paging__link.paging__link--next'
            nextPage = soup.select_one(nextPageSelector)
            contents = []
            while len(contents) < int(how_many) and nextPage is not None:
                links = list(
                    map ( lambda a: a['href'],
                        soup.select(articleSelector)
                    )
                )
                for link in links:
                    if len(contents) >= int(how_many):
                        break
                    try:
                        contents.append(handle_kompas(link))
                    except Exception as e:
                        print(e)
                        print(f'Error on {link}')
                if len(contents) >= int(how_many):
                    break
                nextPageUrl = nextPage['href']
                nextPageResponse = requests.get(nextPageUrl)
                soup = BeautifulSoup(nextPageResponse.text, 'html.parser')
                nextPage = soup.select_one(nextPageSelector)
            currentTimestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f'kompas_{how_many}_{currentTimestamp}.csv'
            csv_writer(filename, contents)
            print(f'File {filename} created')
        elif choice == '3':
            how_many = input("How many news do you want to pick? ")
            homepage = requests.get('https://www.cnnindonesia.com/indeks')
            soup = BeautifulSoup(homepage.text, 'html.parser')
            # nhl-list
            articleSelector = 'article > a'
            nextPageSelector = 'a[dtr-sec="halaman selanjutnya"][dtr-act="halaman selanjutnya"]'
            nextPage = soup.select_one(nextPageSelector)
            contents = []
            while len(contents) < int(how_many) and nextPage is not None:
                links = list(
                    map ( lambda a: a['href'],
                    filter(lambda a: a['href'].startswith('https://www.cnnindonesia.com/'), soup.select(articleSelector))
                    )
                )
                for link in links:
                    if len(contents) >= int(how_many):
                        break
                    try:
                        contents.append(cnn_indonesia_handler(link))
                    except Exception as e:
                        print(e)
                        print(f'Error on {link}')
                nextPageUrl = nextPage['href']
                nextPageResponse = requests.get(nextPageUrl)
                soup = BeautifulSoup(nextPageResponse.text, 'html.parser')
            currentTimestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f'cnn_indonesia_{how_many}_{currentTimestamp}.csv'
            csv_writer(filename, contents)
            print(f'File {filename} created')
        elif choice == '4':
            how_many = input("How many news do you want to pick? ")
            topic = input("Topic: ")
            homepage = requests.get(f'https://www.google.com/search?q={topic}&tbm=nws')
            soup = BeautifulSoup(homepage.text, 'html.parser')
            # select anchor with href that starts with /url?q=
            articleSelector = 'div#main a[href^="/url?q="]'
            # select footer anchor with href that starts with /search?q=
            nextPageSelector = 'footer a[href^="/search?q="]' 
            nextPage = soup.select_one(nextPageSelector)
            contents = []
            while len(contents) < int(how_many) and nextPage is not None:
                anchors = list(
                    filter(lambda a: a['href'].startswith('/url?q=') and 'google.com' not in a['href'], soup.select(articleSelector))
                    )
                for anchor in anchors:
                    if len(contents) >= int(how_many):
                        break
                    divorspans = anchor.parent.select('div, span')
                    divorspans = list(filter(lambda d: d.find(string=True, recursive=False) is not None, divorspans))
                    try:
                        url = anchor['href'].split('&')[0][7:]
                        title = divorspans[0].text
                        author = divorspans[1].text
                        published = divorspans[3].text
                    except Exception as e:
                        with open(f'google_{topic}.html', 'w', encoding='utf-8') as f:
                            f.write(soup.prettify())
                        print(e)
                        print(f'Error on {anchor}')
                    try:
                        content = generic_handler(url)
                        contents.append([title, author, published, url, content])
                    except Exception as e:
                        print(e)
                        print(f'Error on {url}')
                nextPageUrl = 'https://www.google.com' + nextPage['href']
                nextPageResponse = requests.get(nextPageUrl)
                soup = BeautifulSoup(nextPageResponse.text, 'html.parser')
                nextPage = soup.select_one(nextPageSelector)
            currentTimestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f'google_{topic}_{how_many}_{currentTimestamp}.csv'
            csv_writer_discovery(filename, contents)
            print(f'File {filename} created')
        else:
            print("Invalid input")
    else:
        print("Invalid input")
