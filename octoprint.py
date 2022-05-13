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
        if printer[0].Get_Printer_State() == 'operational':
            start_print_job(queued_jobs.pop(0), printer[0])


@db_session
def check_for_finished_jobs():
    printers = Printer.Get_All_Enabled()
    for printer in printers:
        state, actual_print_volume = printer.Get_Printer_State(get_actual_volume=True)
        if state == 'finished':
            job = printer.Get_Current_Job()
            if job:
                grams = round(actual_print_volume * printer.material_density, 2)
                job.weight = round(grams, 2)
                if job.permission_code:
                    job.cost = round(grams * 0.05, 2)
                else:
                    job.cost = round(grams * 0.05 * 1.0775, 2)
                job.print_status = PrintStatus.FINISHED.name
                job.print_finished_date = datetime.now()
                job.payment_status = PaymentStatus.NEEDS_PAYMENT_LINK.name
                commit()
                jira.send_print_finished(job)
                printer.Reset_Connection()
            else:
                print(printer.name + " has finished job not found in DB.")


def start_print_job(job, printer):
    """Starts a print job on a printer and updates jira with print started comment. Also prints physical receipt."""
    upload_result = printer.Upload_Job(job)
    if upload_result.ok:
        job.printed_on = printer.id
        job.print_status = PrintStatus.PRINTING.name
        job.payment_status = PaymentStatus.PRINTING.name
        job.print_started_date = datetime.now()
        commit()
        if config["receipt_printer"]["print_physical_receipt"] is True:
            receiptPrinter(job.Get_Name(job_name_only=True), printer.name)
        jira.send_print_started(job)
    else:
        print("Error uploading " + job.Get_Name() + " to " + printer.name + '. Status code: ' + str(upload_result.status_code))


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


def PrintIsFinished():
    """
    If a print is complete update people and mark as ready for new file
    """
    printers = Printer.Get_All_Enabled()
    for printer in printers:
        headers = {
            "Accept": "application/json",
            "Host": printer.ip,
            "X-Api-Key": printer.api_key
        }
        try:
            response = requests.request(
                "GET",
                printer.Get_Job_Url(),
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
