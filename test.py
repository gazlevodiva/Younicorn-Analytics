import requests
from bs4 import BeautifulSoup

api_key = ""
url = f"https://api.similarweb.com/v1/website/%7Bdomain.com%7D/general-data/description?api_key={api_key}&format=json"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

print(response.text)



# Парсим HTML страницу
soup = BeautifulSoup(response.text, 'html.parser')

print( soup )
