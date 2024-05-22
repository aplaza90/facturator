import pytest

from facturator.domain.model import InvoiceOrder


@pytest.mark.parametrize("quantity, expected_result", [
    (150, [{'units': 3, 'price': 50, 'subtotal': 150}]),
    (120, [{'units': 2, 'price': 60, 'subtotal': 120}]),
    (330, [
        {'units': 3, 'price': 50, 'subtotal': 150},
        {'units': 3, 'price': 60, 'subtotal': 180}
    ])
])
def test_calculate_lines_happy_path(quantity, expected_result):
    lines = InvoiceOrder.calculate_lines(quantity)
    assert lines == expected_result


@pytest.mark.parametrize("quantity", [0, 20, -150])
def test_calculate_lines_exceptions(quantity):
    with pytest.raises(ValueError):
        InvoiceOrder.calculate_lines(quantity)