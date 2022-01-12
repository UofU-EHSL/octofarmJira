import requests
import schedule
import time
from requests.auth import HTTPBasicAuth
import json
import yaml
from google_drive_downloader import GoogleDriveDownloader as gdd
import find
import os
import re

from app import KEYS

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
    try:
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
    except:
        print("No new tickets")

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

def getGcode():
    i = 0
    listOfIssues = None
    while listOfIssues is None:
        listOfIssues = issueList()
        i = i + 1
        if i > 5:
            print("I could not get any issues in the issue list for 5 times in a row. You are being rate limited.")
            raise TypeError
    for issue in listOfIssues:
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
        #print(singleIssue['fields']['description'])
        user = singleIssue['fields']['reporter']['name']
        #print(singleIssue)
        #parsing class key value
        start = "*Class Key* \\\\"
        end = "\n\n*Description of print*"
        s = singleIssue['fields']['description']
        description = s.splitlines()
        taxExempt = False
        for line in description:
            #print(line)
            if 'Tax Exempt' in line:
                print(line.split('*Tax Exempt* \\\\')[1])
                if line.split('*Tax Exempt* \\\\')[1] == "Yes":
                    taxExempt = True
        classKey = s[s.find(start)+len(start):s.rfind(end)]
        #print(s)
        ## keys can be validated and update the key logs but keys do not change if a print is to be printed or not yet.
<<<<<<< Updated upstream
        print(validateClassKey(classKey,5,1))

        if user in userlist["NICE"]:
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
        elif user in userlist["NAUGHTY"]:
            print(user + " is on the naughty list and was rejected")
            commentStatus(
                singleID,
                "Your print was not printed, please contact " + config["contact_info"]
            )
            changeStatus(singleID, "11")
            changeStatus(singleID, "21")
            changeStatus(singleID, "131")
=======
        
        
        ##If someone is nice they go in here
        if user in userlist["NICE"] and config["use_nice_list"] == True:
            printIsGoodToGo(singleIssue, singleID, classKey, taxExempt)
        #if they are naughty they go in here
        elif user in userlist["NAUGHTY"] and config["use_naughty_list"] == True:
            printIsNoGo(singleID, singleID)
>>>>>>> Stashed changes
            if os.path.exists("jiradownloads/" + singleID + ".gcode"):
                os.remove("jiradownloads/" + singleID + ".gcode")
        else :
<<<<<<< Updated upstream
            print(user + " is a new user and was rejected")
            commentStatus(
                singleID,
                "Your print was rejected becuase you have not completed the canvas cource at " + config["link_to_canvas_class"]
            )
            changeStatus(singleID, "11")
            changeStatus(singleID, "21")
            changeStatus(singleID, "131")
            if os.path.exists("jiradownloads/" + singleID + ".gcode"):
                os.remove("jiradownloads/" + singleID + ".gcode")

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
=======
            if config["use_naughty_list"] == True:
                printIsGoodToGo(singleIssue, singleID, classKey, taxExempt)
            elif config["use_nice_list"] == True:
                printIsNoGo(singleIssue, singleID)
                
>>>>>>> Stashed changes

def downloadGoogleDrive(file_ID, singleID):
    if config['Make_files_anon'] == True:
        gdd.download_file_from_google_drive(file_id=file_ID, dest_path="jiradownloads/" + singleID + ".gcode")
        file = open("jiradownloads/" + singleID + ".gcode", "r")
    else:
        gdd.download_file_from_google_drive(file_id=file_ID, dest_path="jiradownloads/" + file_ID + "__" + singleID + ".gcode")
        file = open("jiradownloads/" + file_ID + "__" + singleID + ".gcode", "r")
    
    passFail, editedGcode = checkGcode(response.text, singleID)
    if passFail == "Bad G-code":
        commentStatus(singleID, "Please follow the slicing instructions and re-submit. Our automated check suggests you did not use our slicer configs")
        changeStatus(singleID, "11")
        changeStatus(singleID, "21")
        changeStatus(singleID, "131")
        if os.path.exists("jiradownloads/" + singleID + ".gcode"):
            os.remove("jiradownloads/" + singleID + ".gcode")
    elif passFail == "Manual G-code":
        if config['Make_files_anon'] == True:
            text_file = open("manual_prints/" + singleID + ".gcode", "w")
        else:
            text_file = open("manual_prints/" + filename + "__" + singleID + ".gcode", "w")
        n = text_file.write(editedGcode)
        text_file.close()
        changeStatus(singleID, "11")
        commentStatus(singleID, "Your print will need to be started manually by a human (TAZ prints and Gigabot prints cannot be started automatically) A teammember will start it for you as soon as they are available.")
    elif passFail == "Valid G-code":
        if config['Make_files_anon'] == True:
            text_file = open("jiradownloads/" + singleID + ".gcode", "w")
        else:
            text_file = open("jiradownloads/" + filename + "__" + singleID + ".gcode", "w")
        n = text_file.write(editedGcode)
        text_file.close()
        changeStatus(singleID, "11")
        #commentStatus(singleID, "Your print file has been downloaded and is now in the print queue.")
    #this final case may be unneccesary
    else:
        changeStatus(singleID, "11")
        commentStatus(singleID, "Your print file has been downloaded and is now in the print queue.")

