import requests
import schedule
import time
from requests.auth import HTTPBasicAuth
import json
import yaml
import jira

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
        if "Operational" in status:
            uploadFileToPrinter(printer, file)
            return
        print(status)

def PrintIsFinished():
    """
    need to make a notification send but not double send
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
                
def uploadFileToPrinter(printer, file):
    print("Found an open printer")
    jira.commentStatus(file, "Your print is on a printer and starting now")
    """
    1) upload file
    2) start print
    
    """
TryPrintingFile("")


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
