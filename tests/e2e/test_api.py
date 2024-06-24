import requests
from pathlib import Path
import jwt

from facturator import config


def get_login_token():
    url = config.get_api_url()
    signup_data = {
        "username": "Luis",
        "nif": "12345678A",
        "address": "Some st, some av",
        "city": "Some village",
        "province": "Madrid",
        "zip_code": "12345",
        "email": "Luis@test.com",
        "password": "admin123"
    }
    user_register = requests.post(
        f"{url}/signup",
        json=signup_data,
        headers={'Content-Type': 'application/json'}
    )
    assert user_register.status_code == 201, "Signup failed"
    login_data = {
    "username": "Luis",
    "password": "admin123"
    }
    user_login = requests.post(
        f"{url}/login", 
        json=login_data, 
        headers={'Content-Type': 'application/json'}
    )

    assert user_login.status_code == 201, "Login failed"

    token = user_login.cookies.get('token')
    assert token, "Login response does not contain a token cookie"
    
    return token


def test_protected_resource_valid_token(setup_users):
    url = config.get_api_url()
    login_token = get_login_token()
    cookies = {
        'token': login_token
    }
    response = requests.get(f"{url}/protected", cookies=cookies)
    assert response.status_code == 200


def test_protected_resource_invalid_token():
    url = config.get_api_url()
    cookies = {
        'token': 'invalid_token'
    }
    response = requests.get(f"{url}/protected", cookies=cookies)
    assert response.status_code == 401 


def test_store_orders(setup_orders):
    file_path = Path(__file__).resolve().parent.parent / 'data' / 'movs_feb.xls'
    files = {'file': open(file_path, 'rb')}

    url = config.get_api_url()
    response = requests.post(f"{url}/orders/file", files=files)
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
    response = requests.post(f"{url}/payers", json=json_data)
    assert response.status_code == 201
