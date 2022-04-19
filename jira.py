import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
from google_drive_downloader import GoogleDriveDownloader as gdd
from gcodeLine import GcodeLine
import os
import time
from enumDefinitions import *
import re

# load all of our config files
with open("config.yml", "r") as yamlFile:
    config = yaml.load(yamlFile, Loader=yaml.FullLoader)
with open("lists.yml", "r") as yamlFile:
    userList = yaml.load(yamlFile, Loader=yaml.FullLoader)
with open("keys.yml", "r") as yamlFile:
    keys = yaml.load(yamlFile, Loader=yaml.FullLoader)
with open("printers.yml", "r") as yamlFile:
    printers = yaml.load(yamlFile, Loader=yaml.FullLoader)

# jira authentication information that gets pulled in from the config ###
auth = HTTPBasicAuth(config['jira_user'], config['jira_password'])


def issueList():
    """
    Get the list of issues in the jira project
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Checking for new submissions...")
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
        issues.append(issue['self'])
    return issues


def getGcode():
    """
    Gets the files and puts them where they need to be
    """
    for issue in issueList():
        issueId = issue.split("/")
        singleID = issueId[-1]
        url = issue
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
        singleIssue = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        user = singleIssue['fields']['reporter']['name']

        # parsing class key value
        start = "*Class Key* \\\\"
        end = "\n\n*Description of print*"
        s = singleIssue['fields']['description']
        classKey = s[s.find(start) + len(start):s.rfind(end)]

        # keys can be validated and update the key logs but keys do not change if a print is to be printed or not yet.

        # If someone is nice they go in here
        if user in userList["NICE"] and config["use_nice_list"] is True:
            printIsGoodToGo(singleIssue, singleID, classKey)
        # if they are naughty they go in here
        elif user in userList["NAUGHTY"] and config["use_naughty_list"] is True:
            printIsNoGo(singleID, singleID)
            if os.path.exists("jiradownloads/" + singleID + ".gcode"):
                os.remove("jiradownloads/" + singleID + ".gcode")
        # if they are a new user they go in here
        else:
            if config["use_naughty_list"] is True:
                printIsGoodToGo(singleIssue, singleID, classKey)
            elif config["use_nice_list"] is False:
                printIsNoGo(singleIssue, singleID)
            elif config["use_naughty_list"] is False and config["use_naughty_list"] is False:
                printIsGoodToGo(singleIssue, singleID, classKey)


def downloadGoogleDrive(file_ID, singleID):
    """
    if the jira project has a Google Drive link in the description download it
    """
    if config['Make_files_anon'] is True:
        gdd.download_file_from_google_drive(file_id=file_ID, dest_path="jiradownloads/" + singleID + ".gcode")
        file = open("jiradownloads/" + singleID + ".gcode", "r")
    else:
        gdd.download_file_from_google_drive(file_id=file_ID, dest_path="jiradownloads/" + file_ID + "__" + singleID + ".gcode")
        file = open("jiradownloads/" + file_ID + "__" + singleID + ".gcode", "r")

    if check_gcode(file) == GcodeStates.INVALID:
        commentStatus(singleID, config['messages']['wrongConfig'])
        changeStatus(singleID, JiraTransitionCodes.START_PROGRESS)
        changeStatus(singleID, JiraTransitionCodes.READY_FOR_REVIEW)
        changeStatus(singleID, JiraTransitionCodes.REJECT)
        if os.path.exists("jiradownloads/" + singleID + ".gcode"):
            os.remove("jiradownloads/" + singleID + ".gcode")
    else:
        changeStatus(singleID, JiraTransitionCodes.START_PROGRESS)
        commentStatus(singleID, config['messages']['downloadedFile'])


def download(gcode, singleID, filename):
    """
    Downloads the files that getGcode wants
    """
    url = gcode

    headers = {
        "Accept": "application/json"
    }

    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )
    checkResult, validatedGcode = check_gcode(response.text)
    if checkResult is GcodeStates.INVALID:
        commentStatus(singleID, config['messages']['wrongConfig'])
        changeStatus(singleID, JiraTransitionCodes.START_PROGRESS)
        changeStatus(singleID, JiraTransitionCodes.READY_FOR_REVIEW)
        changeStatus(singleID, JiraTransitionCodes.REJECT)
    else:
        if config['Make_files_anon'] is True:
            text_file = open("jiradownloads/" + singleID + ".gcode", "w")
        else:
            text_file = open("jiradownloads/" + filename + "__" + singleID + ".gcode", "w")
        n = text_file.write(validatedGcode)
        text_file.close()
        changeStatus(singleID, JiraTransitionCodes.START_PROGRESS)
        commentStatus(singleID, config['messages']['downloadedFile'])


def parse_gcode(gcode):
    """
    Parses a .gcode file into a list of GcodeLine objects.
    Empty lines are ignored and not added.
    """
    gcode = gcode.split("\n")
    parsed_gcode = []
    for line in gcode:
        if line:  # Filter out empty lines.
            commentIndex = 0  # Start at 0 so we enter the loop.
            comment = ""
            while commentIndex >= 0:  # Find any comments.
                commentIndex = line.find(';')  # Will be -1 if no comments found.
                if commentIndex >= 0:
                    comment = comment + line[commentIndex + 1:].strip()  # Pull out the comment
                    line = line[:commentIndex]  # Remove it from the line.
            if line:  # If there is anything left in the line keep going.
                split_line = line.split()
                parsed_gcode.append(GcodeLine(split_line[0], split_line[1:], comment))
            else:  # If nothing is left at this point, the line is purely a comment.
                parsed_gcode.append(GcodeLine(';', None, comment))
    return parsed_gcode


def gcode_to_text(parsed_gcode):
    """
    Turns a list of GcodeLine objects into plain text suitable to be written to a text file and run on a printer.
    """
    text_gcode = ''
    for line in parsed_gcode:
        new_line = ''
        new_line += line.command + ' '
        if line.params:
            new_line += ' '.join(line.params)
        if line.comment and line.command != ';':
            new_line += ' ;'
        if line.comment:
            new_line += line.comment
        new_line += '\n'
        text_gcode += new_line
    return text_gcode


def filter_characters(string):
    """Removes all characters from a string except for numbers."""
    return re.sub("\D", "", string)


def check_gcode(file):
    """
    Check if gcode fits the requirements that we have set in the config
    """
    parsedGcode = parse_gcode(file)

    for checkItem in config['gcodeCheckItems']:
        if GcodeCheckActions[checkItem['checkAction']] is GcodeCheckActions.REMOVE_COMMAND_ALL:
            for i in range(len(parsedGcode)):
                if parsedGcode[i].command == checkItem['command']:
                    parsedGcode.pop(i)

        elif GcodeCheckActions[checkItem['checkAction']] is GcodeCheckActions.ADD_COMMAND_AT_END:
            parsedGcode.append(GcodeLine(checkItem['command'], checkItem['actionValue'], ''))

        elif GcodeCheckActions[checkItem['checkAction']] is GcodeCheckActions.COMMAND_MUST_EXIST:
            commandFound = False
            for line in parsedGcode:
                if line.command == checkItem['command'] and line.command != ';':  # If it is not a comment, only check that the command is there.
                    commandFound = True
                    break
                elif line.command == checkItem['command'] and line.command == ';':  # If it is a comment, ensure the string matches.
                    if checkItem['actionValue'][0].lower().strip() in line.comment.lower().strip():
                        commandFound = True
                        break
            if not commandFound:
                return None, GcodeStates.INVALID

        elif GcodeCheckActions[checkItem['checkAction']] is GcodeCheckActions.COMMAND_PARAM_MIN:
            for line in parsedGcode:
                if line.command == checkItem['command']:
                    value = int(filter_characters(line.params[0]))  # Get int value of first param.
                    if value < int(checkItem['actionValue'][0]):
                        return None, GcodeStates.INVALID

        elif GcodeCheckActions[checkItem['checkAction']] is GcodeCheckActions.COMMAND_PARAM_MAX:
            for line in parsedGcode:
                if line.command == checkItem['command']:
                    value = int(filter_characters(line.params[0]))  # Get int value of first param.
                    if value > int(checkItem['actionValue'][0]):
                        return None, GcodeStates.INVALID

        elif GcodeCheckActions[checkItem['checkAction']] is GcodeCheckActions.COMMAND_PARAM_RANGE:
            for line in parsedGcode:
                if line.command == checkItem['command']:
                    value1 = int(filter_characters(line.params[0]))  # Get int value of first param.
                    value2 = int(filter_characters(line.params[1]))  # Get int value of second param.
                    if not value1 > int(checkItem['actionValue'][0]) > value2:
                        return None, GcodeStates.INVALID

    text_gcode = gcode_to_text(parsedGcode)
    return GcodeStates.VALID, text_gcode


def printIsNoGo(singleIssue, singleID):
    """
    If the print is a no-go and shouldn't continue
    """
    attachments = str(singleIssue).split(',')
    if any(config['base_url'] + "/secure/attachment" in s for s in attachments):
        print("Downloading " + singleID)
        matching = [s for s in attachments if config['base_url'] + "/secure/attachment" in s]
        attachment = str(matching[0]).split("'")
        filename = attachment[3].rsplit(config['ticketStartString'], 1)[-1]
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


def printIsGoodToGo(singleIssue, singleID, classKey):
    """
    Things to do when a print is good to go
    """
    attachments = str(singleIssue).split(',')
    if any(config['base_url'] + "/secure/attachment" in s for s in attachments):
        print("Downloading " + singleID)
        matching = [s for s in attachments if config['base_url'] + "/secure/attachment" in s]
        attachment = str(matching[0]).split("'")
        filename = attachment[3].rsplit('EHSL3DPR-', 1)[-1]
        download(attachment[3], singleID, filename)
        if validateClassKey(classKey, 5, 1) == ClassKeyStates.VALID:
            print("Skip payment, they had a valid class key")
        else:
            print("payment")
    elif any("https://drive.google.com/file/d/" in s for s in attachments):
        print("Downloading " + singleID + " from google drive")
        matching = [s for s in attachments if "https://drive.google.com/file/d/" in s]
        attachment = str(str(matching[0]).split("'"))
        start = "https://drive.google.com/file/d/"
        end = "/view?usp="
        downloadGoogleDrive(attachment[attachment.find(start) + len(start):attachment.rfind(end)], singleID)
        if validateClassKey(classKey, 5, 1) == ClassKeyStates.VALID:
            print("Skip payment, they had a valid class key")
        else:
            print("payment")
    else:
        commentStatus(
            singleID,
            config['messages']['noFile']
        )
        changeStatus(singleID, JiraTransitionCodes.START_PROGRESS)
        changeStatus(singleID, JiraTransitionCodes.STOP_PROGRESS)


def validateClassKey(key, cost, count):
    """
    class keys are used when you want to do bulk class orders
    """
    for singleKey in keys["CLASSKEYS"]:
        if keys["CLASSKEYS"][singleKey]["key"] == key:
            if keys["CLASSKEYS"][singleKey]["active"] is True:
                if count > 0:
                    keys['CLASSKEYS'][singleKey]['printCount'] = keys['CLASSKEYS'][singleKey]['printCount'] + count
                with open("keys.yml", 'w') as f:
                    yaml.safe_dump(keys, f, default_flow_style=False)
                if cost > 0:
                    keys['CLASSKEYS'][singleKey]['classCost'] = keys['CLASSKEYS'][singleKey]['classCost'] + cost
                with open("keys.yml", 'w') as f:
                    yaml.safe_dump(keys, f, default_flow_style=False)
                return ClassKeyStates.VALID
    return ClassKeyStates.INVALID


def changeStatus(singleID, transitionCode):
    """
    Changes status of issue in Jira.
    See enumDefinitions JiraTransitionCodes for codes.
    """
    simple_singleID = singleID.rsplit('__', 1)[-1]
    url = config['base_url'] + "/rest/api/2/issue/" + simple_singleID + "/transitions"
    headers = {
        "Content-type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "update": {
            "comment": [{
                "add": {
                    "body": "The ticket is resolved"
                }
            }]
        },
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


def commentStatus(singleID, comment):
    """
    a simple function call to be used whenever you want to comment on a ticket
    """
    simple_singleID = singleID.rsplit('__', 1)[-1]
    url = config['base_url'] + "/rest/api/2/issue/" + simple_singleID + "/comment"
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
    os.system('cls' if os.name == 'nt' else 'clear')
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
        comment = singleIssue['fields']['comment']['comments'][-1]['body']
        for trigger in config['requestUpdate']:
            if str(comment).find(trigger) != -1:
                print(comment)
                directory = r'jiradownloads'
                for filename in sorted(os.listdir(directory)):
                    if filename.find(ticketID):
                        commentStatus(ticketID, config["messages"]["statusInQueue"])
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
                        status = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
                        if str(status['job']['file']['name']).find(ticketID) != -1:
                            base = config['messages']['statusUpdate'] + "\n"
                            completion = "Completion: " + str(round(status['progress']['completion'], 2)) + "%" + "\n"
                            eta = "Print time left: " + str(time.strftime('%H:%M:%S', time.gmtime(status['progress']['printTimeLeft']))) + "\n"
                            material = "Cost: $" + str(round(
                                status['job']['filament']['tool0']['volume'] * printers['farm_printers'][printer]['materialDensity'] *
                                config['payment']['costPerGram'], 2)) + "\n"
                            end = config['messages']['statusUpdateEnd']

                            printerStatusUpdate = base + completion + eta + material + end
                            commentStatus(ticketID, printerStatusUpdate)
                            print(printerStatusUpdate)
                    except requests.exceptions.RequestException as e:  # This is the correct syntax
                        print("Skipping " + printer + " due to network error.")
                return
