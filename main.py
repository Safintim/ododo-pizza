import re
import os
import json
import redis
import logging
import yandex_geocoder
from logs_conf import LogsHandler
from description import make_text_description_cart, make_text_description_product, make_msg_depending_on_distance
from buttons import (generate_buttons_products, generate_buttons_for_all_products_from_cart,
                     generate_buttons_for_description)
from api_moltin import (get_product_by_id, delete_product_from_cart, get_img_by_id, push_product_to_cart_by_id,
                        get_cart, get_total_amount_from_cart, get_entries, push_address_to_customer_address,
                        get_entries_by_id)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, LabeledPrice
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, PreCheckoutQueryHandler
from dotenv import load_dotenv
from geopy.distance import distance


logger = logging.getLogger(__name__)


database = None


def handle_start(bot, update):
    update_message = update.message or update.callback_query.message
    reply_markup = InlineKeyboardMarkup(generate_buttons_products())
    update_message.reply_text('Пожалуйста, выберите товар:', reply_markup=reply_markup)
    return 'MENU'


def handle_menu(bot, update):
    update_message = update.message or update.callback_query.message
    query_data = update.callback_query.data
    client_id = update_message.chat_id
    if query_data.startswith('prev') or query_data.startswith('next'):
        _, *limit_offset = query_data.split('/')

        if limit_offset[0] != 'None':
            reply_markup = InlineKeyboardMarkup(generate_buttons_products(limit_offset[0], limit_offset[1]))
            update_message.reply_text('Пожалуйста, выберите товар:', reply_markup=reply_markup)
            bot.delete_message(chat_id=client_id, message_id=update_message.message_id)
        return 'MENU'

    product_id = query_data
    product = get_product_by_id(product_id)

    img_id = product['data']['relationships']['main_image']['data']['id']
    url_img_product = get_img_by_id(img_id)

    keyboard = generate_buttons_for_description(product_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_photo(
        chat_id=client_id,
        photo=url_img_product,
        caption=make_text_description_product(product, client_id),
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN)
    bot.delete_message(
        chat_id=client_id,
        message_id=update_message.message_id)

    return 'DESCRIPTION'


def handle_description(bot, update):
    client_id = update.callback_query.message.chat_id
    regex = r'[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}'
    if update.callback_query.data == 'В меню':
        handle_start(bot, update.callback_query)
        return 'MENU'
    elif re.match(regex, update.callback_query.data):
        amount, product = 1, update.callback_query.data
        push_product_to_cart_by_id(product, client_id, amount)
        return 'DESCRIPTION'


def handle_cart(bot, update):
    client_id = update.callback_query.message.chat_id
    update_message = update.message or update.callback_query.message

    if update.callback_query.data == 'В меню':
        handle_start(bot, update.callback_query)
        return 'MENU'
    elif update.callback_query.data == 'Оплата':
        update_message.reply_text('\nПришлите, пожалуйста, ваш адрес текстом или геолокацию')
        return 'WAITING_GEO'
    else:
        product_id = update.callback_query.data
        delete_product_from_cart(client_id, product_id)

    cart = get_cart(client_id)
    total_amount = get_total_amount_from_cart(client_id)

    text = make_text_description_cart(cart, total_amount)

    keyboard = generate_buttons_for_all_products_from_cart(client_id)
    keyboard.append([InlineKeyboardButton('В меню', callback_data='В меню')])
    keyboard.append([InlineKeyboardButton('Оплата', callback_data='Оплата')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update_message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return 'CART'


def handle_waiting_geo(bot, update):
    update_message = update.message or update.callback_query.message

    if update.callback_query:
        if update.callback_query.data.startswith('Самовывоз'):
            nearest_pizzeria = json.loads(database.get('nearest_pizzeria'))['address']
            update_message.reply_text(f'Адрес ближайшей пиццерии: {nearest_pizzeria}. До свидания')
            handle_start(bot, update)
            return 'START'
        elif update.callback_query.data.startswith('Доставка'):
            handle_delivery(bot, update)
            return 'DELIVERY'

    if update.message:
        try:
            client_position = yandex_geocoder.Client.coordinates(update_message.text)
        except yandex_geocoder.exceptions.YandexGeocoderAddressNotFound:
            update_message.reply_text('Не могу распознать этот адрес')
    elif not update.callback_query:
        client_position = (update_message.location.latitude, update_message.location.longitude)

    client_position = (float(client_position[0]), float(client_position[1]))
    pizzerias = get_entries()['data']
    nearest_pizzeria = min(pizzerias, key=lambda piz: distance(client_position, (piz['lon'], piz['lat'])).km)
    distance_to_nearest_pizzeria = distance((nearest_pizzeria['lon'], nearest_pizzeria['lat']), client_position).km

    id_address_client = push_address_to_customer_address(client_position)['data']['id']

    keyboard = [
        [InlineKeyboardButton('Самовызов', callback_data='Самовызов')],
        [InlineKeyboardButton('Доставка', callback_data=f'Доставка/{id_address_client}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = make_msg_depending_on_distance(distance_to_nearest_pizzeria, nearest_pizzeria)
    update_message.reply_text(msg, reply_markup=reply_markup)
    database.set('nearest_pizzeria', json.dumps(nearest_pizzeria))
    return 'WAITING_GEO'


def handle_delivery(bot, update):
    update_message = update.message or update.callback_query.message
    query = update.callback_query.data
    client_id = update_message.chat_id
    nearest_pizzeria = json.loads(database.get('nearest_pizzeria'))
    cart = get_cart(client_id)
    total_amount = get_total_amount_from_cart(client_id)
    total_amount_rub = total_amount['data']['meta']['display_price']['with_tax']['amount']
    if query.startswith('Доставка'):
        _, id_address_client = query.split('/')    
        entries = get_entries_by_id(id_address_client)['data']
        lon = entries['lon']
        lat = entries['lat']
        bot.send_message(chat_id=nearest_pizzeria['courier'],
                         text=make_text_description_cart(cart, total_amount),
                         parse_mode=ParseMode.MARKDOWN)
        bot.send_location(chat_id=nearest_pizzeria['courier'], latitude=lat, longitude=lon)

        keyboard = [
            [InlineKeyboardButton('Оплатить', callback_data=f'{total_amount_rub}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update_message.reply_text('Для оплаты нажмите кнопку Оплатить', reply_markup=reply_markup)

    if str(update.callback_query.data) == str(total_amount_rub):
        handle_without_shipping(bot, update)
        return 'WITHOUT_SHIPPING'
    return 'DELIVERY'


def handle_without_shipping(bot, update):
    update_message = update.message or update.callback_query.message
    chat_id = update_message.chat_id
    title = 'Payment Example'
    description = 'Payment Example using python-telegram-bot'
    payload = 'Payload'
    provider_token = os.environ.get('PAYMENT_TOKEN_TRANZZO')
    start_parameter = 'test-payment'
    currency = 'RUB'
    price = float(update.callback_query.data)
    prices = [LabeledPrice('Test', int(price * 100))]
    bot.send_invoice(chat_id, title, description, payload,
                     provider_token, start_parameter, currency, prices)
    return 'START'


def handle_precheckout(bot, update):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Payload':

        bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=False,
                                      error_message='Что-то пошло не так...')
        handle_start(bot, update)
    else:
        bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)


def handle_successful_payment(bot, update):
    update.message.reply_text('Спасибо за покупку')


def handle_users_reply(bot, update, job_queue):
    database = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    elif user_reply == 'Корзина':
        user_state = 'CART'
        database.set(chat_id, user_state)
    else:
        user_state = database.get(chat_id)

    if user_reply.startswith('Доставка'):
        job_queue.run_once(handle_order, 10, context=chat_id)

    states_functions = {
        'START': handle_start,
        'MENU': handle_menu,
        'DESCRIPTION': handle_description,
        'CART': handle_cart,
        'WAITING_GEO': handle_waiting_geo,
        'DELIVERY': handle_delivery,
        'WITHOUT_SHIPPING': handle_without_shipping,
    }

    state_handler = states_functions[user_state]
    next_state = state_handler(bot, update)
    database.set(chat_id, next_state)


def handle_order(bot, job):
    bot.send_message(chat_id=job.context,
                     text='Приятного аппетита! *место для рекламы*\n\n'
                          '*сообщение что делать если пицца не пришла*',
                     parse_mode=ParseMode.MARKDOWN)


def get_database_connection():
    global database
    if database is None:
        database = redis.Redis(
            host=os.environ.get("REDIS_HOST"),
            port=os.environ.get("REDIS_PORT"),
            password=os.environ.get("REDIS_PASSWORD"),
            decode_responses=True,
            charset='utf-8')
    return database


def handle_error(bot, update, error):
    try:
        logging.error(f'(pizza) {update}\n {error}')
        update.message.reply_text(text='Простите, возникла ошибка.')
    except Exception as err:
        print(err)
        logging.critical(f'(pizza) {err}')


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO,
                        handlers=[LogsHandler()])

    logger.info('(pizza) OdodoPizza запущен')

    load_dotenv()

    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply, pass_job_queue=True))
    dispatcher.add_handler(MessageHandler(Filters.location, handle_users_reply,
                                          pass_job_queue=True,
                                          edited_updates=True))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply, pass_job_queue=True))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply, pass_job_queue=True))
    dispatcher.add_handler(PreCheckoutQueryHandler(handle_precheckout))
    dispatcher.add_handler(MessageHandler(Filters.successful_payment, handle_successful_payment))
    dispatcher.add_error_handler(handle_error)
    updater.start_polling()


if __name__ == '__main__':
    main()
