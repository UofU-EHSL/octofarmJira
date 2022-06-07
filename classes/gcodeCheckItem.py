from classes.printerModel import *


class GcodeCheckItem(db.Entity):
    """
    Checks gcode according to specific settings.
    """
    name = Required(str)
    description = Optional(str)
    command = Required(str)
    check_action = Required(str)
    action_value = Optional(str)
    hard_fail = Required(bool)
    message = Optional(Message)
    printer_model = Optional(PrinterModel)


    @staticmethod
    @db_session
    def Get_All():
        query_result = select(gci for gci in GcodeCheckItem)
        gcode_check_items = []
        for gci in query_result:
            gcode_check_items.append(gci)
        return gcode_check_items


    @staticmethod
    def Map_Request(gcode_check_item, form_data):
        """
        Maps request data to a gcode_check_item object.
        """
        gcode_check_item.name = form_data['name']
        gcode_check_item.description = form_data['description']
        gcode_check_item.command = form_data['command']
        gcode_check_item.check_action = GcodeCheckActions(int(form_data['check_action'])).name
        gcode_check_item.action_value = form_data['action_value']
        gcode_check_item.hard_fail = form_data['hard_fail'] == 'true'
        if form_data['message']:
            gcode_check_item.message = int(form_data['message'])
        else:
            gcode_check_item.message = None
        gcode_check_item.printer_model = int(form_data['printer_model'])


    @staticmethod
    @db_session
    def Add_From_Request(form_data):
        """
        Maps request data to a gcode check item.
        """
        name = form_data['name']
        description = form_data['description']
        command = form_data['command']
        action_value = form_data['action_value']
        check_action = GcodeCheckActions(int(form_data['check_action'])).name
        printer_model = int(form_data['printer_model'])
        if form_data['message']:
            message = int(form_data['message'])
        else:
            message = None
        hard_fail = form_data['hard_fail'] == 'true'

        GcodeCheckItem(name=name, description=description, command=command, action_value=action_value, check_action=check_action, printer_model=printer_model, message=message, hard_fail=hard_fail)
