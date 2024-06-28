import re
import uuid
from abc import ABC, abstractmethod
import pandas as pd

from facturator.domain.model import InvoiceOrder


class AbstractFileHandler(ABC):
    @staticmethod
    def get_name_from_concept(concept):
        """
        Extracts a name from a given concept string using predefined patterns.

        This function searches for specific patterns in the concept string to extract
        the name. It currently supports two patterns: 'BIZUM DE' and 'TRANSFERENCIA DE',
        followed by a name and the word 'CONCEPTO'.

        Args:
            concept (str): The concept string from which to extract the name.

        Returns:
            str or None: The extracted name if found, otherwise None.

        Examples:
            >>> get_name_from_concept("BIZUM DE John Doe CONCEPTO")
            'John Doe'
            >>> get_name_from_concept("TRANSFERENCIA DE Alice Bob Smith, CONCEPTO")
            'Alice Bob Smith'
            >>> get_name_from_concept("Payment via credit card")
            None
        """
        patterns = [
            r'BIZUM DE (.+?) CONCEPTO',
            r'TRANSFERENCIA DE (.+?), CONCEPTO'
        ]

        for pattern in patterns:
            match = re.search(pattern, concept)
            if match:
                return match.group(1)

        return None

    @abstractmethod
    def get_orders_from_file(self):
        pass


class ExcelFileHandler(AbstractFileHandler):
    def __init__(self, file_path):
        self.file_path = file_path

    @staticmethod
    def _clean_df(data):
        data = data.iloc[10:, 1:]
        data.reset_index(drop=True, inplace=True)

        data.columns = data.iloc[0]
        data = data.iloc[1:]
        data.reset_index(drop=True, inplace=True)

        columns_to_remove = [1, 3, 5, 7, 8]
        data.drop(data.columns[columns_to_remove], axis=1, inplace=True)
        data.dropna(axis=0, how='all', inplace=True)
        return data

    @staticmethod
    def convert_to_float(value):
        value = value.replace('.', '')
        value = value.replace(',', '.')
        return float(value)

    @staticmethod
    def _process_dates_and_numbers(data):
        data['Fecha Operaci?n'] = pd.to_datetime(data['Fecha Operaci?n'], dayfirst=True)
        data['Fecha Valor'] = pd.to_datetime(data['Fecha Valor'], dayfirst=True)
        data['Importe'] = data['Importe'].apply(ExcelFileHandler.convert_to_float) / 100
        return data

    def _get_df_from_excel(self):

        data = pd.read_html(self.file_path)[0]
        data = self._clean_df(data)
        data = self._process_dates_and_numbers(data)
        return data

    def _get_orders_from_df(self, data):
        data['Name'] = data['Concepto'].apply(self.get_name_from_concept)
        grouped_df = data.groupby('Name').agg({
            'Fecha Operaci?n': 'max', 'Importe': 'sum'
        })
        grouped_df.rename(columns={
            'Fecha Operaci?n': 'Latest Date', 'Importe': 'Total Amount'
        }, inplace=True)

        invoice_orders = []
        for index, row in grouped_df.iterrows():
            # Create an InvoiceOrder object for each row
            invoice_order = InvoiceOrder(
                id=str(uuid.uuid4()),
                payer_name=index,
                date=row['Latest Date'],
                quantity=row['Total Amount'],
            )
            invoice_orders.append(invoice_order)
        return invoice_orders

    def get_orders_from_file(self):
        df = self._get_df_from_excel()
        invoice_orders = self._get_orders_from_df(df)
        return invoice_orders

