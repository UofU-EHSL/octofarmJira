import jira
import schedule
import time
import octoprint
import yaml
from classes.printer import *


def main():
    set_sql_debug(True)  # Shows the SQL queries pony is running in the console.
    db.bind(provider='sqlite', filename='octofarmJira_database.sqlite', create_db=True)  # Establish DB connection.
    db.generate_mapping(create_tables=True)

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


if __name__ == "__main__":
    main()
