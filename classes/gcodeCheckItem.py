from classes.printerModel import *


class GcodeCheckItem(db.Entity):
    """
    Checks gcode according to specific settings.
    """
    name = Required(str)
    description = Optional(str)
    command = Required(str)
    check_action = Required(str)
    action_value = Required(str)
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
        gcode_check_item.check_action = form_data['check_action']
        gcode_check_item.action_value = form_data['action_value']
        gcode_check_item.hard_fail = form_data['hard_fail']
        gcode_check_item.message = form_data['message']
        gcode_check_item.printer_model = form_data['printer_model']
