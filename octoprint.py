import requests
import schedule
import time
from requests.auth import HTTPBasicAuth
import json
import yaml
import jira
import os
import time

with open("config.yml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)

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
        if str(status['state']) == "Operational" and str(status['progress']['completion']) != "100.0":
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
        print("Now printing: " + file + " on " + printerIP)
        
def resetConnection(apikey, printerIP):
    url="http://" + printerIP + "/api/connection"
    disconnect={'command': 'disconnect'}
    connect={'command': 'connect'}
    header={'X-Api-Key': apikey}
    response = requests.post(url,json=disconnect,headers=header)
    time.sleep(30)
    response = requests.post(url,json=connect,headers=header)

def PrintIsFinished():
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
        
        """
        I might want to change some of this code when I am in front of the printers to make it so each printers status get's printed out
        """
        if status['state'] == "Operational":
            if str(status['progress']['completion']) == "100.0":
                file = os.path.splitext(status['job']['file']['display'])[0]
                print(printerIP + " Notifying about a print completion")
                resetConnection(apikey, printerIP)
                jira.commentStatus(file, "Your print has been completed and should now be available for pickup")
                jira.changeStatus(file, "21")
                jira.changeStatus(file, "31")
                jira.changeStatus(file, "41")
            else:
                print(printerIP + " is ready")
                continue
        elif status['state'] == "Printing":
            print(printerIP + " is printing")
        else:
            print(printerIP + " is offline")

def eachNewFile():
    directory = r'jiradownloads'
    for filename in os.listdir(directory):
        if filename.endswith(".gcode") or filename.endswith(".stl"):
            TryPrintingFile(os.path.splitext(filename)[0])
        else:
            continue
