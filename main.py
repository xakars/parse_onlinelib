import requests
import os
from pathlib import Path
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_txt(url, filename, folder='books/'):
    Path(folder).mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()
    pure_filename = sanitize_filename(filename)
    path_to_save = os.path.join(folder, pure_filename)
    with open(path_to_save, "wb") as file:
        file.write(response.content)


def main():
    base_url = 'https://tululu.org/'
    for id in range(1, 11):
        try:
            url = f"{base_url}/b{id}/"
            response = requests.get(url)
            response.raise_for_status()
            check_for_redirect(response)
            soup = BeautifulSoup(response.text, 'lxml')
            selector = soup.find('div', {'id': 'content'})
            about_book = selector.find('h1')
            title, author = about_book.text.split("::")
            pat_to_url = [i['href'] for i in selector.find_all('a', href=True) if i.text == 'скачать txt']
            if not pat_to_url:
                continue
            bookname = f'{title.strip()}.txt'
            download_url = f'{base_url}{pat_to_url[0]}'
            download_txt(download_url, bookname)
        except requests.HTTPError:
            print("There is no such book")
            continue

if __name__ == "__main__":
    main()

