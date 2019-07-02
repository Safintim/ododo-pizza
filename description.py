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


def make_msg_depending_on_distance(distance_to_nearest_pizzeria, nearest_pizzeria):
    if distance_to_nearest_pizzeria <= 0.5:
        text = (f'Может заберете пиццу из нашей пиццерии неподалеку? Она всего в '
                f'{int(distance_to_nearest_pizzeria*100)}м от вас.'
                f'Вот её адрес: {nearest_pizzeria["address"]}\n\nА ожем бесплатно доставить')
    elif distance_to_nearest_pizzeria <= 5:
        text = (f'Похоже придется ехать до вас. {distance_to_nearest_pizzeria:.2f}км'
                f' от вас. Доставка будет стоить 100рублей. Доставка или самовызов?')
    elif distance_to_nearest_pizzeria <= 20:
        text = (f'Похоже придется ехать до вас. {distance_to_nearest_pizzeria:.2f}км'
                f' от вас. Доставка будет стоить 300рублей. Доставка или самовызов?')
    else:
        text = (f'Очень далеко. {int(distance_to_nearest_pizzeria)}км'
                f' от вас. Только самовызов')

    return text
