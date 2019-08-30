from api_moltin import create_products, create_flow_from_fields, push_addresses_to_pizzeria
from dotenv import load_dotenv


def load_products():
    load_dotenv()
    fields_for_pizzeria = [
        {
            'name': 'address',
            'slug': 'address',
            'type': 'string',
            'description': 'pizzeria address'
        },
        {
            'name': 'alias',
            'slug': 'alias',
            'type': 'string',
            'description': 'pizzeria name'
        },
        {
            'name': 'longitude',
            'slug': 'lon',
            'type': 'float',
            'description': 'Longitude'
        },
        {
            'name': 'latitude',
            'slug': 'lat',
            'type': 'float',
            'description': 'Latitude'
        },
        {
            'name': 'courier',
            'slug': 'courier',
            'type': 'integer',
            'description': 'telegram id'
        },
    ]
    fields_for_customer_address = [
        {
            'name': 'longitude',
            'slug': 'lon',
            'type': 'float',
            'description': 'Longitude'
        },
        {
            'name': 'latitude',
            'slug': 'lat',
            'type': 'float',
            'description': 'Latitude'
        },
    ]

    create_products()
    create_flow_from_fields(fields_for_pizzeria, 'Pizzeria', 'Ododo pizzeria')
    push_addresses_to_pizzeria()
    create_flow_from_fields(fields_for_customer_address, 'customer_address', 'customer address')


if __name__ == '__main__':
    load_products()
