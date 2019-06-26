import json
from pprint import pprint

with open('addresses.json', 'r') as file:
    addresses = json.load(file)

with open('menu.json', 'r') as file:
    menu = json.load(file)

pprint(addresses)
pprint(menu)
