import jira
import schedule
import time
import octoprint
import yaml
from classes.printer import *
from classes.permissionCode import *
from classes.printJob import *


def drop_and_create_db():
    db.generate_mapping(check_tables=False, create_tables=False)
    db.drop_all_tables(with_all_data=True)
    db.create_tables()

    with db_session:
        p1 = Printer(name='Prusa01', model=PrinterModel.PRUSA_MK3.name, ip='localhost:81', api_key='53148701F56E47368C7737DF546B1532', enabled=True, material_density=1.25)
        p2 = Printer(name='Prusa02', model=PrinterModel.PRUSA_MK3.name, ip='localhost:82', api_key='2ECDDF5FCFF44C56A4E864AFC1ABABD9', enabled=True, material_density=1.25)
        p3 = Printer(name='Prusa03', model=PrinterModel.PRUSA_MK3.name, ip='localhost:83', api_key='A004159B89CB4226BED7E66A442A76F6', enabled=True, material_density=1.25)
        p4 = Printer(name='Prusa04', model=PrinterModel.PRUSA_MK3.name, ip='localhost:84', api_key='0E00C61D6C964722A0D39B3D2CD98DBA', enabled=True, material_density=1.25)
        p5 = Printer(name='Prusa05', model=PrinterModel.PRUSA_MK3.name, ip='localhost:85', api_key='44D69C98F8B54EEA827988AFE667BA0A', enabled=True, material_density=1.25)

        pc1 = PermissionCode(name='Test1', code='abcd', description='No dates')
        pc2 = PermissionCode(name='Test2', code='abcde', description='Start Today', start_date=datetime.date.today())
        pc3 = PermissionCode(name='Test3', code='abcdef', description='Start Tomorrow', start_date=datetime.date.today() + datetime.timedelta(days=1))
        pc4 = PermissionCode(name='Test4', code='abcdefg', description='End Today', end_date=datetime.date.today())
        pc5 = PermissionCode(name='Test5', code='abcdefgh', description='End Tomorrow', end_date=datetime.date.today() + datetime.timedelta(days=1))
        pc6 = PermissionCode(name='Test6', code='abcdefghi', description='Both dates valid', start_date=datetime.date.today() - datetime.timedelta(days=1), end_date=datetime.date.today() + datetime.timedelta(days=1))
        pc6 = PermissionCode(name='Test7', code='abcdefghij', description='Both dates not valid', start_date=datetime.date.today() - datetime.timedelta(days=2), end_date=datetime.date.today() - datetime.timedelta(days=1))


def print_loop():
    jira.getGcode()
    octoprint.eachNewFile()
    octoprint.PrintIsFinished()
    jira.askedForStatus()


def main():
    set_sql_debug(False)  # Shows the SQL queries pony is running in the console.
    db.bind(provider='sqlite', filename='octofarmJira_database.sqlite', create_db=True)  # Establish DB connection.
    # db.generate_mapping(create_tables=True)
    drop_and_create_db()

    with open("config_files/config.yml", "r") as yamlfile:
        config = yaml.load(yamlfile, Loader=yaml.FullLoader)

    print_loop()
    print("PRINT MONITORING SYSTEM LOOP STARTED")
    schedule.every(config['updateRate']).minutes.do(print_loop)

    while 1:
        schedule.run_pending()
        time.sleep(config['updateRate'])


if __name__ == "__main__":
    main()
