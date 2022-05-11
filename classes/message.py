from classes.user import *


class Message(db.Entity):
    name = Required(str, unique=True)
    text = Required(str)
    print_job = Set(PrintJob)



    @staticmethod
    @db_session
    def Get_All():
        query_result = select(m for m in Message)
        messages = []
        for m in query_result:
            messages.append(m)
        return messages


    @staticmethod
    def Map_Request(message, form_data):
        """
        Maps request data to a message object.
        """
        message.name = form_data['name']
        message.text = form_data['text']

    @staticmethod
    @db_session
    def Add_From_Request(form_data):
        """
        Maps request data to a message object.
        """
        name = form_data['name']
        text = form_data['text']

        Message(name=name, text=text)
