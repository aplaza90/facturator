import datetime

from facturator.domain import model
from facturator.service_layer.invoice_generator import invoice


def test_generate_context():
    payer = model.Payer(
        name="test_name",
        nif="12A",
        address="test ad",
        zip_code="123",
        city="test_cty",
        province="TS"
    )

    order = model.InvoiceOrder(
                "test_name",
                date=datetime.date(2024, 4, 30),
                quantity=50,
                number='TEST-001'
            )
    order._payer = payer

    expected_dict = {
        'invoice_number': 'TEST-001',
        'invoice_date': datetime.date(2024, 4, 30),
        'client_name': 'test_name',
        'client_address': 'test ad',
        "client_zip_code": "123",
        'client_city': 'test_cty',
        "client_province": "TS",
        'client_nif': '12A',
        "professional_name": "SOME PROF",
        "professional_address": "Some st, some av",
        "professional_zip_code": "34567",
        "professional_city": "Some city",
        "professional_province": "some town",
        "professional_nif": "1234567",
        "professional_email": "example@gmail.com",
        'order_lines': [{'units': 1.0, 'price': 50, 'subtotal': 50.0}],
        'total_bi': '50€',
        'discount_qty': '50€',
        'iva_qty': '50€',
        'irpf_qty': '50€',
        'Total_a_pagar': '50€',
        'logo_path': ''
    }

    context = invoice.generate_context(order, logo_path='')
    assert context == expected_dict
