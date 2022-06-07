from classes.keyword import *


class PrinterModel(db.Entity):
    """
    Used to group different kinds of printers. Can be used in gcodeCheckItems to target checks against certain printers.
    """
    name = Required(str)
    description = Optional(str)
    keyword = Optional("Keyword")
    printer = Set(Printer)
    gcode_check_items = Set('GcodeCheckItem')


    @staticmethod
    @db_session
    def Get_All():
        query_result = select(pm for pm in PrinterModel)
        printer_models = []
        for pm in query_result:
            printer_models.append(pm)
        return printer_models


    @staticmethod
    def Map_Request(printer_model, form_data):
        """
        Maps request data to a printer_model object.
        """
        printer_model.name = form_data['name']
        printer_model.description = form_data['description']
        printer_model.keyword = form_data['keyword']
