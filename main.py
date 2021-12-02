import jira
import schedule
import time
import octoprint
import os

jira.getGcode()
octoprint.eachNewFile()
octoprint.PrintIsFinished()


print("PRINT MONITORING SYSTEM STARTED")
schedule.every(1).minutes.do(jira.getGcode)
schedule.every(1).minutes.do(octoprint.eachNewFile)
schedule.every(1).minutes.do(octoprint.PrintIsFinished)
os.system('cls' if os.name == 'nt' else 'clear')

while 1:
    schedule.run_pending()
    time.sleep(1)

