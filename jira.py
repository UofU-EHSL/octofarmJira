import requests
import schedule
import time
from requests.auth import HTTPBasicAuth
import json
import yaml
from google_drive_downloader import GoogleDriveDownloader as gdd
import find

with open("config.yml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)
    print("Read successful")

auth = HTTPBasicAuth(config['jira_user'], config['jira_password'])

def issueList():
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
        
        attachments = str(singleIssue).split(',')
        if any("https://projects.lib.utah.edu:8443/secure/attachment" in s for s in attachments):
            print("Downloading " + singleID)
            matching = [s for s in attachments if "https://projects.lib.utah.edu:8443/secure/attachment" in s]
            attachment = str(matching[0]).split("'")
            download(attachment[3], singleID)
        elif any("https://drive.google.com/file/d/" in s for s in attachments):
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

def downloadGoogleDrive(file_ID, singleID):
    gdd.download_file_from_google_drive(file_id=file_ID, dest_path="jiradownloads/" + singleID + ".gcode")
    if config['gcode_check_text'] not in text_file == open("jiradownloads/" + singleID + ".gcode", "w"):
        commentStatus(singleID, "Please follow the slicing instructions and re-submit. Our automated check suggests you did not use our slicer configs")
        changeStatus(singleID, "11")
        changeStatus(singleID, "21")
        changeStatus(singleID, "131")
        if os.path.exists("jiradownloads/" + singleID + ".gcode"):
            os.remove("jiradownloads/" + singleID + ".gcode")
    else:
        changeStatus(singleID, "11")
        commentStatus(singleID, "Your print file has been downloaded and is now in the print queue.")

def download(gcode, singleID):
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
    if config['gcode_check_text'] not in response.text:
        commentStatus(singleID, "Please follow the slicing instructions and re-submit. Our automated check suggests you did not use our slicer configs")
        changeStatus(singleID, "11")
        changeStatus(singleID, "21")
        changeStatus(singleID, "131")
    else:
        text_file = open("jiradownloads/" + singleID + ".gcode", "w")
        n = text_file.write(response.text)
        text_file.close()
        changeStatus(singleID, "11")
        commentStatus(singleID, "Your print file has been downloaded and is now in the print queue.")

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
    print("updating ticket " + singleID + "...")
    auth = HTTPBasicAuth("ehsl_client", "asdqwe123")
    url = "https://projects.lib.utah.edu:8443/rest/api/2/issue/" + singleID + "/transitions"
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
    print("ticket" + str(singleID) + " status updated to: " + str(id))
    
def commentStatus(singleID, comment):
    print("commenting on ticker " + singleID + ": " + comment)
    url = config['base_url'] + "/rest/api/2/issue/" + singleID + "/comment"
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

getGcode()
