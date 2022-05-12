import requests
import json
import yaml
import jira
from classes.enumDefinitions import JiraTransitionCodes
from classes.printer import Printer
from classes.printJob import *
import os
import time
from datetime import datetime

# importing configs
with open("config_files/config.yml", "r") as yamlFile:
    config = yaml.load(yamlFile, Loader=yaml.FullLoader)

@db_session
def start_queued_jobs():
    queued_jobs = PrintJob.Get_All_By_Status(PrintStatus.IN_QUEUE)
    if len(queued_jobs) == 0:
        return
    printers_by_count = Printer.Get_All_Print_Counts()
    for printer in printers_by_count:
        # printer is a tuple: (printer, <print_count>)
        if len(queued_jobs) == 0:
            break
        if check_printer_available(printer[0]):
            start_print_job(queued_jobs.pop(0), printer[0])


def check_printer_available(printer):
    url = "http://" + printer.ip + "/api/job"

    headers = {
        "Accept": "application/json",
        "Host": printer.ip,
        "X-Api-Key": printer.api_key
    }
    try:
        response = requests.request(
            "GET",
            url,
            headers=headers
        )
        status = json.loads(response.text)
        if str(status['state']) == "Operational" and str(status['progress']['completion']) != "100.0":
            return True
    except requests.exceptions.RequestException as e:
        return False
        print("Skipping " + printer.name + " due to network error")
    return False


def start_print_job(job, printer):
    upload_result = upload_job_to_printer(job, printer)
    if upload_result.ok:
        job.printed_on = printer.id
        job.print_status = PrintStatus.PRINTING.name
        job.print_started = datetime.now()
        commit()
        receiptPrinter(job.Get_Name(job_name_only=True), printer.name)
        jira.send_print_started(job)
    else:
        print("Error uploading " + job.Get_Name() + " to " + printer.name + '. Status code: ' + str(upload_result.status_code))


def upload_job_to_printer(job, printer):
    openFile = open(job.Get_File_Name(), 'rb')
    fle = {'file': openFile, 'filename': job.Get_Name()}
    url = "http://" + printer.ip + "/api/files/{}".format("local")
    payload = {'select': 'true', 'print': 'true'}
    header = {'X-Api-Key': printer.api_key}
    return requests.post(url, files=fle, data=payload, headers=header)


# def TryPrintingFile(file):
#     """
#     This will look at the prints we have waiting and see if a printer is open for it
#     """
#     printers = Printer.Get_All_Enabled()
#     for printer in printers:
#         url = "http://" + printer.ip + "/api/job"
#
#         headers = {
#             "Accept": "application/json",
#             "Host": printer.ip,
#             "X-Api-Key": printer.api_key
#         }
#         try:
#             response = requests.request(
#                 "GET",
#                 url,
#                 headers=headers
#             )
#             status = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
#             if str(status['state']) == "Operational" and str(status['progress']['completion']) != "100.0":
#                 uploadFileToPrinter(printer.api_key, printer.ip, file)
#                 return
#         except requests.exceptions.RequestException as e:  # This is the correct syntax
#             print("Skipping " + printer.name + " due to network error")


def GetStatus(ip, api):
    """
    Get the status of the printer you are asking about
    """
    apikey = api
    printerIP = ip
    url = "http://" + printerIP + "/api/job"

    headers = {
        "Accept": "application/json",
        "Host": printerIP,
        "X-Api-Key": apikey
    }
    try:
        response = requests.request(
            "GET",
            url,
            headers=headers
        )
        status = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        return status
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(printerIP + "'s raspberry pi is offline")
        status = "offline"
        return status


def GetName(ip, api):
    """
    get the name of the printer you are asking about
    """
    apikey = api
    printerIP = ip
    url = "http://" + printerIP + "/api/printerprofiles"
    name = ip
    headers = {
        "Accept": "application/json",
        "Host": printerIP,
        "X-Api-Key": apikey
    }
    try:
        response = requests.request(
            "GET",
            url,
            headers=headers
        )
        status = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

        name = status["profiles"]["_default"]["name"]
        return name
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(printerIP + "'s raspberry pi is offline and can't be contacted over the network")
        status = "offline"
        return name


def receiptPrinter(scrapedPRNumber, printer=''):
    """
    probably shouldn't be in the octoprint file but this gets the receipt printer stuff
    """
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    from escpos.printer import Usb

    try:
        # try to reconnect to printer
        p = Usb(0x0416, 0x5011, 0, 0x81, 0x03)
    except:
        alreadyConnected = True
    try:
        # try to center printing alignment
        p.set(align='center')
    except:
        alreadyAligned = True
    # create new image large enough to fit super long names
    img = Image.new('RGB', (2400, 400), color=(0, 0, 0))
    fnt = ImageFont.truetype(r"resources/arialbd.ttf", 110, encoding="unic")
    tiny = ImageFont.truetype(r"resources/arial.ttf", 20, encoding="unic")
    d = ImageDraw.Draw(img)
    d.text((32, 0), scrapedPRNumber, font=fnt, fill=(255, 255, 255))
    d.text((34, 355), printer, font=tiny, fill=(255, 255, 255))

    imageBox = img.getbbox()
    cropped = img.crop(imageBox)
    inverted = ImageOps.invert(cropped)
    rotated = inverted.rotate(270, expand=True)

    try:
        # print image
        p.image(rotated)
        # cut point
        p.text("\n\n-                              -\n\n")
    except:
        print("\nThe receipt printer is unplugged or not powered on, please double check physical connections.")
        raise ValueError


