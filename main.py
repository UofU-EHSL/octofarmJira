import jira
import schedule
import time
import octoprint

print("PRINT MONITORING SYSTEM STARTED")
schedule.every(1).minutes.do(jira.getGcode)
schedule.every(1).minutes.do(octoprint.eachNewFile)

while 1:
    schedule.run_pending()
    time.sleep(1)

