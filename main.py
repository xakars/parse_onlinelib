import requests
import os
import argparse
import time
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
    book_selector = soup.find("div", {"id": "content"})
    about_book = book_selector.find("h1")
    title, author = about_book.text.split("::")
    book_url_selector = book_selector.find("a", string="скачать txt")
    book_url = book_url_selector["href"] if book_url_selector else None
    images_selector = "table.tabs div.bookimage img"
    img_url = soup.select_one(images_selector).get("src")
    img_name = urlparse(img_url).path.split("/")[-1]

    comments_selector = "table.tabs div.texts span.black"
    book_comments = soup.select(comments_selector)
    comments = [comment.text for comment in book_comments]

    genre_selector = "table.tabs span.d_book a"
    book_genres = soup.select(genre_selector)
    genrs = [genre.text for genre in book_genres]

    book = {
        "title": title.strip(),
        "author": author.strip(),
        "book_url": urljoin(response.url, book_url),
        "img_url": urljoin(response.url, img_url),
        "img_name": img_name,
        "comments": comments,
        "genrs": genrs
    }
    return book


def main():
    base_url = "https://tululu.org/"
    parser = argparse.ArgumentParser(
        description="scrip can parse https://tululu.org/ site and download books with images."
    )
    parser.add_argument("-s", "--start_id", default=1, type=int, help="set up start_value")
    parser.add_argument("-e", "--end_id", default=10, type=int, help="set up end_value")
    args = parser.parse_args()
    start = args.start_id
    end = args.end_id
    attempts_conn = 0
    for book_id in range(start, end):
        try:
            url = f"{base_url}b{book_id}/"
            response = requests.get(url)
            response.raise_for_status()
            check_for_redirect(response)

            book = parse_book_page(response)

            book_title = book.get("title")
            book_url = book.get("book_url")
            if not book_url:
                continue
            download_txt(book_url, book_title)

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


if __name__ == "__main__":
    main()
