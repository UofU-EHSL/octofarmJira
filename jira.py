# This code sample uses the 'requests' library:
# http://docs.python-requests.org
import requests
import schedule
import time
from requests.auth import HTTPBasicAuth
import json

def issueList():
    print("Checking for new submissions...")
    """
    curl -D- -u ehsl_client:asdqwe123 -X GET -H "Content-Type: application/json" "https://projects.lib.utah.edu:8443/rest/api/2/search?jql=project=EHSL3DPR"
    """
    url = "https://projects.lib.utah.edu:8443/rest/api/2/search?jql=project%20%3D%20EHSL3DPR%20AND%20status%20%3D%20Open"
    auth = HTTPBasicAuth("ehsl_client", "asdqwe123")
    
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
        auth = HTTPBasicAuth("ehsl_client", "asdqwe123")
        
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
            
def download(gcode, singleID):
    url = gcode
    auth = HTTPBasicAuth("ehsl_client", "asdqwe123")
    
    headers = {
       "Accept": "application/json"
    }
    
    response = requests.request(
       "GET",
       url,
       headers=headers,
       auth=auth
    )

    text_file = open("jiradownloads/" + singleID + ".gcode", "w")
    n = text_file.write(response.text)
    text_file.close()
    changeStatus(singleID, "11")
    commentStatus(singleID, "Your print file has been downloaded and is now in the print queue.")

def changeStatus(singleID, id):
    """
    
    11 = in progress
    21 = submit for review
    32 = accept as done
    
    curl -u ehsl_client:asdqwe123 -X POST --data '{"transition":{"id":"11"}}' -H "Content-Type: application/json" "https://projects.lib.utah.edu:8443/rest/api/2/issue/55598/transitions"
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
    print("ticket" + singleID + " status updated to: " + id)
    
def commentStatus(singleID, comment):
    """
    curl -D- -u fred:fred -X POST --data {see below} -H "Content-Type: application/json" http://kelpie9:8081/rest/api/2/issue/QA-31/comment"
    """
    print("commenting on ticker " + singleID + ": " + comment)
    auth = HTTPBasicAuth("ehsl_client", "asdqwe123")
    url = "https://projects.lib.utah.edu:8443/rest/api/2/issue/" + singleID + "/comment"
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
