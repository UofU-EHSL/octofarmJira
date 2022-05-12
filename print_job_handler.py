import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
from google_drive_downloader import GoogleDriveDownloader as gdd

import jira
from classes.gcodeLine import GcodeLine
from classes.printer import *
from classes.permissionCode import *
from classes.message import *
from classes.printJob import *
import os
import time
from classes.enumDefinitions import *
import re

# load all of our config files
with open("config_files/config.yml", "r") as yamlFile:
    config = yaml.load(yamlFile, Loader=yaml.FullLoader)

drive_api_key = config['google_drive_api_key']


@db_session
def process_new_jobs():
    new_jobs = PrintJob.Get_All_By_Status(PrintStatus.NEW)
    for job in new_jobs:
        if not job.gcode_url:  # If there is no gcode_url, no files were attached.
            handle_job_failure(job, MessageNames.NO_FILE_ATTACHED)
            continue

        elif config["use_naughty_list"] is True and job.user.black_listed:
            handle_job_failure(job, MessageNames.BLACK_LIST_FAIL)
            continue

        elif config["use_nice_list"] is True and not job.user.white_listed:
            handle_job_failure(job, MessageNames.WHITE_LIST_FAIL)
            continue

        elif job.permission_code:  # If there is a permission code, validate it.
            code_state = PermissionCode.Validate_Permission_Code(job.permission_code.code)
            if code_state == PermissionCodeStates.INVALID:
                handle_job_failure(job, MessageNames.PERMISSION_CODE_INVALID)
                continue
            elif code_state == PermissionCodeStates.EXPIRED:
                handle_job_failure(job, MessageNames.PERMISSION_CODE_EXPIRED)
                continue
            elif code_state == PermissionCodeStates.NOT_YET_ACTIVE:
                handle_job_failure(job, MessageNames.PERMISSION_CODE_NOT_YET_ACTIVE)
                continue

        gcode = download_gcode(job)

        if gcode == "ERROR":
            handle_job_failure(job, MessageNames.UNKNOWN_DOWNLOAD_ERROR)
            continue
        elif gcode == "ERROR_403":
            handle_job_failure(job, MessageNames.GOOGLE_DRIVE_403_ERROR)
            continue
        else:
            checked_gcode, check_result = check_gcode(gcode)
            if check_result == GcodeStates.VALID:
                text_file = open(job.Get_File_Name(), "w")
                n = text_file.write(checked_gcode)
                text_file.close()
                job.print_status = PrintStatus.IN_QUEUE.name
                jira.send_print_queued(job.job_id)
            elif check_result == GcodeStates.INVALID:
                handle_job_failure(job, MessageNames.GCODE_CHECK_FAIL)


def download_gcode(job):
    try:
        if job.url_type == UrlTypes.JIRA_ATTACHMENT.name:
            return jira.download(job)
        elif job.url_type == UrlTypes.GOOGLE_DRIVE.name:
            return downloadGoogleDrive(job)
        elif job.url_type == UrlTypes.UNKNOWN.name:
            return "ERROR"
    except:
        return "ERROR"


def downloadGoogleDrive(job):
    """
    if the jira project has a Google Drive link in the description download it
    """
    url = 'https://www.googleapis.com/drive/v3/files/' + job.gcode_url + '/?key=' + drive_api_key + '&alt=media'

    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.request(
            "GET",
            url,
            headers=headers,
        )
    except Exception as e:
        print("Ticket " + job.Get_Name() + " error while downloading gcode from google drive.")
        print(e)
        return "ERROR"

    if response.ok:
        return response.text
    elif response.status_code == 403:
        return "ERROR_403"
    else:
        print("Ticket " + job.Get_Name() + ": " + str(response.status_code) + " while downloading gcode from google drive.")
        return "ERROR"


def handle_job_failure(job, message_name):
    message = Message.get(name=message_name.name)
    if message:
        job.failure_message = message.id
        jira.send_fail_message(job.job_id, message.text)
    else:
        print("No message found for:", message_name)
        print("Suggest adding it in the admin panel.")
    job.print_status = PrintStatus.CANCELLED.name
    commit()


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
    return text_gcode, GcodeStates.VALID
