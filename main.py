import json

with open('addresses.json', 'r') as file:
    addresses = json.load(file)

with open('menu.json', 'r') as file:
    menu = json.load(file)

print(addresses)
print(menu)
