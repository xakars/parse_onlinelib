import requests
import os
from pathlib import Path
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse, unquote


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download(url, filename, folder='books/'):
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
            book_selector = soup.find('div', {'id': 'content'})
            about_book = book_selector.find('h1')
            title, author = about_book.text.split("::")
            path_to_url = [i['href'] for i in book_selector.find_all('a', href=True) if i.text == 'скачать txt']
            if not path_to_url:
                continue
            book = f'{title.strip()}.txt'
            download_url = urljoin(base_url, path_to_url[0])
            download(download_url, book)

            images_selector = "table.tabs div.bookimage img"
            img_src = soup.select(images_selector)[0]["src"]
            img_url = urljoin(base_url, img_src)
            img = urlparse(img_url).path.split('/')[-1]
            print(img_url)
            download(img_url, img, folder='images/')

        except requests.HTTPError:
            print("There is no such book")
            continue

if __name__ == "__main__":
    main()

