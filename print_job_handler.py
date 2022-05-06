import requests
from requests.auth import HTTPBasicAuth
import json
import yaml
from google_drive_downloader import GoogleDriveDownloader as gdd
from classes.gcodeLine import GcodeLine
from classes.printer import *
from classes.permissionCode import *
from classes.printJob import *
import os
import time
from classes.enumDefinitions import *
import re

# load all of our config files
with open("config_files/config.yml", "r") as yamlFile:
    config = yaml.load(yamlFile, Loader=yaml.FullLoader)


@db_session
def process_new_jobs():
    new_jobs = PrintJob.Get_All_By_Status(PrintStatus.NEW)
    for job in new_jobs:
        if config["use_naughty_list"] is True and job.user.black_listed:
            pass  # TODO: Handle black list fail
        if config["use_nice_list"] is True and not job.user.white_listed:
            pass  # TODO: Handle white list fail
        if job.permission_code:
            code_state = PermissionCode.Validate_Permission_Code(job.permission_code.code)
            if code_state != PermissionCodeStates.VALID:
                pass  # TODO: Handle bad code
    # TODO: Download gcode and parse


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
