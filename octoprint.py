import yaml
import jira
from classes.printerModel import *
import os
from datetime import datetime

# importing configs
with open("config_files/config.yml", "r") as yamlFile:
    config = yaml.load(yamlFile, Loader=yaml.FullLoader)


@db_session
def start_queued_jobs():
    print("Checking for queued jobs...")
    queued_jobs = PrintJob.Get_All_By_Status(PrintStatus.IN_QUEUE)
    print(str(len(queued_jobs)) + " queued jobs found.")
    if len(queued_jobs) == 0:
        return

    jobs_started = 0  # Just used to track the number of jobs for logging.
    manual_jobs = 0
    printer_models = PrinterModel.Get_All()
    printers_by_count = Printer.Get_All_Printers_By_Count(True)
    for pm in printer_models:
        if pm.auto_start_prints:
            printers = list(filter(lambda p: p[0].printer_model.id == pm.id, printers_by_count))  # Get printers for this printer model
            jobs = list(filter(lambda j: j.printer_model.id == pm.id, queued_jobs))  # Get jobs for this printer model
            for printer in printers:
                # printer is a tuple: (printer, <print_count>)
                if len(jobs) == 0:  # We are out of jobs for this printer model
                    break
                if printer[0].Get_Printer_State() == 'operational':
                    start_print_job(jobs.pop(0), printer[0])  # Removes the job from the list for this printer model
                    jobs_started += 1
        else:
            jobs = list(filter(lambda j: j.printer_model.id == pm.id, queued_jobs))  # Get jobs for this printer model
            manual_jobs += len(jobs)

    print(str(len(queued_jobs) - jobs_started - manual_jobs) + " auto start jobs still in queue.")
    print(str(manual_jobs) + " manual start jobs still in queue.")



@db_session
def check_for_finished_jobs():
    print("Checking for finished jobs...")
    finished_count = 0
    printers = Printer.Get_All_Enabled()
    for printer in printers:
        if not printer.printer_model.auto_start_prints:
            continue
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
                print(job.Get_Name() + " finished on " + printer.name + ".")
                finished_count += 1
                printer.Reconnect_Printer()
                if os.path.exists(job.Get_File_Name()):
                    os.remove(job.Get_File_Name())
            else:
                print(printer.name + " has finished job not found in DB.")
        elif state == 'needs_clearing':
            print(printer.name + " needs to be cleared.")
    print(str(finished_count) + " finished jobs found.")



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
        print(job.Get_Name() + " started on " + printer.name + ".")
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
