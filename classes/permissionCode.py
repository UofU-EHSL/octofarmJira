from classes.printer import *
import datetime


class PermissionCode(db.Entity):
    code = Required(str, unique=True)
    """The actual code. Can be any string"""
    name = Required(str, unique=True)
    """Friendly name of the code."""
    description = Optional(str)
    """Optional description."""
    start_date = Optional(datetime.date)
    """Date the key beings being valid."""
    end_date = Optional(datetime.date)
    """Date the key stops being valid."""

    @staticmethod
    @db_session
    def Get_All():
        query_result = select(p for p in PermissionCode)
        codes = []
        for c in query_result:
            codes.append(c)
        return codes

    @staticmethod
    @db_session
    def Get_All_Active():
        now = datetime.date.today()
        query_result = select(c for c in PermissionCode if (c.start_date is None or c.start_date <= now) and (c.end_date is None or now <= c.end_date))
        codes = []
        for c in query_result:
            codes.append(c)
        return codes

    @staticmethod
    def Map_Request(code, form_data):
        """
        Maps request data to a permission code object.
        """
        code.name = form_data['name']
        code.code = form_data['code']
        code.description = form_data['description']
        try:
            code.start_date = datetime.datetime.fromisoformat(form_data['start_date'])
        except:
            code.start_date = None
        try:
            code.end_date = datetime.datetime.fromisoformat(form_data['end_date'])
        except:
            code.end_date = None

        if code.start_date and code.end_date and code.start_date > code.end_date:
            raise Exception

    @staticmethod
    @db_session
    def Add_From_Request(form_data):
        """
        Maps request data to a permission code object.
        """
        name = form_data['name']
        code = form_data['code']
        description = form_data['description']
        try:
            start_date = datetime.datetime.fromisoformat(form_data['start_date'])
        except:
            start_date = None
        try:
            end_date = datetime.datetime.fromisoformat(form_data['end_date'])
        except:
            end_date = None

        if start_date and end_date and start_date > end_date:
            raise Exception

        PermissionCode(name=name, code=code, description=description, start_date=start_date, end_date=end_date)