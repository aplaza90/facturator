import datetime

from facturator.domain import model
from facturator.service_layer.invoice_generator import invoice


def test_generate_context():
    payer = model.Payer(
        name="test_name",
        address=model.CompleteAddress(
            "test ad", "123", "test_cty", "TS"
        ),
        nif="12A"
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
        'client_city': 'test_cty',
        'client_nif': '12A',
        'professional_name': 'Some Professional',
        'professional_address': '5678 Some Avenue',
        'professional_city': 'Almendralejo, SP',
        'professional_nif': '987654321',
        'professional_email': 'some.pro@example.com',
        'order_lines': [{'units': 1.0, 'price': 50, 'subtotal': 50.0}],
        'total_bi': '50€',
        'discount_qty': '0.00€',
        'iva_qty': '0.00€',
        'irpf_qty': '0.00€',
        'Total_a_pagar': '50€',
        'logo_path': ''
    }

    context = invoice.generate_context(order, logo_path='')
    assert context == expected_dict