import os
import re

import pathlib
import requests
import urllib.parse as urlparse

IMAGE_PATH = 'images/'


def convert_cyrillic_to_latin(s):
    symbols = ('абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
               'abvgdeejzijklmnoprstufhzcss_y_eua')

    s = s.lower()
    trantab = s.maketrans(symbols[0], symbols[1])

    return s.translate(trantab)


def convert_str_to_slug(s):
    return re.sub(r'[\W\s]+', '_', convert_cyrillic_to_latin(s))


def download_and_save_img(url, filename):
    pathlib.Path(IMAGE_PATH).mkdir(exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    filename = f'{convert_cyrillic_to_latin(filename)}{os.path.splitext(url)[1]}'
    print(filename)
    with open(IMAGE_PATH+filename, 'wb') as f:
        f.write(response.content)

    return IMAGE_PATH+filename


def get_query_params_from_url(url):
    parsed = urlparse.urlparse(url)
    return urlparse.parse_qs(parsed.query)['page[limit]'][0], urlparse.parse_qs(parsed.query)['page[offset]'][0]
