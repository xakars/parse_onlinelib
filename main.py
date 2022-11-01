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


def download_txt(url, filename, folder="books/"):
    Path(folder).mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    pure_filename = sanitize_filename(filename)
    title = f"{pure_filename}.txt"
    path_to_save = os.path.join(folder, title)
    with open(path_to_save, "wb") as file:
        file.write(response.content)


def download_image(url, filename, folder="images/"):
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

def get_books_from_catalog(start, end):
    book_urls = []
    for page in range(start, end):
        url = f"https://tululu.org/l55/{page}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        selector = ".d_book tr:nth-of-type(2) a"
        books = soup.select(selector)
        for book in books:
            book_urls.append(urljoin(response.url, book["href"]))
    return book_urls


def main():
    parser = argparse.ArgumentParser(
        description="scrip can parse https://tululu.org/ site and download books with images."
    )
    parser.add_argument("-s", "--start_id", default=1, type=int, help="set up start_value")
    parser.add_argument("-e", "--end_id", default=10, type=int, help="set up end_value")
    args = parser.parse_args()
    start = args.start_id
    end = args.end_id
    attempts_conn = 0

    book_urls = get_books_from_catalog(start, end)
    books = []
    for book_url in book_urls:
        try:
            response = requests.get(book_url)
            response.raise_for_status()
            check_for_redirect(response)

            book = parse_book_page(response)

            book_title = book.get("title")
            download_url = book.get("download_url")
            if not download_url:
                continue

            books.append(book)

            download_txt(download_url, book_title)

            img_name = book.get("img_name")
            img_url = book.get("img_url")
            download_image(img_url, img_name)

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
    with open("books.json", "w") as my_file:
        my_file.write(books_json)


if __name__ == "__main__":
    main()
