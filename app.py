from importlib import import_module
import octoprint
import os
import flask
from classes.printer import *
from classes.permissionCode import *
from pony.flask import Pony
import threading
from markupsafe import escape
from multiprocessing import Process
import time
import pythonFunctions
from classes.enumDefinitions import *
from flask import request
import yaml
import asyncio
import jsonify
from threading import Lock
from flask import Flask, render_template, session, request, copy_current_request_context
from flask_socketio import SocketIO, emit

with open("config_files/config.yml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

DOWNLOAD_FOLDER = './jiradownloads'
CONFIG = './config_files/config.yml'
PRINTERS = './config_files/printers.yml'
KEYS = "./config_files/keys.yml"
LISTS = "./config_files/lists.yml"
HISTORY = "./config_files/history.yml"

set_sql_debug(False)  # Shows the SQL queries pony is running in the console.
db.bind(provider='sqlite', filename='octofarmJira_database.sqlite', create_db=True)  # Establish DB connection.
db.generate_mapping(create_tables=True)  # Have to generate mapping to use Pony. Will create tables that do not already exist.

Pony(app)  # Connects routes to the DB as needed without having to do it manually.


def background_thread():
    """How to send server generated events to clients."""
    while True:
        socketio.sleep(1)

        with open(PRINTERS, "r") as yamlfile:
            printers = yaml.load(yamlfile, Loader=yaml.FullLoader)
        for printer in printers['PRINTERS']:
            apikey = printers['PRINTERS'][printer]['api']
            printerIP = printers['PRINTERS'][printer]['ip']
            status = octoprint.GetStatus(printerIP, apikey)
            if status['progress']['completion'] is None:
                percent = 0
                eta = 0
            else:
                percent = str(round(status['progress']['completion'], 2))
                eta = str(round(status['progress']['printTimeLeft'], 0))

            socketio.emit('my_response', {
                'api': apikey,
                'percent': percent,
                'status': str(status['state']),
                'eta': eta
            })


@app.route('/')
def index():
    return flask.render_template('layout.html', async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/printers')
def printers():
    all_printers = Printer.Get_All()
    return flask.render_template('printers.html', printers=all_printers, async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/printers/deletePrinter/<printer_id>', methods=['POST'])
def delete_printer(printer_id):
    try:
        Printer[printer_id].delete()
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/printers/togglePrinterStatus/<printer_id>', methods=['POST'])
def toggle_printer_status(printer_id):
    try:
        printer = Printer[printer_id]
        printer.enabled = not printer.enabled
        commit()
        return {'status': 'success', 'enabled': printer.enabled}
    except:
        return {'status': 'failed'}


@app.route('/printers/createPrinter', methods=['GET'])
def create_printer_get():
    return flask.render_template('create_printer.html', models=get_dict(PrinterModel), async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/printers/createPrinter', methods=['POST'])
def create_printer_post():
    try:
        form_data = request.form
        Printer.Add_From_Request(form_data)
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/printers/editPrinter/<printer_id>', methods=['GET'])
def edit_printer_get(printer_id):
    printer = Printer[printer_id]
    return flask.render_template('edit_printer.html', printer=printer, models=get_dict(PrinterModel), async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/printers/editPrinter/<printer_id>', methods=['POST'])
def edit_printer_post(printer_id):
    try:
        form_data = request.form
        printer = Printer[printer_id]
        Printer.Map_Request(printer, form_data)
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/permissionCodes')
def permissionCodes():
    all_codes = PermissionCode.Get_All()
    return flask.render_template('permission_codes.html', permissionCodes=all_codes, async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/permissionCodes/deletePermissionCode/<code_id>', methods=['POST'])
def delete_permission_code(code_id):
    try:
        PermissionCode[code_id].delete()
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/permissionCodes/createPermissionCode', methods=['GET'])
def create_permission_code_get():
    return flask.render_template('create_permission_code.html', async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/permissionCodes/createPermissionCode', methods=['POST'])
def create_permission_code_post():
    try:
        form_data = request.form
        PermissionCode.Add_From_Request(form_data)
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/permissionCodes/editPermissionCode/<code_id>', methods=['GET'])
def edit_permission_code_get(code_id):
    permissionCode = PermissionCode[code_id]
    return flask.render_template('edit_permission_code.html', permissionCode=permissionCode, async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/permissionCodes/editPermissionCode/<code_id>', methods=['POST'])
def edit_permission_code_post(code_id):
    try:
        form_data = request.form
        code = PermissionCode[code_id]
        PermissionCode.Map_Request(code, form_data)
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # config
    with open(CONFIG) as f:
        config = f.read()
    with open(PRINTERS) as f:
        printers = f.read()
    with open(KEYS) as f:
        keys = f.read()
    with open(LISTS) as f:
        lists = f.read()

    if request.method == 'POST':
        if "config_box" in request.form:
            config = request.form['config_box']
            with open(CONFIG, 'w') as f:
                f.write(str(config))
        if "printers_box" in request.form:
            printers = request.form['printers_box']
            with open(PRINTERS, 'w') as f:
                f.write(str(printers))
        if "keys_box" in request.form:
            keys = request.form['keys_box']
            with open(KEYS, 'w') as f:
                f.write(str(keys))
        if "lists_box" in request.form:
            lists = request.form['lists_box']
            with open(LISTS, 'w') as f:
                f.write(str(lists))

    return flask.render_template('admin.html', config=config, printers=printers, keys=keys, lists=lists, ip=flask.request.host)


@app.route('/delete/<fileName>', methods=['GET', 'POST'])
def remove(fileName=None):
    abs_path = os.path.join(DOWNLOAD_FOLDER, fileName)
    pythonFunctions.delete(abs_path)
    files = os.listdir(DOWNLOAD_FOLDER)
    return flask.render_template('queue.html', files=files, ip=flask.request.host)


@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    return flask.send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


@app.route('/queue/', methods=['GET', 'POST'])
def dir_listing():
    files = os.listdir(DOWNLOAD_FOLDER)
    return flask.render_template('queue.html', files=files, ip=flask.request.host)


if __name__ == '__main__':
    socketio.run(app, host='localhost', port=10001)
