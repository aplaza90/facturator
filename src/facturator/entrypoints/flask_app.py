from flask import Flask, request, render_template, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from facturator import config
from facturator.adapters import orm
from facturator.service_layer import handlers
from facturator.service_layer import unit_of_work, messagebus
from facturator.domain import commands

orm.start_mappers()
engine = create_engine(config.get_postgres_uri())
orm.metadata.create_all(engine)
get_session = sessionmaker(bind=engine)
app = Flask(__name__, template_folder='templates')


@app.route('/test')
def test():
    return 'Flask application is running!'


@app.route("/add_payer", methods=['GET', 'POST'])
def add_payer():
    if request.method == 'POST':
        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.AddPayer(
            name=request.json["name"],
            nif=request.json["nif"],
            address=request.json["address"],
            zip_code=request.json["zip_code"],
            city=request.json["city"],
            province=request.json["province"],
        )
        messagebus.handle(message=cmd, uow=uow)
        return "OK", 201

    return render_template("add_payer.html")


@app.route('/upload_payment', methods=['GET', 'POST'])
def upload_payments_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part in the request', 400

        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400

        uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
        cmd = commands.UploadOrders(
            file=file, code_fixed_part='TEST', code_starting_number=0
        )
        messagebus.handle(message=cmd, uow=uow)

        return "OK", 201
    return render_template("upload_payments.html")


@app.route("/payers", methods=['GET'])
def get_payers():
    uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
    payers = handlers.get_payers(uow)

    return jsonify(payers), 200


@app.route("/orders", methods=['GET'])
def get_orders():
    uow = unit_of_work.SqlAlchemyUnitOfWork(get_session)
    orders = handlers.get_orders(uow)

    return jsonify(orders), 200



