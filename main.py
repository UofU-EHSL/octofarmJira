import jira
import os
import schedule
import octoprint
import yaml
from classes.permissionCode import *
from classes.gcodeCheckItem import *
import print_job_handler


def drop_and_create_db():
    db.generate_mapping(check_tables=False, create_tables=False)
    db.drop_all_tables(with_all_data=True)
    db.create_tables()

    with db_session:
        kw1 = Keyword(name='PrusaMK3S', description='Key to check for prusa model printers.', value='MLIB_PRUSAMK3S')
        kw2 = Keyword(name='Config Version 1', description='Version 1 created on: DATE', value='MLIB_BUNDLE_V1')
        kw3 = Keyword(name='Gigabot', description='Key to check for prusa model printers.', value='MLIB_GIGABOT')

        commit()

        pm1 = PrinterModel(name="PrusaMK3S", description="Best printer out there.", keyword=1, auto_start_prints=True)
        pm2 = PrinterModel(name="Gigabot", description="Big boi", keyword=3, auto_start_prints=False)

        commit()

        p1 = Printer(name='Prusa01', printer_model=1, ip='localhost:81', api_key='53148701F56E47368C7737DF546B1532', enabled=True, material_density=1.25)
        p2 = Printer(name='Prusa02', printer_model=1, ip='localhost:82', api_key='2ECDDF5FCFF44C56A4E864AFC1ABABD9', enabled=True, material_density=1.25)
        p3 = Printer(name='Prusa03', printer_model=1, ip='localhost:83', api_key='A004159B89CB4226BED7E66A442A76F6', enabled=True, material_density=1.25)
        p4 = Printer(name='Prusa04', printer_model=1, ip='localhost:84', api_key='0E00C61D6C964722A0D39B3D2CD98DBA', enabled=True, material_density=1.25)
        p5 = Printer(name='Prusa05', printer_model=1, ip='localhost:85', api_key='44D69C98F8B54EEA827988AFE667BA0A', enabled=True, material_density=1.25)
        p6 = Printer(name='Gigaboi', printer_model=2, ip='localhost:86', api_key='test', enabled=True, material_density=1.25)

        pc1 = PermissionCode(name='INVALID', code='INVALID', description='This code is invalid.')
        pc2 = PermissionCode(name='Test2', code='abcde', description='Start Today', start_date=datetime.date.today())
        pc3 = PermissionCode(name='Test3', code='abcdef', description='Start Tomorrow', start_date=datetime.date.today() + datetime.timedelta(days=1))
        pc4 = PermissionCode(name='Test4', code='abcdefg', description='End Today', end_date=datetime.date.today())
        pc5 = PermissionCode(name='Test5', code='abcdefgh', description='End Tomorrow', end_date=datetime.date.today() + datetime.timedelta(days=1))
        pc6 = PermissionCode(name='Test6', code='abcdefghi', description='Both dates valid', start_date=datetime.date.today() - datetime.timedelta(days=1), end_date=datetime.date.today() + datetime.timedelta(days=1))
        pc6 = PermissionCode(name='Test7', code='abcdefghij', description='Both dates not valid', start_date=datetime.date.today() - datetime.timedelta(days=2), end_date=datetime.date.today() - datetime.timedelta(days=1))

        m1 = Message(name='BLACK_LIST_FAIL', text='You have been blocked from using this service. Contact us for more information.')
        m2 = Message(name='WHITE_LIST_FAIL', text='You are currently not permitted to use this service. Must complete course at: <Insert_Course_URL>')
        m3 = Message(name='NO_FILE_ATTACHED', text='There is not a file attached to this submission!')
        m4 = Message(name='PERMISSION_CODE_INVALID', text='The permission code you used does not exist. Please verify your code and submit again.')
        m5 = Message(name='PERMISSION_CODE_EXPIRED', text='The permission code you used is expired.')
        m6 = Message(name='PERMISSION_CODE_NOT_YET_ACTIVE', text='The permission code you used is not yet active.')
        m7 = Message(name='UNKNOWN_DOWNLOAD_ERROR', text='There was an issue downloading your file. Please verify that you submitted correctly and contact us if the problem persists.')
        m8 = Message(name='GOOGLE_DRIVE_403_ERROR', text='There was an issue downloading your file. Please verify that you have linked to the file and not the folder containing it. Also verify that you set the permissions to "everyone".')
        m9 = Message(name='GCODE_CHECK_FAIL', text='There is an issue with your submitted .gcode file. Please verify you used our printer profiles correctly.')
        m10 = Message(name='FINISH_TEXT_WITH_TAX', text='Your print is ready for pickup by the orange pillars in the ProtoSpace on the 2nd floor of the library whenever the library is open. A payment link will be generated and sent to you within approximately 48 hours. Thank you!')
        m11 = Message(name='FINISH_TEXT_TAX_EXEMPT', text='Your print is ready for pickup by the orange pillars in the ProtoSpace on the 2nd floor of the library whenever the library is open. Payment will be handled by your department or class. Thank you!')
        m12 = Message(name='PROFILE_OUT_OF_DATE', text='Please update your print profiles.')
        m13 = Message(name='NO_PRINTER_MODEL', text='We could not determine what printer this gcode was for! It is likely that your print profiles are out of date or you do not have them installed correctly.')
        m14 = Message(name='PRINT_CANCELLED', text='Print cancelled from admin panel.')
        m15 = Message(name='PRINT_QUEUED', text='Print queued from admin panel.')

        commit()

        gci1 = GcodeCheckItem(name="Profile", command=";", check_action=GcodeCheckActions.KEYWORD_CHECK.name, action_value='2', hard_fail=False, message=12, printer_model=1)
        gci2 = GcodeCheckItem(name="Remove M0", command="M0", check_action=GcodeCheckActions.REMOVE_COMMAND_ALL.name, action_value='', hard_fail=False)
        gci3 = GcodeCheckItem(name="Add M0", command="M0", check_action=GcodeCheckActions.ADD_COMMAND_AT_END.name, action_value='', hard_fail=False)
        gci4 = GcodeCheckItem(name="Remove beep", command="M300", check_action=GcodeCheckActions.REMOVE_COMMAND_ALL.name, action_value='', hard_fail=False)
        gci5 = GcodeCheckItem(name="Ensure home", command='G28', check_action=GcodeCheckActions.COMMAND_MUST_EXIST.name, action_value='', hard_fail=True)
        gci6 = GcodeCheckItem(name="Max nozzle temp", command='M104', check_action=GcodeCheckActions.COMMAND_PARAM_MAX.name, action_value='205', hard_fail=True)
        gci7 = GcodeCheckItem(name="Max nozzle temp", command='M109', check_action=GcodeCheckActions.COMMAND_PARAM_MAX.name, action_value='205', hard_fail=True)
        gci8 = GcodeCheckItem(name="Max bed temp", command='M140', check_action=GcodeCheckActions.COMMAND_PARAM_MAX.name, action_value='60', hard_fail=True)
        gci9 = GcodeCheckItem(name="Max bed temp", command='M190', check_action=GcodeCheckActions.COMMAND_PARAM_MAX.name, action_value='60', hard_fail=True)


def print_loop(clearTerminal):
    if clearTerminal:
        os.system('cls' if os.name == 'nt' else 'clear')
    print("Starting print loop.")
    jira.get_new_print_jobs()
    print_job_handler.process_new_jobs()
    octoprint.start_queued_jobs()
    octoprint.check_for_finished_jobs()
    print("Finished print loop.\n")
    # jira.askedForStatus()


def main():
    set_sql_debug(False)  # Shows the SQL queries pony is running in the console.
    db.bind(provider='sqlite', filename='octofarmJira_database.sqlite', create_db=True)  # Establish DB connection.
    db.generate_mapping(create_tables=True)
    # drop_and_create_db()

    with open("config_files/config.yml", "r") as yamlfile:
        config = yaml.load(yamlfile, Loader=yaml.FullLoader)

    print_loop(config['clearTerminal'])
    schedule.every(config['updateRate']).minutes.do(print_loop, config['clearTerminal'])

    while 1:
        schedule.run_pending()


if __name__ == "__main__":
    main()
