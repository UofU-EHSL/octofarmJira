import requests
import schedule
import time
from requests.auth import HTTPBasicAuth
import json
import yaml
from google_drive_downloader import GoogleDriveDownloader as gdd
import find
import os

from app import CONFIG, KEYS

with open("config.yml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)

with open("lists.yml", "r") as yamlfile:
    userlist = yaml.load(yamlfile, Loader=yaml.FullLoader)

with open("keys.yml", "r") as yamlfile:
    keys = yaml.load(yamlfile, Loader=yaml.FullLoader)

auth = HTTPBasicAuth(config['jira_user'], config['jira_password'])

def issueList():
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
    openissues = json.loads(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    issues= []
    for issue in openissues['issues']:
        issues.append(issue['self'])
    return issues

def getGcode():
    for issue in issueList():
        id = issue.split("/")
        singleID = id[-1]
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
        
        #parsing class key value
        start = "*Class Key* \\\\"
        end = "\n\n*Description of print*"
        s = singleIssue['fields']['description']
        classKey = s[s.find(start)+len(start):s.rfind(end)]
        
        ## keys can be validated and update the key logs but keys do not change if a print is to be printed or not yet.
        
        
        ##If someone is nice they go in here
        if user in userlist["NICE"] and config["use_nice_list"] == True:
            printIsGoodToGo(singleIssue, singleID, classKey)
        #if they are naughty they go in here
        elif user in userlist["NAUGHTY"] and config["use_naughty_list"] == True:
            printIsNoGo(singleID, singleID)
            if os.path.exists("jiradownloads/" + singleID + ".gcode"):
                os.remove("jiradownloads/" + singleID + ".gcode")
        # if they are a new user they go in here
        else :
            if config["use_naughty_list"] == True:
                printIsGoodToGo(singleIssue, singleID, classKey)
            elif config["use_nice_list"] == True:
                printIsNoGo(singleIssue, singleID)
            elif config["use_naughty_list"] == False and config["use_naughty_list"] == False:
                printIsGoodToGo(singleIssue, singleID, classKey)
                

def downloadGoogleDrive(file_ID, singleID):
    if config['Make_files_anon'] == True:
        gdd.download_file_from_google_drive(file_id=file_ID, dest_path="jiradownloads/" + singleID + ".gcode")
        file = open("jiradownloads/" + singleID + ".gcode", "r")
    else:
        gdd.download_file_from_google_drive(file_id=file_ID, dest_path="jiradownloads/" + file_ID + "__" + singleID + ".gcode")
        file = open("jiradownloads/" + file_ID + "__" + singleID + ".gcode", "r")
    
    if checkGcode(file.read()) == "Bad G-code":
        commentStatus(singleID, config['messages']['wrongConfig'])
        changeStatus(singleID, "11")
        changeStatus(singleID, "21")
        changeStatus(singleID, "131")
        if os.path.exists("jiradownloads/" + singleID + ".gcode"):
            os.remove("jiradownloads/" + singleID + ".gcode")
    else:
        changeStatus(singleID, "11")
        commentStatus(singleID, config['messages']['downloadedFile'])

def download(gcode, singleID, filename):
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
    if checkGcode(response.text) == "Bad G-code":
        commentStatus(singleID, config['messages']['wrongConfig'])
        changeStatus(singleID, "11")
        changeStatus(singleID, "21")
        changeStatus(singleID, "131")
    else:
        if config['Make_files_anon'] == True:
            text_file = open("jiradownloads/" + singleID + ".gcode", "w")
        else:
            text_file = open("jiradownloads/" + filename + "__" + singleID + ".gcode", "w")
        n = text_file.write(response.text)
        text_file.close()
        changeStatus(singleID, "11")
        commentStatus(singleID, config['messages']['downloadedFile'])


def checkGcode(file):
    status = True
    for code_check in config['gcode_check_text']:
        code_to_check = config['gcode_check_text'][code_check]
        print(code_to_check)
        if code_to_check not in file:
            status = False
        if status == False:
            print("File is bad at: " + code_check)
            return "Bad G-code"
    if status == True:
        print("File checkedout as good")
        return "Valid G-code"

def printIsNoGo(singleIssue, singleID):
    attachments = str(singleIssue).split(',')
    if any("https://projects.lib.utah.edu:8443/secure/attachment" in s for s in attachments):
        print("Downloading " + singleID)
        matching = [s for s in attachments if "https://projects.lib.utah.edu:8443/secure/attachment" in s]
        attachment = str(matching[0]).split("'")
        filename = attachment[3].rsplit('EHSL3DPR-', 1)[-1]
        download(attachment[3], singleID, filename)
    elif any("https://drive.google.com/file/d/" in s for s in attachments):
        print("Downloading " + singleID + " from google drive")
        matching = [s for s in attachments if "https://drive.google.com/file/d/" in s]
        attachment = str(str(matching[0]).split("'"))
        start = "https://drive.google.com/file/d/"
        end = "/view?usp=sharing"
        downloadGoogleDrive(attachment[attachment.find(start)+len(start):attachment.rfind(end)], singleID)
    else:
        commentStatus(
            singleID,
            "Please try again and make sure to upload a file, if your file is larger than 25mb then paste a google drive share link in the description of the print"
        )
        changeStatus(singleID, "11")
        changeStatus(singleID, "111")

def printIsGoodToGo(singleIssue, singleID, classKey):
    
    attachments = str(singleIssue).split(',')
    if any("https://projects.lib.utah.edu:8443/secure/attachment" in s for s in attachments):
        print("Downloading " + singleID)
        matching = [s for s in attachments if "https://projects.lib.utah.edu:8443/secure/attachment" in s]
        attachment = str(matching[0]).split("'")
        filename = attachment[3].rsplit('EHSL3DPR-', 1)[-1]
        download(attachment[3], singleID, filename)
        if validateClassKey(classKey, 5, 1) == "Valid key":
            print("Skip payment, they had a valid class key")
        else:
            print("payment")
    elif any("https://drive.google.com/file/d/" in s for s in attachments):
        print("Downloading " + singleID + " from google drive")
        matching = [s for s in attachments if "https://drive.google.com/file/d/" in s]
        attachment = str(str(matching[0]).split("'"))
        start = "https://drive.google.com/file/d/"
        end = "/view?usp=sharing"
        downloadGoogleDrive(attachment[attachment.find(start)+len(start):attachment.rfind(end)], singleID)
        if validateClassKey(classKey, 5, 1) == "Valid key":
            print("Skip payment, they had a valid class key")
        else:
            print("payment")
    else:
        commentStatus(
            singleID,
            "Please try again and make sure to upload a file, if your file is larger than 25mb then paste a google drive share link in the description of the print"
        )
        changeStatus(singleID, "11")
        changeStatus(singleID, "111")

def validateClassKey(key, cost, count):
    for singlekey in keys["CLASSKEYS"]:
        if keys["CLASSKEYS"][singlekey]["key"] == key:
            if keys["CLASSKEYS"][singlekey]["active"] == True:
                if count > 0:
                    keys['CLASSKEYS'][singlekey]['printCount'] = keys['CLASSKEYS'][singlekey]['printCount'] + count
                with open("keys.yml", 'w') as f:
                    yaml.safe_dump(keys, f, default_flow_style=False)
                if cost > 0:
                    keys['CLASSKEYS'][singlekey]['classCost'] = keys['CLASSKEYS'][singlekey]['classCost'] + cost
                with open("keys.yml", 'w') as f:
                    yaml.safe_dump(keys, f, default_flow_style=False)
                return "Valid key"
    return "Bad key"

def changeStatus(singleID, id):
    """
    Start Progress: 11 (From Open to In Progress)
    Ready for review: 21 (From In Progress to UNDER REVIEW)
    Stop Progress: 111 (From In Progress to CANCELLED)
    Approve : 31 (From Under Review to APPROVED)
    Reject: 131 (From Under Review to REJECTED)
    Done: 41  (From APPROVED to DONE)
    Reopen: 121  (From Cancelled to OPEN)
    Start progress : 141  (From REJECTEDto IN PROGRESS)
    """
    simple_singleID = singleID.rsplit('__', 1)[-1]
    url = config['base_url'] + "/rest/api/2/issue/" + simple_singleID + "/transitions"
    headers = {
       "Content-type": "application/json",
       "Accept" : "application/json"
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
            "id":id
        }
    }
    
    response = requests.request(
        "POST",
        url,
        headers=headers,
        json = data,
        auth=auth
    )
    
def commentStatus(singleID, comment):
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