def download(gcode, singleID, filename, taxExempt=False):
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
    
    projectNumber = gcode.split('/')[-1].split('_')[0]
    passFail, editedGcode = checkGcode(response.text, singleID, taxExempt, projectNumber)
    if passFail == "Bad G-code":
        commentStatus(singleID, "Please follow the slicing instructions and re-submit. Our automated check suggests you did not use our slicer configs")
        changeStatus(singleID, "11")
        changeStatus(singleID, "21")
        changeStatus(singleID, "131")
    elif passFail == "Valid G-code":
        if config['Make_files_anon'] == True:
            text_file = open("jiradownloads/" + singleID + ".gcode", "w")
        else:
            text_file = open("jiradownloads/" + filename + "__" + singleID + ".gcode", "w")
        n = text_file.write(editedGcode)
        text_file.close()
        changeStatus(singleID, "11")
        #commentStatus(singleID, "Your print file has been downloaded and is now in the print queue.")
    elif passFail == "Manual G-code":
        if config['Make_files_anon'] == True:
            text_file = open("manual_prints/" + singleID + ".gcode", "w")
        else:
            text_file = open("manual_prints/" + filename + "__" + singleID + ".gcode", "w")
        n = text_file.write(editedGcode)
        text_file.close()
        changeStatus(singleID, "11")
        commentStatus(singleID, "Your print will need to be started manually by a human (TAZ prints and Gigabot prints cannot be started automatically) A teammember will start it for you as soon as they are available.")


