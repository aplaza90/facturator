import jinja2
import pdfkit
from datetime import datetime
import os

from facturator.domain import model

# Define paths
base_dir = os.path.abspath(os.path.dirname(__file__))
static_dir = os.path.join(base_dir, 'static')
logo_path = os.path.join(static_dir, 'logo.png')
css_path = os.path.join(static_dir, 'invoice.css')


def generate_context(order: model.InvoiceOrder, logo_path=logo_path):
    order_context = {
        "invoice_number": order.number,
        "invoice_date": order.date,
        "client_name": order.allocated_payer.name,
        "client_address": order.allocated_payer.address,
        "client_zip_code": order.allocated_payer.zip_code,
        "client_city": order.allocated_payer.city,
        "client_province": order.allocated_payer.province,
        "client_nif": order.allocated_payer.nif,
        "professional_name": "SOME PROF",
        "professional_address": "Some st, some av",
        "professional_zip_code": "34567",
        "professional_city": "Some city",
        "professional_province": "some town",
        "professional_nif": "1234567",
        "professional_email": "example@gmail.com",
        "order_lines": order.lines,
        "total_bi": f"{order.quantity}€",
        "discount_qty": f"{order.quantity}€",
        "iva_qty": f"{order.quantity}€",
        "irpf_qty": f"{order.quantity}€",
        "Total_a_pagar": f"{order.quantity}€",
        "logo_path": logo_path
    }
    return order_context


template_loader = jinja2.FileSystemLoader(base_dir)
template_env = jinja2.Environment(loader=template_loader)

html_template = 'invoice.html'
template = template_env.get_template(html_template)

output_pdf = os.path.join(base_dir, 'invoice.pdf')


def create_pdf(context, css_path=css_path):
    pdf_path = os.path.join(base_dir, f'{context["client_name"]}_{context["invoice_date"]}.pdf')
    config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
    options = {
        'enable-local-file-access': '',
    }
    pdfkit.from_string(
        template.render(context),
        pdf_path,
        configuration=config,
        options=options,
        css=css_path
    )

