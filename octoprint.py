import requests
import schedule
import time
from requests.auth import HTTPBasicAuth
import json
import yaml
import jira
import os

with open("config.yml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)

"""
GET /api/job HTTP/1.1
Host: example.com
X-Api-Key: abcdef...
"""

def TryPrintingFile(file):
    for printer in config['PRINTERS']:
        apikey = config['PRINTERS'][printer]['api']
        printerIP = config['PRINTERS'][printer]['ip']
        url = "http://" + printerIP + "/api/job"

        headers = {
            "Accept": "application/json",
            "Host": printerIP,
            "X-Api-Key": apikey
        }
        
        response = requests.request(
            "GET",
            url,
            headers=headers
        )
        status = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        print(apikey + " " + printerIP)
        if "Operational" in str(status):
            uploadFileToPrinter(apikey, printerIP, file)
            return
        
def uploadFileToPrinter(apikey, printerIP, file):
    fle={'file': open('jiradownloads/' + file + '.gcode', 'rb'), 'filename': file}
    url="http://" + printerIP + "/api/files/{}".format("local")
    payload={'select': 'true','print': 'true' }
    header={'X-Api-Key': apikey}
    response = requests.post(url, files=fle,data=payload,headers=header)
    if os.path.exists("jiradownloads/" + file + ".gcode"):
        os.remove("jiradownloads/" + file + ".gcode")
        jira.commentStatus(file, "Your file is now printing and we will update you when it is finished and ready for pickup")
        print("Now printing: " + file )
    
def PrintIsFinished():
    """
    Make it so when a print starts it opens a new thread, that thread does checks on the stats of the print often. If the print gets to 100% done it sends a notification and kills the thread. that makes it so every print get's only one notification and we can store the jira ID in that thread
    """
    for printer in config['PRINTERS']:
        apikey = config['PRINTERS'][printer]['api']
        printerIP = config['PRINTERS'][printer]['ip']
        url = "http://" + printerIP + "/api/job"

        headers = {
            "Accept": "application/json",
            "Host": printerIP,
            "X-Api-Key": apikey
        }
        
        response = requests.request(
            "GET",
            url,
            headers=headers
        )
        status = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        if "Operational" in status:
                print("Notifying about a print completion")
                jira.commentStatus(file, "Your print has been completed and should now be available for pickup")

def eachNewFile():
    directory = r'jiradownloads'
    for filename in os.listdir(directory):
        if filename.endswith(".gcode") or filename.endswith(".stl"):
            TryPrintingFile(os.path.splitext(filename)[0])
        else:
            continue

"""
NOT PRINTING STATUS DUMP

{'job': {'averagePrintTime': 8252.386931791902, 'estimatedPrintTime': 6949.799612229507, 'filament': {'tool0': {'length': 10256.492500000235, 'volume': 24.66975551547465}}, 'file': {'date': 1618616948, 'display': '(Unsaved).gcode', 'name': '(Unsaved).gcode', 'origin': 'local', 'path': '(Unsaved).gcode', 'size': 1192417}, 'lastPrintTime': 8252.386931791902, 'user': 'Admin'}, 'progress': {'completion': None, 'filepos': None, 'printTime': None, 'printTimeLeft': None, 'printTimeLeftOrigin': None}, 'state': 'Operational'}
"""
"""
PRINTING STATUS DUMP

{'job': {'averagePrintTime': None, 'estimatedPrintTime': 776.9711917705915, 'filament': {'tool0': {'length': 940.7207699999908, 'volume': 2.2626986178977173}}, 'file': {'date': 1634339973, 'display': 'whistle2.gcode', 'name': 'whistle2.gcode', 'origin': 'local', 'path': 'whistle2.gcode', 'size': 516878}, 'lastPrintTime': None, 'user': 'Admin'}, 'progress': {'completion': 9.030951210924048, 'filepos': 46679, 'printTime': 466, 'printTimeLeft': 655, 'printTimeLeftOrigin': 'analysis'}, 'state': 'Printing'}
"""
"""
PRINT FINISHED DUMP

{'job': {'averagePrintTime': 1233.8309079409992, 'estimatedPrintTime': 776.9711917705915, 'filament': {'tool0': {'length': 940.7207699999908, 'volume': 2.2626986178977173}}, 'file': {'date': 1634339973, 'display': 'whistle2.gcode', 'name': 'whistle2.gcode', 'origin': 'local', 'path': 'whistle2.gcode', 'size': 516878}, 'lastPrintTime': 1233.8309079409992, 'user': 'Admin'}, 'progress': {'completion': 100.0, 'filepos': 516878, 'printTime': 1234, 'printTimeLeft': 0, 'printTimeLeftOrigin': None}, 'state': 'Operational'}
"""
