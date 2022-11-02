import requests
import os
import argparse
import time
import json
from pathlib import Path
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def download_txt(url, filename, folder="./books/"):
    Path(folder).mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    pure_filename = sanitize_filename(filename)
    title = f"{pure_filename}.txt"
    path_to_save = os.path.join(folder, title)
    with open(path_to_save, "wb") as file:
        file.write(response.content)


def download_image(url, filename, folder="./images/"):
    Path(folder).mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    path_to_save = os.path.join(folder, filename)
    with open(path_to_save, "wb") as file:
        file.write(response.content)


def parse_book_page(response):
    soup = BeautifulSoup(response.text, "lxml")
    about_book = soup.select_one("#content h1")
    title, author = about_book.text.split("::")
    book_url_selector = soup.select_one(".d_book:nth-of-type(1) tr:nth-of-type(4) a:nth-of-type(2)")
    book_url = book_url_selector["href"] if book_url_selector else None
    images_selector = "table.tabs div.bookimage img"
    img_url = soup.select_one(images_selector).get("src")
    img_name = urlparse(img_url).path.split("/")[-1]

    comments_selector = "table.tabs div.texts span.black"
    book_comments = soup.select(comments_selector)
    comments = [comment.text for comment in book_comments]

    genre_selector = "table.tabs span.d_book a"
    book_genres = soup.select(genre_selector)
    genres = [genre.text for genre in book_genres]
    book = {
        "title": title.strip(),
        "author": author.strip(),
        "download_url": urljoin(response.url, book_url) if book_url else None,
        "img_url": urljoin(response.url, img_url),
        "img_name": img_name,
        "comments": comments,
        "genres": genres
    }
    return book


def get_books_urls_from_catalog(start, end):
    book_urls = []
    attempts_conn = 0
    for page in range(start, end):
        try:
            url = f"https://tululu.org/l55/{page}"
            response = requests.get(url)
            response.raise_for_status()
            check_for_redirect(response)
            soup = BeautifulSoup(response.text, 'lxml')
            selector = ".d_book tr:nth-of-type(2) a"
            books = soup.select(selector)
            for book in books:
                book_urls.append(urljoin(response.url, book["href"]))
            attempts_conn = 0
        except requests.HTTPError:
            print("There is no such page from catalog")
            continue
        except requests.ConnectionError:
            print("Are you connected to your internet?")
            attempts_conn += 1
            if attempts_conn == 1:
                continue
            else:
                time.sleep(10)
                continue
    return book_urls


def main():
    parser = argparse.ArgumentParser(
        description="scrip can parse https://tululu.org/ site and download books with images."
    )
    parser.add_argument("-s", "--start_page", default=1, type=int, help="set up start_page")
    parser.add_argument("-e", "--end_page", default=702, type=int, help="set up end_page")
    parser.add_argument("--dest_folder", default=".", help="specify download folder for books, images, JSON")
    parser.add_argument("--skip_imgs", default=False, type=bool, help="set to 1 if you don't want download images")
    parser.add_argument("--skip_txt", default=False, type=bool, help="set to 1 if you don't want download texts")
    parser.add_argument("--json_path", default="books", help="specify json file where you want to save info about books")

    args = parser.parse_args()
    start = args.start_page
    end = args.end_page
    download_dir = args.dest_folder
    skip_imgs = args.skip_imgs
    skip_txt = args.skip_txt
    json_path = args.json_path
    attempts_conn = 0

    book_urls = get_books_urls_from_catalog(start, end)
    books = []
    for book_url in book_urls:
        try:
            response = requests.get(book_url)
            response.raise_for_status()
            check_for_redirect(response)

            book = parse_book_page(response)

            download_url = book.get("download_url")
            if not download_url:
                continue
            books.append(book)

            if not skip_txt:
                book_title = book.get("title")
                book_folder = os.path.join(download_dir, "books")
                download_txt(download_url, book_title, book_folder)

            if not skip_imgs:
                img_folder = os.path.join(download_dir, "images")
                img_name = book.get("img_name")
                img_url = book.get("img_url")
                download_image(img_url, img_name, img_folder)

            attempts_conn = 0

        except requests.HTTPError:
            print("There is no such book")
            continue
        except requests.ConnectionError:
            print("Are you connected to your internet?")
            attempts_conn += 1
            if attempts_conn == 1:
                continue
            else:
                time.sleep(10)
                continue

    books_json = json.dumps(books, ensure_ascii=False)
    books_json_path = os.path.join(download_dir, json_path)
    with open(f"{books_json_path}.json", "w") as my_file:
        my_file.write(books_json)


if __name__ == "__main__":
    main()


