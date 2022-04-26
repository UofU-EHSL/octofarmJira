import jira
import schedule
import time
import octoprint
import yaml
from pony.orm import *
from classes.printer import *
from classes.enumDefinitions import *


def main():
    set_sql_debug(True)  # Shows the SQL queries pony is running in the console.
    db.bind(provider='sqlite', filename='octofarmJira_database.sqlite', create_db=True)  # Establish DB connection.
    db.generate_mapping(create_tables=True)

    # db.generate_mapping(check_tables=False, create_tables=False)
    # db.drop_all_tables(with_all_data=True)
    # db.create_tables()
    #
    # with db_session:
    #     p1 = Printer(name='Prusa01', model=PrinterModel.PRUSA_MK3.name, ip='localhost:81', api_key='53148701F56E47368C7737DF546B1532')
    #     p2 = Printer(name='Prusa02', model=PrinterModel.PRUSA_MK3.name, ip='localhost:82', api_key='2ECDDF5FCFF44C56A4E864AFC1ABABD9')
    #     p3 = Printer(name='Prusa03', model=PrinterModel.PRUSA_MK3.name, ip='localhost:83', api_key='A004159B89CB4226BED7E66A442A76F6')
    #     p4 = Printer(name='Prusa04', model=PrinterModel.PRUSA_MK3.name, ip='localhost:84', api_key='0E00C61D6C964722A0D39B3D2CD98DBA')
    #     p5 = Printer(name='Prusa05', model=PrinterModel.PRUSA_MK3.name, ip='localhost:85', api_key='44D69C98F8B54EEA827988AFE667BA0A')

    with open("config_files/config.yml", "r") as yamlfile:
        config = yaml.load(yamlfile, Loader=yaml.FullLoader)

    printers = Printer.Get_All_Enabled()

    # jira.getGcode()
    # octoprint.eachNewFile()
    # octoprint.PrintIsFinished()
    #
    # print("PRINT MONITORING SYSTEM LOOP STARTED")
    # schedule.every(config['updateRate']).minutes.do(jira.getGcode)
    # schedule.every(config['updateRate']).minutes.do(octoprint.eachNewFile)
    # schedule.every(config['updateRate']).minutes.do(octoprint.PrintIsFinished)
    # schedule.every(config['updateRate']).minutes.do(jira.askedForStatus)

    # while 1:
    #     schedule.run_pending()
    #     time.sleep(config['updateRate'])


if __name__ == "__main__":
    main()