def uploadFileToPrinter(apikey, printerIP, file):
    """
    Uploads a file to a printer
    """
    openFile = open('jiradownloads/' + file + '.gcode', 'rb')
    fle = {'file': openFile, 'filename': file}
    url = "http://" + printerIP + "/api/files/{}".format("local")
    payload = {'select': 'true', 'print': 'true'}
    header = {'X-Api-Key': apikey}
    response = requests.post(url, files=fle, data=payload, headers=header)

    with open('jiradownloads/' + file + '.gcode', 'rb') as gcode:
        for line in gcode:
            line = line.decode()
            if line.startswith('; filament used [g]'):
                grams = line.split('=')[1].strip()
            elif line.startswith('; estimated printing time (normal mode)'):
                printTime = line.split('=')[1].strip()

    startTime = datetime.now().strftime("%I:%M" '%p')
    if startTime[0] == '0':
        startTime = startTime[1:]
    if grams != '' and printTime != '':
        ticketText = "\nPrint was started at " + str(startTime) + "\nEstimated print weight is " + str(grams) + "g" + "\nEstimated print time is " + printTime
        ticketText += "\nEstimated print cost is (" + str(grams) + "g * $0.05/g * 1.0775 state tax = $"
        cost = float(grams) * .05 * 1.0775
        cost = str(("%.2f" % cost))
        ticketText += cost
    else:
        ticketText = config['messages']['printStarted']
    openFile.close()
    if os.path.exists("jiradownloads/" + file + ".gcode"):
        # print(config['Save_printed_files'])
        if config['Save_printed_files'] is False:
            os.remove("jiradownloads/" + file + ".gcode")
        else:
            os.replace("jiradownloads/" + file + ".gcode", "archive_files/" + file + ".gcode")
        if ticketText != config['messages']['printStarted']:
            # file name referenced
            jira.commentStatus(file, ticketText)
        printerName = GetName(printerIP, apikey)
        print("Now printing: " + file + " on " + printerName + " at " + printerIP)

    if config["receipt_printer"]["print_physical_receipt"] is True:
        try:
            printerName = GetName(printerIP, apikey)
            projectNumber = file.split('__')[0]
            receiptPrinter(projectNumber, printerName)
        except:
            print("There was a problem printing the receipt " + projectNumber)


def resetConnection(apikey, printerIP):
    """
    Resets the connection to a printer, done as a safety check and status clear
    """
    url = "http://" + printerIP + "/api/connection"
    disconnect = {'command': 'disconnect'}
    connect = {'command': 'connect'}
    header = {'X-Api-Key': apikey}
    response = requests.post(url, json=disconnect, headers=header)
    time.sleep(30)
    response = requests.post(url, json=connect, headers=header)


def PrintIsFinished():
    """
    If a print is complete update people and mark as ready for new file
    """
    printers = Printer.Get_All_Enabled()
    for printer in printers:
        url = "http://" + printer.ip + "/api/job"
        headers = {
            "Accept": "application/json",
            "Host": printer.ip,
            "X-Api-Key": printer.api_key
        }
        try:
            response = requests.request(
                "GET",
                url,
                headers=headers
            )
            if "State" not in response.text:
                if json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": "))):
                    status = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
                else:
                    status = {'state': 'Offline'}
            else:
                print(printer.name + " is having issues and the pi is un-reachable, if this continues restart the pi")
                status = {'state': 'Offline'}
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            print(printer.name + "'s raspberry pi is offline and can't be contacted over the network")
            status = {'state': 'Offline'}

        """
        I might want to change some of this code when I am in front of the printers to make it so each printers status gets printed out
        """
        if status != "offline":
            if status['state'] == "Operational":
                if str(status['progress']['completion']) == "100.0":
                    volume = status['job']['filament']['tool0']['volume']
                    grams = round(volume * printer.material_density, 2)
                    print(printer.name + " is finishing up")
                    file = os.path.splitext(status['job']['file']['display'])[0]
                    resetConnection(printer.api_key, printer.ip)
                    try:
                        finishTime = datetime.now().strftime("%I:%M" '%p')
                        response = "{color:#00875A}Print completed successfully!{color}\n\nPrint was harvested at " + finishTime
                        response += "\nFilament Usage ... " + str(grams) + "g"
                        response += "\nActual Cost ... (" + str(grams) + "g * $" + str(config["payment"]["costPerGram"]) + "/g) = $"
                        cost = grams * config["payment"]["costPerGram"]
                        cost = str(("%.2f" % cost))
                        response += cost + " " + config["messages"]["finalMessage"]
                        jira.commentStatus(file, response)
                    except FileNotFoundError:
                        print("This print was not started by this script, I am ignoring it: " + file)
                    jira.changeStatus(file, JiraTransitionCodes.READY_FOR_REVIEW)  # file name referenced
                    jira.changeStatus(file, JiraTransitionCodes.APPROVE)  # file name referenced
                    if config['payment']['prepay'] is True:
                        jira.changeStatus(file, JiraTransitionCodes.DONE)  # file name referenced

        print(printer.name + " : " + status['state'])
