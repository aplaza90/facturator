import pytest
from pathlib import Path

from facturator.service_layer import file_handler


@pytest.fixture
def sample_instance():
    file_path = Path(__file__).resolve().parent.parent / 'data' / 'movs_feb.xls'
    excel_handler = file_handler.ExcelFileHandler(file_path)
    return excel_handler


@pytest.mark.parametrize("concept, expected_name", [
    ("BIZUM DE Pepe CONCEPTO pepazo", "Pepe"),
    ("TRANSFERENCIA DE Fede Juanra, CONCEPTO algo", "Fede Juanra"),
    ("Payment via credit card", None),
    ("", None)
])
def test_get_name_from_concept(sample_instance, concept, expected_name):
    assert sample_instance.get_name_from_concept(concept) == expected_name


def test_get_df_from_excel(sample_instance):
    df = sample_instance._get_df_from_excel()
    assert df['Importe'][0] == -86.66
    assert df['Importe'].sum() == 1390.74


def test_get_orders_from_df(sample_instance):
    orders = sample_instance.get_orders_from_file()
    assert len(orders) == 16
    assert orders[4].payer_name == 'CLIENT_13'
