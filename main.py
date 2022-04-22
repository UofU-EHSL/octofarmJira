import jira
import schedule
import time
import octoprint
import yaml
from pony.orm import *
from classes.printer import *
from classes.enumDefinitions import *

# set_sql_debug(True)  # Shows the SQL queries pony is running in the console.
db.bind(provider='sqlite', filename='octofarmJira_database.sqlite', create_db=True)  # Establish DB connection.
db.provider.converter_classes.append((Enum, EnumConverter))  # Add a custom enum converter to pony so we can use enums in the DB.
db.generate_mapping(create_tables=True)  # Required by pony.


with open("config_files/config.yml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)

jira.getGcode()
octoprint.eachNewFile()
octoprint.PrintIsFinished()

print("PRINT MONITORING SYSTEM LOOP STARTED")
schedule.every(config['updateRate']).minutes.do(jira.getGcode)
schedule.every(config['updateRate']).minutes.do(octoprint.eachNewFile)
schedule.every(config['updateRate']).minutes.do(octoprint.PrintIsFinished)
schedule.every(config['updateRate']).minutes.do(jira.askedForStatus)

while 1:
    schedule.run_pending()
    time.sleep(config['updateRate'])
