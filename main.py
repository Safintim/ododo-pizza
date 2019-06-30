import re
import os
import redis
import logging
import phonenumbers
from logs_conf import LogsHandler
from description import make_text_description_cart, make_text_description_product
from buttons import (generate_buttons_products, generate_buttons_for_all_products_from_cart,
                     generate_buttons_for_description, generate_buttons_for_confirm_personal_data)
from api_moltin import (get_product_by_id, delete_product_from_cart, get_img_by_id, push_product_to_cart_by_id,
                        get_cart, get_total_amount_from_cart, create_customer)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from dotenv import load_dotenv
from validate_email import validate_email


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
    client = update_message.chat_id
    if query_data.startswith('prev') or query_data.startswith('next'):
        params = query_data.split('/')

        if params[1] != 'None':
            reply_markup = InlineKeyboardMarkup(generate_buttons_products(params[1], params[2]))
            update_message.reply_text('Пожалуйста, выберите товар:', reply_markup=reply_markup)
            bot.delete_message(chat_id=client, message_id=update_message.message_id)
        return 'MENU'

    product_id = query_data
    product = get_product_by_id(product_id)

    img_id = product['data']['relationships']['main_image']['data']['id']
    url_img_product = get_img_by_id(img_id)

    keyboard = generate_buttons_for_description(product_id)
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_photo(
        chat_id=client,
        photo=url_img_product,
        caption=make_text_description_product(product, client),
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN)
    bot.delete_message(
        chat_id=client,
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
        handle_waiting_geo(bot, update)
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

    if update.message:
        email = update.message.text.strip()
        if validate_email(email):
            database.set(f'{update.message.chat_id}_email', email)
            handle_waiting_phone_number(bot, update)
            update_message.reply_text('\nПришлите, пожалуйста, ваш номер телефона')
            return 'WAITING_PHONE_NUMBER'
        else:
            update_message.reply_text(f'\nКажется, вы ввели неверный email: {email}\n Повторите попытку')
            update_message = None
    return 'WAITING_EMAIL'


def handle_waiting_phone_number(bot, update):
    update_message = update.message or update.callback_query.message

    if update.message.text == database.get(f'{update.message.chat_id}_email'):
        return 'WAITING_PHONE_NUMBER'

    if re.match(r'^\+{0,1}\d+', update.message.text):
        phone_number = update.message.text
        phone_number = phonenumbers.parse(phone_number, 'RU')

        if phonenumbers.is_valid_number(phone_number):
            database.set(f'{update.message.chat_id}_phone', phone_number.national_number)

            keyboard = generate_buttons_for_confirm_personal_data()
            reply_markup = InlineKeyboardMarkup(keyboard)

            email = database.get(f'{update.message.chat_id}_email')
            update_message.reply_text(f'\nВаш email: {email}\n'
                                      f'Ваш номер телефона: {phone_number.national_number}',
                                      reply_markup=reply_markup)
            return 'CONFIRM_PERSONAL_DATA'
        else:
            update_message.reply_text(f'\nКажется, вы неправильно набрали номер: {phone_number.national_number}'
                                      '\n Повторите попытку')
            update_message = None
    else:
        update_message.reply_text('\nДолжны быть цифры')

    return 'WAITING_PHONE_NUMBER'


def handle_confirm_personal_data(bot, update):
    update_message = update.message or update.callback_query.message
    if update.callback_query.data == 'Верно':
        name = database.get(f'{update_message.chat_id}_phone')
        email = database.get(f'{update_message.chat_id}_email')
        create_customer(name, email)
        update_message.reply_text(f'В скором времени я свяжусь с вами')
        handle_start(bot, update)
        return 'MENU'
    elif update.callback_query.data == 'Неверно':
        handle_waiting_geo(bot, update)
        update_message.reply_text('\nПришлите, пожалуйста, ваш email')
        return 'WAITING_EMAIL'
    return 'CONFIRM_PERSONAL_DATA'


def handle_users_reply(bot, update):
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

    states_functions = {
        'START': handle_start,
        'MENU': handle_menu,
        'DESCRIPTION': handle_description,
        'CART': handle_cart,
        'WAITING_GEO': handle_waiting_geo,
        'WAITING_PHONE_NUMBER': handle_waiting_phone_number,
        'CONFIRM_PERSONAL_DATA': handle_confirm_personal_data
    }

    state_handler = states_functions[user_state]
    next_state = state_handler(bot, update)
    database.set(chat_id, next_state)


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
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    dispatcher.add_error_handler(handle_error)
    updater.start_polling()


if __name__ == '__main__':
    main()
