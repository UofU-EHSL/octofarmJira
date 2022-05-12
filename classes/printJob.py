from classes.printer import *
import datetime


class PrintJob(db.Entity):
    printed_on = Optional(Printer)
    """Printer this job was processed on."""
    permission_code = Optional('PermissionCode')
    job_id = Required(int, unique=True)
    """ID from the job submission system. We use Jira. This will be the unique ID generated by jira. Only digits in our case."""
    job_name = Optional(str, unique=True)
    """Optional custom job name from the submission system. We use PR-#### formatted names."""
    user = Required('User')
    print_started_date = Optional(datetime.datetime)
    print_finished_date = Optional(datetime.datetime)
    payment_link_generated_date = Optional(datetime.datetime)
    paid_date = Optional(datetime.datetime)
    payment_link = Optional(str)
    weight = Optional(float)
    cost = Optional(float)
    print_time = Optional(str)
    url_type = Optional(str)
    """UrlTypes Enum"""
    gcode_url = Optional(str)
    print_status = Required(str)
    """PrintStatus Enum"""
    payment_status = Optional(str)
    """PaymentStatus Enum"""
    failure_message = Optional('Message')
    """MessageNames Enum"""

    def Get_Name(self, job_name_only=False):
        if self.job_name and job_name_only:
            name = self.job_name
        elif self.job_name:
            name = self.job_name + '__' + str(self.job_id)
        else:
            name = str(self.job_id)
        return name

    def Get_File_Name(self):
        name = self.Get_Name()
        if self.url_type == UrlTypes.JIRA_ATTACHMENT.name:
            return "jiradownloads/" + name + ".gcode"
        elif self.url_type == UrlTypes.GOOGLE_DRIVE.name:
            return "drivedownloads/" + name + ".gcode"

    @staticmethod
    @db_session
    def Get_All_By_Status(print_status: PrintStatus):
        query_result = select(pj for pj in PrintJob if pj.print_status == print_status.name)
        print_jobs = []
        for p in query_result:
            print_jobs.append(p)
        return print_jobs

    def Generate_Start_Message(self):
        startTime = datetime.now().strftime("%I:%M" '%p')
        if startTime[0] == '0':
            startTime = startTime[1:]
        message = "Print was started at: " + startTime + "\n"
        message += "Estimated print weight: " + str(self.weight)
        message += "Estimated print time: " + str(self.print_time)
        message += "Estimated print cost: " + str(self.cost)
        return message

