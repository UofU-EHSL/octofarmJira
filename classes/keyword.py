from classes.user import *


class Keyword(db.Entity):
    """
    Used to associate something with a key in the gcode. Ex) Detect printer model or config bundle version. Used with gcodeCheckItems.
    """
    name = Required(str)
    description = Optional(str)
    value = Required(str)
    printer_model = Set('PrinterModel')


    @staticmethod
    @db_session
    def Get_All():
        query_result = select(k for k in Keyword)
        keyword = []
        for k in query_result:
            keyword.append(k)
        return keyword


    @staticmethod
    def Map_Request(keyword, form_data):
        """
        Maps request data to a keyword object.
        """
        keyword.name = form_data['name']
        keyword.description = form_data['description']
        keyword.value = form_data['value']


    @staticmethod
    @db_session
    def Add_From_Request(form_data):
        """
        Maps request data to a message object.
        """
        name = form_data['name']
        description = form_data['description']
        value = form_data['value']

        Keyword(name=name, description=description, value=value)
