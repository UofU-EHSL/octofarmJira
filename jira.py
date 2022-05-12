import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
from google_drive_downloader import GoogleDriveDownloader as gdd

import print_job_handler
from classes.gcodeLine import GcodeLine
from classes.printer import *
from classes.permissionCode import *
from classes.message import *
from classes.printJob import *
from classes.user import *
import os
import time
from classes.enumDefinitions import *
import re

# load all of our config files
with open("config_files/config.yml", "r") as yamlFile:
    config = yaml.load(yamlFile, Loader=yaml.FullLoader)
with open("config_files/lists.yml", "r") as yamlFile:
    userList = yaml.load(yamlFile, Loader=yaml.FullLoader)
with open("config_files/keys.yml", "r") as yamlFile:
    keys = yaml.load(yamlFile, Loader=yaml.FullLoader)

# jira authentication information that gets pulled in from the config ###
auth = HTTPBasicAuth(config['jira_user'], config['jira_password'])


def get_issues():
    """
    Get the list of issues in the jira project
    """
    url = config['base_url'] + "/rest/api/2/" + config['search_url']
    headers = {
        "Accept": "application/json"
    }

    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )

    # parse all open projects:
    openIssues = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    issues = []
    for issue in openIssues['issues']:
        url = issue['self']
        headers = {
            "Accept": "application/json"
        }
        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )
        if response.ok:
            issues.append(response)
        else:
            print("Bad response from Jira on issue:", issue.split('/')[-1])

    return issues


def parse_permission_code(description):
    start = "*Class Key* \\\\"  # TODO: UPDATE TO PERMISSION CODE ONCE FORM CHANGES
    end = "\n\n*Description of print*"
    code_string = description[description.find(start) + len(start):description.rfind(end)]
    if code_string:
        code = PermissionCode.get(code=code_string)
        if code:
            return code.id
        else:
            return 1  # Permission code ID 1 is an invalid code.
    return None


def parse_gcode_url(issue):
    attachments = issue['fields']['attachment']
    if attachments:
        return attachments[0]['self'], UrlTypes.JIRA_ATTACHMENT

    description = issue['fields']['description']
    split = description.split('\\\\')
    for s in split:
        if s.startswith('https'):
            url = s[:s.rfind('\n\n')]
            if "drive.google.com" in url:
                split = url.split('/')
                return split[5], UrlTypes.GOOGLE_DRIVE
            else:
                return url, UrlTypes.UNKNOWN

    return ''


@db_session
def get_new_print_jobs():
    # Get the IDs of issues that are new and have not been processed to ensure we don't add duplicates
    existing_issues = PrintJob.Get_All_By_Status(PrintStatus.NEW)
    existing_ids = []
    if existing_issues:
        for issue in existing_issues:
            existing_ids.append(issue.job_id)

    new_issues = get_issues()
    new_print_jobs = []
    for issue in new_issues:
        parsed_issue = json.loads(issue.text)
        job_id = parsed_issue['id']
        if int(job_id) in existing_ids:
            continue
        job_name = parsed_issue['key']
        user_id = parsed_issue['fields']['reporter']['name']
        user_name = parsed_issue['fields']['reporter']['displayName']
        user = User.Get_Or_Create(user_id, user_name)
        permission_code_id = parse_permission_code(parsed_issue['fields']['description'])
        gcode_url, url_type = parse_gcode_url(parsed_issue)

        new_print_jobs.append(PrintJob(job_id=job_id, job_name=job_name, print_status=PrintStatus.NEW.name, user=user.id, permission_code=permission_code_id, gcode_url=gcode_url, url_type=url_type.name))
    commit()
    return new_print_jobs


def download(job):
    """
    Downloads the files that getGcode wants
    """

    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.request(
            "GET",
            job.gcode_url,
            headers=headers,
            auth=auth
        )
    except Exception as e:
        print("Ticket " + job.Get_Name() + " error while downloading gcode from jira.")
        print(e)
        return "ERROR"

    if response.ok:
        return response.text
    else:
        print("Ticket " + job.Get_Name() + ": " + str(response.status_code) + " while downloading gcode from jira.")
        return "ERROR"


def printIsNoGo(singleIssue, singleID):
    """
    If the print is a no-go and shouldn't continue
    """
    attachments = str(singleIssue).split(',')
    if any(config['base_url'] + "/secure/attachment" in s for s in attachments):
        print("Downloading " + singleID)
        matching = [s for s in attachments if config['base_url'] + "/secure/attachment" in s]
        attachment = str(matching[0]).split("'")
        filename = attachment[3].split('/' + config['jiraTicketPrefix'] + '-', 1)[-1].split('_')[0]
        filename = config['jiraTicketPrefix'] + '-' + filename
        download(attachment[3], singleID, filename)
    elif any("https://drive.google.com/file/d/" in s for s in attachments):
        print("Downloading " + singleID + " from google drive")
        matching = [s for s in attachments if "https://drive.google.com/file/d/" in s]
        attachment = str(str(matching[0]).split("'"))
        start = "https://drive.google.com/file/d/"
        end = "/view?usp="
        downloadGoogleDrive(attachment[attachment.find(start) + len(start):attachment.rfind(end)], singleID)
    else:
        commentStatus(
            singleID,
            config['messages']['noFile']
        )
        changeStatus(singleID, JiraTransitionCodes.START_PROGRESS)
        changeStatus(singleID, JiraTransitionCodes.STOP_PROGRESS)


