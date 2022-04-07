import requests
import json
import yaml
import jira
import os
import time
from datetime import datetime

# importing configs
with open("config.yml", "r") as yamlFile:
    config = yaml.load(yamlFile, Loader=yaml.FullLoader)
with open("printers.yml", "r") as yamlFile:
    printers = yaml.load(yamlFile, Loader=yaml.FullLoader)


def TryPrintingFile(file):
    """
    This will look at the prints we have waiting and see if a printer is open for it
    """
    for printer in printers['farm_printers']:
        apikey = printers['farm_printers'][printer]['api']
        printerIP = printers['farm_printers'][printer]['ip']
        materialType = printers['farm_printers'][printer]['materialType']
        materialColor = printers['farm_printers'][printer]['materialColor']
        materialDensity = printers['farm_printers'][printer]['materialDensity']
        printerType = printers['farm_printers'][printer]['printerType']

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
            if str(status['state']) == "Operational" and str(status['progress']['completion']) != "100.0":
                uploadFileToPrinter(apikey, printerIP, file)
                return
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            print("Skipping " + printer + " due to network error")
            print("code needed to reboot printer is it's having this issue")


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
        print(printerIP + "'s raspberry pi is offline and can't be contacted over the network")
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


def receiptPrinter(scrapedPRNumber, ticketNumber, scrapedPatronName, printer=''):
    """
    probably shouldn't be in the octoprint file but this gets the receipt printer stuff
    """
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    from escpos.printer import Usb

    patronName = scrapedPatronName
    try:
        patronName = str(patronName)
        patronName = patronName.title()
    except:
        patronName = ''

    if len(patronName) > 0:
        firstName = patronName.split(' ')[0]
        lastName = patronName.split(' ')[-1]
        if firstName != lastName:
            patronName = firstName[0] + ', ' + lastName

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
    firstFew = patronName[:8]
    if 'y' in firstFew or 'g' in firstFew or 'p' in firstFew or 'q' in firstFew:
        d.text((32, 121), patronName, font=fnt, fill=(255, 255, 255))
    else:
        d.text((32, 128), patronName, font=fnt, fill=(255, 255, 255))
    d.text((32, 256), ticketNumber, font=fnt, fill=(255, 255, 255))
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
    with open('jiradownloads/' + file + '.gcode', 'rb') as fh:
        first = next(fh).decode()
    try:
        grams = first.split('GRAMS')[1].split(',')[0].strip('=')
    except:
        grams = ''
    try:
        printTime = first.split('TIME')[1].split(',')[0].strip('=')
    except:
        printTime = ''
    try:
        taxExempt = first.split('TAXEXEMPT=')[1].split(',')[0]
    except:
        taxExempt = ''
    try:
        patronName = first.split('NAME=')[1].split(',')[0]
    except:
        patronName = ''
    try:
        projectNumber = first.split('PROJECTNUMBER=')[1].split(',')[0]
    except:
        projectNumber = ''
    try:
        ticketNumber = first.split('ID=')[1].split(',')[0]
    except:
        ticketNumber = ''
    startTime = datetime.now().strftime("%I:%M" '%p')
    if startTime[0] == '0':
        startTime = startTime[1:]
    # print(str(grams) + "  " + printTime + " " + startTime + " " + str(taxExempt))
    if grams != '' and printTime != '' and taxExempt != '':
        ticketText = "\nPrint was started at " + str(startTime) + "\nEstimated print weight is " + str(grams) + "g" + "\nEstimated print time is " + printTime
        if taxExempt == "True":
            ticketText += "\nEstimated print cost is (" + str(grams) + "g * $0.05/g) = $"
            cost = float(grams) * .05
            cost = str(("%.2f" % cost))
            ticketText += cost + ' (tax exempt)'
        elif taxExempt == "False":
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
            receiptPrinter(projectNumber, ticketNumber, patronName, printerName)
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
    for printer in printers['farm_printers']:
        apikey = printers['farm_printers'][printer]['api']
        printerIP = printers['farm_printers'][printer]['ip']
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
            if "State" not in response.text:
                if json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": "))):
                    status = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
                else:
                    status = "offline"
            else:
                print(printer + " is having issues and the pi is un-reachable, if this continues restart the pi")
                status = "offline"
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            print(printer + "'s raspberry pi is offline and can't be contacted over the network")
            status = "offline"

        """
        I might want to change some of this code when I am in front of the printers to make it so each printers status gets printed out
        """
        if status != "offline":
            if status['state'] == "Operational":
                if str(status['progress']['completion']) == "100.0":
                    volume = status['job']['filament']['tool0']['volume']
                    grams = volume * printers['farm_printers'][printer]['materialDensity']
                    print(printer + " is finishing up")
                    file = os.path.splitext(status['job']['file']['display'])[0]
                    resetConnection(apikey, printerIP)
                    try:
                        response = "{color:#00875A}Print completed successfully!{color}\n\nPrint was harvested at "
                        response += "Filament Usage ... " + str(grams) + "g"
                        response += "Actual Cost ... (" + str(grams) + "g * $" + str(config["payment"]["costPerGram"]) + "/g) = $"
                        cost = grams * config["payment"]["costPerGram"]
                        cost = str(("%.2f" % cost))
                        response += cost + " " + config["messages"]["finalMessage"]
                        jira.commentStatus(file, response)
                    except FileNotFoundError:
                        print("This print was not started by this script, I am ignoring it: " + file)
                    jira.changeStatus(file, "21")  # file name referenced
                    jira.changeStatus(file, "31")  # file name referenced
                    if config['payment']['prepay'] is True:
                        jira.changeStatus(file, "41")  # file name referenced
                else:
                    print(printer + " is ready")
                    continue
            elif status['state'] == "Printing":
                print(printer + " is printing")
            else:
                print(printer + " is offline")


def eachNewFile():
    """
    for each file in the list see if a printer is open for it
    """
    directory = r'jiradownloads'
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".gcode"):
            TryPrintingFile(os.path.splitext(filename)[0])
        else:
            continue
