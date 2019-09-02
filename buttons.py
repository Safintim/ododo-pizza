from api_moltin import get_products, get_cart
from telegram import InlineKeyboardButton
from tools import get_query_params_from_url


def generate_buttons_products(limit=6, offset=0):
    keyboard = []
    products = get_products(limit, offset)
    next = prev = 'None/None'
    if products['links'].get('prev'):
        limit, offset = get_query_params_from_url(products['links']['prev'])
        prev = f'{limit}/{offset}'
    if products['links'].get('next'):
        limit, offset = get_query_params_from_url(products['links']['next'])
        next = f'{limit}/{offset}'
    for product in products['data']:
        keyboard.append([InlineKeyboardButton(product['name'], callback_data=product['id'])])

    keyboard.append([
        InlineKeyboardButton('Пред', callback_data=f'prev/{prev}'),
        InlineKeyboardButton('След', callback_data=f'next/{next}')
        ])
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='Корзина')])
    return keyboard


def generate_buttons_for_all_products_from_cart(client_id):
    keyboard = []
    for product in get_cart(client_id)['data']:
        keyboard.append([InlineKeyboardButton(f'Убрать из корзины {product["name"]}',
                                              callback_data=product['id'])])

    return keyboard


def generate_buttons_for_description(product_id):
    keyboard = [
        [InlineKeyboardButton('Положить в корзину', callback_data=f'{product_id}')],
        [InlineKeyboardButton('Корзина', callback_data='Корзина')],
        [InlineKeyboardButton('В меню', callback_data='В меню')]
      ]

    return keyboard


def generate_buttons_for_confirm_personal_data():
    keyboard = [
                [InlineKeyboardButton('Верно', callback_data='Верно')],
                [InlineKeyboardButton('Неверно', callback_data='Неверно')]
            ]

    return keyboard
