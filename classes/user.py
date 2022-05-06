from classes.printJob import *
import datetime


class User(db.Entity):
    print_jobs = Set(PrintJob)
    user_id = Required(str, unique=True)
    white_listed = Required(bool)
    black_listed = Required(bool)
    created_date = Required(datetime.datetime)

    @staticmethod
    @db_session
    def Get_White_Listed():
        query_result = select(u for u in User if u.white_listed is True)
        users = []
        for u in query_result:
            users.append(u)
        return users

    @staticmethod
    @db_session
    def Get_Black_Listed():
        query_result = select(u for u in User if u.black_listed is True)
        users = []
        for u in query_result:
            users.append(u)
        return users

    @staticmethod
    @db_session
    def Get_All():
        query_result = select(u for u in User)
        users = []
        for u in query_result:
            users.append(u)
        return users

    @staticmethod
    @db_session
    def Get_Or_Create(user_id):
        query_result = User.get(user_id=user_id)
        if query_result is None:
            query_result = User(user_id=user_id, white_listed=False, black_listed=False, created_date=datetime.datetime.now())
            commit()
        return query_result
