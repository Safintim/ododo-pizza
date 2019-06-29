from api_moltin import get_product_from_cart


def make_text_description_cart(cart, total_amount):
    parts_text = []
    for product in cart['data']:

        name = product['name']
        description = product['description']
        price = product['meta']['display_price']['with_tax']['unit']['formatted']
        quantity = product['quantity']
        total_amount_product = product['value']['amount']

        parts_text.append(f'*{name}*')
        parts_text.append(f'_{description}_')
        parts_text.append(f'Цена *{price}* рублей')
        parts_text.append(f'Количество пицц: *{quantity}*, *{total_amount_product:.2f} РУБ* рублей\n')

    total_amount = total_amount['data']['meta']['display_price']['with_tax']['formatted']
    parts_text.append(f'*Цена за все пиццы в корзине: {total_amount} РУБ*')
    return '\n'.join(parts_text)


def make_text_description_product(product, client):
    product = product['data']

    product_from_cart = get_product_from_cart(product['id'], client)

    quantity_product_in_cart = 0
    total_amount_product_in_cart = 0
    parts_text = []
    if product_from_cart:
        quantity_product_in_cart = product_from_cart['quantity']
        total_amount_product_in_cart = product_from_cart['value']['amount']

    name = product['name']
    price = product['price'][0]['amount']
    description = product['description']

    parts_text.append(f'*{name}*\n')
    parts_text.append(f'Стоимость: *{price} рублей*\n')
    parts_text.append(f'_{description}_\n')
    parts_text.append(f'Количество пицц в корзине: _{quantity_product_in_cart}_\n')
    parts_text.append(f'К оплате: _{total_amount_product_in_cart:.2f}_\n')

    return '\n'.join(parts_text)
