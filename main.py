import jira
import schedule
import time
import octoprint
import yaml

with open("config.yml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)

### we start the services from the start ###
jira.getGcode()
octoprint.eachNewFile()
octoprint.PrintIsFinished()

### Then the system loops the schedules functions ###
print("PRINT MONITORING SYSTEM LOOP STARTED")
schedule.every(config['updateRate']).minutes.do(jira.getGcode)
schedule.every(config['updateRate']).minutes.do(octoprint.eachNewFile)
schedule.every(config['updateRate']).minutes.do(octoprint.PrintIsFinished)

while 1:
    schedule.run_pending()
    time.sleep(config['updateRate'])
