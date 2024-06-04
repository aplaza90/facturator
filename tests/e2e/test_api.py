import requests
from pathlib import Path

from facturator import config


def test_store_orders(setup_orders):
    file_path = Path(__file__).resolve().parent.parent / 'data' / 'movs_feb.xls'
    files = {'file': open(file_path, 'rb')}

    url = config.get_api_url()
    response = requests.post(f"{url}/order", files=files)
    assert response.status_code == 201


def test_add_payer(setup_payers):
    url = config.get_api_url()
    json_data = {
        "name": "Some Payer",
        "nif": "123456789",
        "address": "Some street",
        "zip_code": "12345",
        "city": "Example City",
        "province": "Example Province"
    }
    response = requests.post(f"{url}/payer", json=json_data)
    assert response.status_code == 201
