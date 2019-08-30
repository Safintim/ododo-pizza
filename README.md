# ododo-pizza

## Описание

ododo-pizza - это телегамм_бот-магазин. В данной демке продаем пиццу.

Есть сеть пиццерий. Пользователь выбирает товар, делает заказ, присылает свою гео-позицию. 
Пользователю предлагается самовызов или доставка. При доставке чек и гео-позиция пользователя отправляется 
курьеру в телеграмм (по умолчанию вам в чат). 

[API Motlin](https://docs.moltin.com/api/)

## Пример работы

### #1

На гифке видно, что нажатии кнопки "Доставка" присылается геопозиция и счет клиента. А также 
Через 10 секунд (для теста) время присылается сообщение "Что делать, если пицца не была доставлена".

![Alt Text](http://ipic.su/img/img7/fs/pizza.1562246120.gif)

### #2

![Alt Text](http://ipic.su/img/img7/fs/pizza2.1562246594.gif)

## Требования

Для запуска скрипта требуется:

*Python 3.6*

## Как установить

1. Установить Python3:

(Windows):[python.org/downloads](https://www.python.org/downloads/windows/)

(Debian):

```sh
sudo apt-get install python3
sudo apt-get install python3-pip
```

2. Установить зависимости и скачать сам проект:

```sh
git clone https://github.com/Safintim/fish-shop.git
cd quiz-bot
pip3 install -r requirements.txt
```

3. Зарегистрироваться на [Redislabs](https://redislabs.com/) и получить адрес базы данных.

4. Персональные настройки:

Скрипт берет настройки из .env файла, где указаны токен телеграм-бота, токен чат-логгер-бота, хост, порт, пароль базы данных, а также токен, id и секретный ключ к moltin. Создайте файл .env вида:

```.env
ACCESS_TOKEN_MOLTIN=your_token
CLIENT_ID_MOLTIN=your_id
CLIENT_SECRET_MOLTIN=your_secret
TELEGRAM_BOT_TOKEN=your_token
LOGGER_BOT_TOKEN=your_token
LOGS_RECEIVER_ID=your_chat_id
REDIS_HOST=your_redis_host
REDIS_PASSWORD=your_redis_password
REDIS_PORT=your_redis_port
PROXY_IP=ip_proxy_server
PROXY_PROTOCOL=protocol_proxy_server
```

## Как использовать

Демо-бот использует данные от додо-пиццы. В проекте должен быть файл c продуктами (menu.json по умолчанию) ввида:

```json
[
    {
        "id": 20,
        "name": "Чизбургер-пицца",
        "description": "мясной соус болоньезе, моцарелла, лук, соленые огурчики, томаты, соус бургер", "food_value": {
            "fats": "6,9",
            "proteins": "7,5",
            "carbohydrates": "23,72",
            "kiloCalories": "188,6",
            "weight": "470±50"
            },
        "culture_name": "ru-RU",
        "product_image": {
            "url": "https://dodopizza-a.akamaihd.net/static/Img/Products/Pizza/ru-RU/1626f452-b56a-46a7-ba6e-c2c2c9707466.jpg",
            "height": 1875,
            "width": 1875
            },
        "price": 395
    },
    ...
    {
        ...
    },
]
```

А также файл с адресами пиццерий (address.json по умолчанию) ввида:

```json
[
    {
        "id": "00000351-0000-0000-0000-000000000000",
        "alias": "Афимолл",
        "address": {
            "full": "Москва, набережная Пресненская дом 2",
            "city": "Москва",
            "street": "Пресненская",
            "street_type": "набережная",
            "building": "2"
        },
        "coordinates": {
            "lat": "55.749299",
            "lon": "37.539644"
        }
    },
    ...
    {
        ...
    },
]
```

```sh
python3 load_products_to_moltin.py
```

```sh
python3 main.py
```

## Демо-боты

Данный бот готов к использованию. Пример работы указан на гифке выше.

* **_@ododo_pizza_bot** - телеграм-бот-магазин
* **_@devmanlogging_bot_** - телеграм-логгер-бот, данный бот выполняет мониторинг телеграмм бота.
В случае ошибки придет уведомление о том, что "бот упал" и почему "бот упал",
 а также при запуске бот сообщит о запуске.

![Alt Text](http://ipic.su/img/img7/fs/quiz-log.1559419941.png)