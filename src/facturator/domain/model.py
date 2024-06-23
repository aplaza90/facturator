
class User:
    def __init__(
            self, username, public_id, nif, address, zip_code, city, province, email, password
    ):
        self.username = username
        self.public_id = public_id
        self.nif = nif
        self.address = address
        self.zip_code = zip_code
        self.city = city
        self.province = province
        self.email = email
        self.password = password

class Payer:
    def __init__(self, id=None, name=None, nif=None, address=None, zip_code=None, city=None, province=None):
        self.id = id
        self.name = name
        self.nif = nif
        self.address = address
        self.zip_code = zip_code
        self.city = city
        self.province = province

    def __str__(self):
        return f"the payer is {self.name}"

    def __eq__(self, other):
        return isinstance(other, Payer) and self.name == other.name

    def __hash__(self):
        return hash(self.name)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'nif': self.nif,
            'address': self.address,
            'zip_code': self.zip_code,
            'city': self.city,
            'province': self.province
        }


class InvoiceOrder:
    def __init__(self, payer_name, date, quantity, number=None, id=None):
        self.payer_name = payer_name
        self.date = date
        self.quantity = quantity
        self.number = number

        self._payer = None

    def __str__(self):
        return f"Invoice {self.number}, associated to {self.payer_name}"

    def __eq__(self, other):
        return (
                isinstance(other, InvoiceOrder) and
                self.payer_name == other.payer_name and
                self.date == other.date and
                self.quantity == other.quantity and
                self.number == other.number
        )

    def __hash__(self):
        return hash(self.payer_name)

    @staticmethod
    def calculate_lines(qty):
        lines = []
        type_1_price = 50
        type_2_price = 60
        price_diff = type_2_price - type_1_price

        if type_1_price >= type_2_price:
            raise ValueError("type_1_price must be lower than type_2_price")
        if qty < type_1_price:
            raise ValueError("quantity must be greater than type_1_price")

        type_2_no = (qty % type_1_price) / price_diff
        type_2_qty = type_2_no * type_2_price

        type_1_qty = qty - type_2_qty
        type_1_no = type_1_qty / type_1_price

        dict_keys = ['units', 'price', 'subtotal']
        if type_1_no:
            lines.append(dict(zip(dict_keys, (type_1_no, type_1_price, type_1_qty))))
        if type_2_no:
            lines.append(dict(zip(dict_keys, (type_2_no, type_2_price, type_2_qty))))

        return lines

    def allocate_payer(self, payer: Payer):
        self._payer = payer

    @property
    def allocated_payer(self):
        return self._payer

    @property
    def lines(self):
        return self.calculate_lines(self.quantity)
    