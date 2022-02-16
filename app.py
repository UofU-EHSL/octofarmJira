from importlib import import_module
import octoprint
import os
import flask
import threading
from markupsafe import escape
from multiprocessing import Process
import time
import pythonFunctions
from flask import request
import yaml
import asyncio
import jsonify
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context
from flask_socketio import SocketIO, emit

with open("./config.yml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

DOWNLOAD_FOLDER = './jiradownloads'
CONFIG = './config.yml'
PRINTERS = './printers.yml'
KEYS = "./keys.yml"
LISTS = "./lists.yml"
HISTORY = "./history.yml"
    
def background_thread():
    """How to send server generated events to clients."""
    while True:
        socketio.sleep(1)
        
        with open(PRINTERS, "r") as yamlfile:
            printers = yaml.load(yamlfile, Loader=yaml.FullLoader)
        for printer in printers['PRINTERS']:
            apikey = printers['PRINTERS'][printer]['api']
            printerIP = printers['PRINTERS'][printer]['ip']
            status = octoprint.GetStatus(printerIP,apikey)
            if status['progress']['completion'] is None:
                percent = 0
                eta = 0
            else:
                percent = str(round(status['progress']['completion'], 2))
                eta = str(round(status['progress']['printTimeLeft'], 0))
            
            socketio.emit('my_response', {
                'api' : apikey,
                'percent': percent,
                'status': str(status['state']),
                'eta': eta
            })
        
@app.route('/')
def index():
    return flask.render_template('main.html', async_mode=socketio.async_mode, config=config, ip=flask.request.host)

@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

@app.route('/admin', methods=['GET','POST'])
def admin():

    #config
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
   
@app.route('/delete/<fileName>', methods=['GET','POST'])
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
