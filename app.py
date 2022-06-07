import octoprint
import os
import flask
from classes.gcodeCheckItem import *
from pony.flask import Pony
import pythonFunctions
from classes.enumDefinitions import *
import yaml
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
    return flask.render_template('printers/printers.html', printers=all_printers, async_mode=socketio.async_mode, ip=flask.request.host)


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
    printer_models = PrinterModel.Get_All()
    return flask.render_template('printers/create_printer.html', models=printer_models, async_mode=socketio.async_mode, ip=flask.request.host)


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
    printer_models = PrinterModel.Get_All()
    return flask.render_template('printers/edit_printer.html', printer=printer, models=printer_models, async_mode=socketio.async_mode, ip=flask.request.host)


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


@app.route('/users')
def users():
    all_users = User.Get_All()
    return flask.render_template('users/users.html', users=all_users, async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/users/toggleWhiteListed/<user_id>', methods=['POST'])
def toggle_white_listed_status(user_id):
    try:
        user = User[user_id]
        user.white_listed = not user.white_listed
        commit()
        return {'status': 'success', 'white_listed': user.white_listed}
    except:
        return {'status': 'failed'}


@app.route('/users/toggleBlackListed/<user_id>', methods=['POST'])
def toggle_black_listed_status(user_id):
    try:
        user = User[user_id]
        user.black_listed = not user.black_listed
        commit()
        return {'status': 'success', 'black_listed': user.black_listed}
    except:
        return {'status': 'failed'}


@app.route('/users/editUser/<user_id>', methods=['GET'])
def edit_user_get(user_id):
    user = User[user_id]
    return flask.render_template('users/edit_user.html', user=user, async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/users/editUser/<user_id>', methods=['POST'])
def edit_user_post(user_id):
    try:
        form_data = request.form
        user = User[user_id]
        User.Map_Request(user, form_data)
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/permissionCodes')
def permissionCodes():
    all_codes = PermissionCode.Get_All()
    return flask.render_template('permission_codes/permission_codes.html', permissionCodes=all_codes, async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/permissionCodes/deletePermissionCode/<code_id>', methods=['POST'])
def delete_permission_code(code_id):
    try:
        if code_id == 1:  # ID 1 is always invalid code.
            return {'status': 'failed'}
        PermissionCode[code_id].delete()
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/permissionCodes/createPermissionCode', methods=['GET'])
def create_permission_code_get():
    return flask.render_template('permission_codes/create_permission_code.html', async_mode=socketio.async_mode, ip=flask.request.host)


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
    return flask.render_template('permission_codes/edit_permission_code.html', permissionCode=permissionCode, async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/permissionCodes/editPermissionCode/<code_id>', methods=['POST'])
def edit_permission_code_post(code_id):
    try:
        if code_id == 1:  # ID 1 is always invalid code.
            return {'status': 'failed'}
        form_data = request.form
        code = PermissionCode[code_id]
        PermissionCode.Map_Request(code, form_data)
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/messages')
def messages():
    all_messages = Message.Get_All()
    message_names = get_dict(MessageNames)
    return flask.render_template('messages/messages.html', messages=all_messages, message_names=message_names, async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/messages/deleteMessage/<message_id>', methods=['POST'])
def delete_message(message_id):
    try:
        Message[message_id].delete()
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/messages/createMessage', methods=['GET'])
def create_message_get():
    return flask.render_template('messages/create_message.html', async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/messages/createMessage', methods=['POST'])
def create_message_post():
    try:
        form_data = request.form
        Message.Add_From_Request(form_data)
        commit()
        return {'status': 'success'}
    except:
        return {'status': 'failed'}


@app.route('/messages/editMessage/<message_id>', methods=['GET'])
def edit_message_get(message_id):
    message = Message[message_id]
    return flask.render_template('messages/edit_message.html', message=message, async_mode=socketio.async_mode, ip=flask.request.host)


@app.route('/messages/editMessage/<message_id>', methods=['POST'])
def edit_message_post(message_id):
    try:
        form_data = request.form
        message = Message[message_id]
        Message.Map_Request(message, form_data)
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
