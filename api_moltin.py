import os
import re
import json
import random
import requests
from tools import convert_str_to_slug, download_and_save_img
from pprint import pprint
from dotenv import load_dotenv


PROXIES = {
    'http': 'http://213.211.146.13:3128',
}

TOKEN = os.environ.get('ACCESS_TOKEN_MOLTIN')


def is_token_works(func):
    def decorator(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
        except requests.HTTPError as error:
            response = None
            if error.response.status_code == 401:
                global TOKEN
                TOKEN = get_access_token()
                response = func(*args, **kwargs)
        return response
    return decorator


@is_token_works
def add_img_to_product(product_id, img_id):
    headers = get_headers()
    headers.update({'Content-Type': 'application/json'})

    data = {
        'type': 'main_image',
        'id': img_id
    }

    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
    response = requests.post(url, headers=headers, json={'data': data}, proxies=PROXIES)
    print(response.json())
    response.raise_for_status()
    return response.json()


@is_token_works
def create_customer(name, email):
    url = 'https://api.moltin.com/v2/customers'

    headers = get_headers()
    headers.update({'Content-Type': 'application/json'})
    payload = {
        'data': {
            'type': 'customer',
            'name': name,
            'email': email
        }
    }

    response = requests.post(url, headers=headers, json=payload, proxies=PROXIES)
    response.raise_for_status()
    return response.json()


@is_token_works
def create_file(file):
    headers = get_headers()

    print(file)
    with open(file, 'rb') as f:
        files = {
            'file': f,
            'public': True
        }

        url = 'https://api.moltin.com/v2/files'
        response = requests.post(url, headers=headers, files=files, proxies=PROXIES)
        pprint(response.json())
        response.raise_for_status()
    return response.json()


@is_token_works
def create_field(field_data, flow_id):
    headers = get_headers()
    headers.update({'Content-Type': 'application/json'})

    data = {
        'type': 'field',
        'name': field_data['name'],
        'slug': field_data['slug'],
        'field_type': field_data['type'],
        'description': field_data['description'],
        'required': True,
        'unique': False,
        'enabled': True,
        'relationships': {
            'flow': {
                'data': {
                    'type': 'flow',
                    'id': flow_id
                }
            }
        }
    }

    url = 'https://api.moltin.com/v2/flows'
    response = requests.post(url, headers=headers, json={'data': data}, proxies=PROXIES)
    response.raise_for_status()
    return response.json()


@is_token_works
def create_flow(name_flow, description):
    headers = get_headers()
    headers.update({'Content-Type': 'application/json'})

    data = {
        'type': 'flow',
        'name': name_flow,
        'slug': name_flow,
        'description': description,
        'enabled': True
    }

    url = 'https://api.moltin.com/v2/flows'
    response = requests.post(url, headers=headers, json={'data': data}, proxies=PROXIES)
    response.raise_for_status()
    return response.json()


def create_flow_pizzeria():
    fields = [
        {
            'name': 'address',
            'slug': 'address',
            'type': 'address',
            'desription': 'Pizzeria address'
        },
        {
            'name': 'alias',
            'slug': 'alias',
            'type': 'string',
            'description': 'Pizzeria name'
        },
        {
            'name': 'longitude',
            'slug': 'longitude',
            'type': 'float',
            'description': 'Longitude'
        },
        {
            'name': 'latitude',
            'slug': 'latitude',
            'type': 'float',
            'description': 'Latitude'
        },
    ]

    flow_id = create_flow('Pizzeria', 'Ododo Pizzeria')['data']['id']
    for field in fields:
        create_field(field, flow_id)


@is_token_works
def create_product(product_data):
    headers = get_headers()
    headers.update({'Content-Type': 'application/json'})
    product_data = {
        'type': 'product',
        'name': product_data['name'],
        'slug': convert_str_to_slug(product_data['name']),
        'sku': f'{product_data["name"]}-{random.randint(10, 10000)}',
        'description': product_data['description'],
        'manage_stock': False,
        'price': [
            {
                'amount': product_data['price'],
                'currency': 'RUB',
                'includes_tax': False
            }
        ],
        'status': 'live',
        'commodity_type': 'physical'
    }

    url = 'https://api.moltin.com/v2/products'
    response = requests.post(url, headers=headers, json={'data': product_data}, proxies=PROXIES)
    response.raise_for_status()
    return response.json()


@is_token_works
def create_products(file='menu.json'):
    with open(file, 'r') as file:
        products = json.load(file)

    for product in products:
        product_id = create_product(product)['data']['id']
        url_img_product = product['product_image']['url']
        path_to_img = download_and_save_img(url_img_product, product['name'])
        img_id = create_file(path_to_img)['data']['id']
        add_img_to_product(product_id, img_id)


@is_token_works
def delete_product_from_cart(client_id, product_id):
    url = f'https://api.moltin.com/v2/carts/{client_id}/items/{product_id}'
    response = requests.delete(url, headers=get_headers(), proxies=PROXIES)
    response.raise_for_status()
    return response.json()


def get_access_token():
    payload = {
        'client_id': os.environ.get('CLIENT_ID_MOLTIN'),
        'client_secret': os.environ.get('CLIENT_SECRET_MOLTIN'),
        'grant_type': 'client_credentials'
    }
    url = 'https://api.moltin.com/oauth/access_token'
    response = requests.post(url, data=payload, proxies=PROXIES)
    response.raise_for_status()
    return response.json()['access_token']


@is_token_works
def get_cart(client_id):
    url = f'https://api.moltin.com/v2/carts/{client_id}/items'
    response = requests.get(url, headers=get_headers(), proxies=PROXIES)
    response.raise_for_status()
    return response.json()


def get_headers():
    return {
        'Authorization': f'Bearer {TOKEN}',
    }


@is_token_works
def get_customer(client_id):
    url = f'https://api.moltin.com/v2/customers/{client_id}'
    response = requests.get(url, headers=get_headers(), proxies=PROXIES)
    response.raise_for_status()
    return response.json()


@is_token_works
def get_customers():
    url = 'https://api.moltin.com/v2/customers/'
    response = requests.get(url, headers=get_headers(), proxies=PROXIES)
    response.raise_for_status()
    return response.json()


@is_token_works
def get_img_by_id(id):
    url = f'https://api.moltin.com/v2/files/{id}'
    response = requests.get(url, headers=get_headers(), proxies=PROXIES)
    response.raise_for_status()
    return response.json()['data']['link']['href']


@is_token_works
def get_products():
    url = 'https://api.moltin.com/v2/products'
    response = requests.get(url, headers=get_headers(), proxies=PROXIES)
    response.raise_for_status()
    return response.json()


@is_token_works
def get_product_by_id(id):
    url = f'https://api.moltin.com/v2/products/{id}'
    response = requests.get(url, headers=get_headers(), proxies=PROXIES)
    response.raise_for_status()
    return response.json()


def get_product_from_cart(product_id, client_id):
    for pr in get_cart(client_id)['data']:
        if pr['product_id'] == product_id:
            return pr


@is_token_works
def get_total_amount_from_cart(client_id):
    url = f'https://api.moltin.com/v2/carts/{client_id}'
    response = requests.get(url, headers=get_headers(), proxies=PROXIES)
    response.raise_for_status()
    return response.json()


@is_token_works
def push_product_to_cart_by_id(product_id, client_id, amount):
    headers = get_headers()
    headers.update({'Content-Type': 'application/json'})

    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': int(amount)
        }
    }
    url = f'https://api.moltin.com/v2/carts/{client_id}/items'
    response = requests.post(url, headers=headers, json=payload, proxies=PROXIES)
    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    pprint(create_products())
    pprint(create_flow_pizzeria())


if __name__ == '__main__':
    main()
