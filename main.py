import requests
from pathlib import Path


url = "https://tululu.org/txt.php?id=32168"
Path("/books").mkdir(parents=True, exist_ok=True)

response = requests.get(url)
response.raise_for_status()

filename = 'dvmn.txt'

with open(f'book/{filename}', 'wb') as file:
	file.write(response.content)
