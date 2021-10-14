import jira
import schedule
import time

print("PRINT MONITORING SYSTEM STARTED")
schedule.every(1).minutes.do(jira.getGcode)

while 1:
    schedule.run_pending()
    time.sleep(1)

