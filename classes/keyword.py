from classes.user import *
import datetime


class Keyword(db.Entity):
    """
    Used to associate something with a key in the gcode. Ex) Detect printer model or config bundle version. Used with gcodeCheckItems.
    """
    name = Required(str)
    description = Required(str)
    value = Required(str)
    created_date = Required(datetime.datetime)


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
        keyword.name = form_data['description']
        keyword.name = form_data['value']