def customGcodeCheck(file, ticketID='', taxExempt=False, projectNumber=''):
    lineCount = 0
    maxtemp = config['custom_gcode_check']['max_hotend']
    maxbed = config['custom_gcode_check']['max_bed']
    splitFile = file.splitlines()
    if "generated by PrusaSlicer" not in splitFile[0]:
        return "Bad G-code", file
    m0Included = False
    for line in splitFile:
        ##Check Whole File
        if "M0 " in line:
            if "Start" in line:
                line = ";" + line
            else:
                m0Included = True
        if 'M300' in line:
            line = ";" + line
        #nozzle temp checks
        if "M109" in line and "start_gcode" not in line and "end_gcode" not in line:
            M109 = str((re.findall('\d+', line))[-1])
            if int(M109) > int(maxtemp):
                return "Bad G-code", file
        if "M104" in line and "start_gcode" not in line and "end_gcode" not in line:
            M104 = str((re.findall('\d+', line))[-1])
            if int(M104) > int(maxtemp):
                return "Bad G-code", file
        #bed temp checks
        if "M190" in line and "start_gcode" not in line and "end_gcode" not in line:
            M190 = str((re.findall('\d+', line))[-1])
            if int(M190) > int(maxbed):
                return "Bad G-code", file
        if "M140" in line and "start_gcode" not in line and "end_gcode" not in line:
            M140 = str((re.findall('\d+', line))[-1])
            if int(M140) > int(maxbed):
                return "Bad G-code", file
        ##Check end of file
        if "[mm]" in line:
            m0line = lineCount-1
            while lineCount < len(splitFile)-1:
                lineCount = lineCount + 1
                if "; printer_settings_id" in splitFile[lineCount]:
                    printerID = splitFile[lineCount].split('= ')[-1].split(' - ')[0]
                    
                    #print(printerID)
                if "; filament_settings_id" in splitFile[lineCount]:
                    filamentSettings = splitFile[lineCount].split('= ')[-1].strip('"').split(' - ')[0]
                    #print(filamentSettings)
                if "; print_settings_id" in splitFile[lineCount]:
                    printerSettings = splitFile[lineCount].split('= ')[-1].split(' - ')[0]
                    #print(printerSettings)
                if "total filament used" in splitFile[lineCount]:
                    grams = (re.findall("\d+\.\d+", splitFile[lineCount]))[0]
                    #print(str(grams) + ' grams of filament used')
                if "filament_density" in splitFile[lineCount]:
                    density = (re.findall(r"([\d.]*\d+)", splitFile[lineCount]))[0]
                    if 1.24 > float(density):
                        return "Bad G-code", file
                    #print(str(density) + " g/cm^3 filament density")
                if "filament_diameter" in splitFile[lineCount]:
                    diameter = (re.findall("\d+\.\d+", splitFile[lineCount]))[0]
                    #print(str(diameter) + " mm filament diameter")
                if "printing time (normal mode)" in splitFile[lineCount]:
                    printingTime = splitFile[lineCount].split('= ')[-1]
                    #print(printingTime + " print duration")
                if "; printer_notes =" in splitFile[lineCount]:
                    profileVersion = splitFile[lineCount].split('~ ')[-1]
                    #print(profileVersion)
        lineCount = lineCount + 1
    if len(ticketID) > 0:
        splitFile[0] = splitFile[0] +",GRAMS="+grams+",TIME="+printingTime+",PRINTER="+printerID+",FILAMENT="+filamentSettings+",PRINT="+printerSettings+",ID="+str(ticketID)+",TAXEXEMPT="+str(taxExempt)+",PROJECTNUMBER="+projectNumber+",LINK=https://projects.lib.utah.edu:8443/browse/"+projectNumber
        print(splitFile[0])
    else:
        splitFile[0] = splitFile[0] +",GRAMS="+grams+",TIME="+printingTime+",PRINTER="+printerID+",FILAMENT="+filamentSettings+",PRINT="+printerSettings+",TAXEXEMPT="+str(taxExempt)
    i = 0
    filamentGcodeFound = False
    for line in splitFile:
        if ';LAYER_CHANGE' in line:
            filamentGcodeFound = True
        if filamentGcodeFound == True:
            #blankLine = i
            #splitFile[i] = splitFile[i] + '\nM117 ' + str(ticketID) + ' ' + grams[0] + "g" +'\n' #modify second line
            if projectNumber != '' and ticketID != '':
                splitFile[i] = "M117 "+projectNumber+" "+str(ticketID)+" "+str(grams)+"g"
            else:
                splitFile[i] = "M117 " + str(grams) + "g" 
            break
        i = i + 1
    
    if m0Included == False:
        splitFile[m0line] = splitFile[m0line] + "\nM0 Done? " + projectNumber +' ' + grams.split('.')[0] + 'g'
    if "MK3S" in printerID and "PLA" in filamentSettings and "Prusa" in printerSettings and float(diameter) == 1.75:
        return "Valid G-code", "\n".join(splitFile)
    elif "TAZ 6" in printerID and "PLA" in filamentSettings and "TAZ 6" in printerSettings and float(diameter) == 2.85:
        return "Manual G-code", "\n".join(splitFile)
    elif "Gigabot" in printerID and "PLA" in filamentSettings and "Gigabot" in printerSettings and float(diameter) == 2.85:
        return "Manual G-code", "\n".join(splitFile)
    else:
        return "Bad G-code", file

<<<<<<< Updated upstream
=======
def checkGcode(file, ticketID='', taxExempt=False, projectNumber=''):
    try:
        runCustomChecks = config['gcode_check_text']['customChecks']
    except NameError:
        runCustomChecks = False
        print('Add the line "customChecks: false" to your gcode_check_text: section in config.yml to remove this warning')
    if runCustomChecks == False:
        status = True
        for code_check in config['gcode_check_text']:
            code_to_check = config['gcode_check_text'][code_check]
            print(code_to_check)
            if code_to_check not in file:
                status = False
            if status == False:
                print("File is bad at: " + code_check)
                return "Bad G-code", file
        if status == True:
            print("File checkedout as good")
            return "Valid G-code", file
    else:
        if len(ticketID) > 0:
            status, file = customGcodeCheck(file, ticketID, taxExempt, projectNumber)
        else:
            status, file = customGcodeCheck(file)
        return(status, file)

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

def printIsGoodToGo(singleIssue, singleID, classKey, taxExempt=False):
    attachments = str(singleIssue).split(',')
    if any("https://projects.lib.utah.edu:8443/secure/attachment" in s for s in attachments):
        print("Downloading " + singleID)
        matching = [s for s in attachments if "https://projects.lib.utah.edu:8443/secure/attachment" in s]
        attachment = str(matching[0]).split("'")
        
        filename = attachment[3].rsplit('EHSL3DPR-', 1)[-1]
        download(attachment[3], singleID, filename, taxExempt)
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
            "Please try again and make sure to upload a file, if your file is larger than 25mb then paste a google drive share link in the description of the print. Here is a video showing how to make a public google drive link: https://youtu.be/GkNTohTTIjY"
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

>>>>>>> Stashed changes
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
