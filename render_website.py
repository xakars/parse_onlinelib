import json
import os
from pathlib import Path
from more_itertools import chunked
from http.server import HTTPServer, SimpleHTTPRequestHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)

template = env.get_template('template.html')

with open("books/books.json", "r") as file:
    books = json.load(file)

rows_per_page = 2
books_row = list(chunked(books, rows_per_page))
books_per_page = 10
chunked_books = list(chunked(books_row, books_per_page))

Path("pages").mkdir(parents=True, exist_ok=True)
index_dir = "pages"

for index, books in enumerate(chunked_books, 1):
    file_name = f"index{index}.html"
    path_to_keep = os.path.join(index_dir, file_name)
    with open(path_to_keep, "w", encoding="utf8") as file:
        rendered_page = template.render(
            books_row=books,
            pages_count=len(chunked_books),
            current_page = index
        )
        file.write(rendered_page)

server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
server.serve_forever()