def send_fail_message(job_id, message_text):
    """
    Comments on a ticket with the provided message and stops the progress on the ticket.
    """
    commentStatus(job_id, message_text)
    changeStatus(job_id, JiraTransitionCodes.START_PROGRESS)
    changeStatus(job_id, JiraTransitionCodes.STOP_PROGRESS)


def send_print_started(job):
    """
    Comments on a ticket with the provided message and stops the progress on the ticket.
    """
    commentStatus(job.job_id, job.Generate_Start_Message())


def printIsGoodToGo(singleIssue, singleID):
    """
    Things to do when a print is good to go
    """
    attachments = str(singleIssue).split(',')
    if any(config['base_url'] + "/secure/attachment" in s for s in attachments):
        print("Downloading " + singleID)
        matching = [s for s in attachments if config['base_url'] + "/secure/attachment" in s]
        attachment = str(matching[0]).split("'")
        filename = attachment[3].split('/' + config['jiraTicketPrefix'] + '-', 1)[-1].split('_')[0]
        filename = config['jiraTicketPrefix'] + '-' + filename
        download(attachment[3], singleID, filename)
    elif any("https://drive.google.com/file/d/" in s for s in attachments):
        print("Downloading " + singleID + " from google drive")
        matching = [s for s in attachments if "https://drive.google.com/file/d/" in s]
        attachment = str(str(matching[0]).split("'"))
        start = "https://drive.google.com/file/d/"
        end = "/view?usp="
        downloadGoogleDrive(attachment[attachment.find(start) + len(start):attachment.rfind(end)], singleID)
    else:
        commentStatus(
            singleID,
            config['messages']['noFile']
        )
        changeStatus(singleID, JiraTransitionCodes.START_PROGRESS)
        changeStatus(singleID, JiraTransitionCodes.STOP_PROGRESS)


def changeStatus(job_id, transitionCode):
    """
    Changes status of issue in Jira.
    See enumDefinitions JiraTransitionCodes for codes.
    """
    url = config['base_url'] + "/rest/api/2/issue/" + str(job_id) + "/transitions"
    headers = {
        "Content-type": "application/json",
        "Accept": "application/json"
    }
    data = {
        # "update": {
        #     "comment": [{
        #         "add": {
        #             "body": "The ticket is resolved"
        #         }
        #     }]
        # },
        "transition": {
            "id": str(transitionCode.value)
        }
    }

    response = requests.request(
        "POST",
        url,
        headers=headers,
        json=data,
        auth=auth
    )


def commentStatus(job_id, comment):
    """
    a simple function call to be used whenever you want to comment on a ticket
    """
    # Don't comment empty strings. Done so you can leave strings empty in the config if you don't want to send that message.
    if not comment:
        return

    url = config['base_url'] + "/rest/api/2/issue/" + str(job_id) + "/comment"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "body": comment
    }

    response = requests.request(
        "POST",
        url,
        json=payload,
        headers=headers,
        auth=auth
    )


def askedForStatus():
    """
    When someone asks what their print status if we reply
    """
    print("Checking for status updates...")
    url = config['base_url'] + "/rest/api/2/" + config['printing_url']
    headers = {
        "Accept": "application/json"
    }

    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )

    # parse all open projects:
    openIssues = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    for issue in openIssues['issues']:
        url = issue['self']
        headers = {
            "Accept": "application/json"
        }

        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )

        ticketID = url[url.find("issue/") + len("issue/"):url.rfind("")]
        singleIssue = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        comments = singleIssue['fields']['comment']['comments']
        comment = ''
        if len(comments) > 0:
            comment = comments[-1]['body']
        for trigger in config['requestUpdate']:
            if str(comment).find(trigger) != -1:
                print(comment)
                directory = r'jiradownloads'
                for filename in sorted(os.listdir(directory)):
                    if filename.find(ticketID):
                        commentStatus(ticketID, config["messages"]["statusInQueue"])
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
                        status = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
                        if str(status['job']['file']['name']).find(ticketID) != -1:
                            base = config['messages']['statusUpdate'] + "\n"
                            completion = "Completion: " + str(round(status['progress']['completion'], 2)) + "%" + "\n"
                            eta = "Print time left: " + str(time.strftime('%H:%M:%S', time.gmtime(status['progress']['printTimeLeft']))) + "\n"
                            material = "Cost: $" + str(round(
                                status['job']['filament']['tool0']['volume'] * printer.material_density *
                                config['payment']['costPerGram'], 2)) + "\n"
                            end = config['messages']['statusUpdateEnd']

                            printerStatusUpdate = base + completion + eta + material + end
                            commentStatus(ticketID, printerStatusUpdate)
                            print(printerStatusUpdate)
                    except requests.exceptions.RequestException as e:  # This is the correct syntax
                        print("Skipping " + printer + " due to network error.")
                return
