from classes.message import *
import datetime


class PrintJob(db.Entity):
    printer_model = Optional('PrinterModel')
    printed_on = Optional(Printer)
    """Printer this job was processed on."""
    permission_code = Optional('PermissionCode')
    job_id = Required(int, unique=True)
    """ID from the job submission system. We use Jira. This will be the unique ID generated by jira. Only digits in our case."""
    job_name = Optional(str, unique=True)
    """Optional custom job name from the submission system. We use PR-#### formatted names."""
    user = Required('User')
    job_created_date = Optional(datetime.datetime)
    print_started_date = Optional(datetime.datetime)
    print_finished_date = Optional(datetime.datetime)
    payment_link_generated_date = Optional(datetime.datetime)
    paid_date = Optional(datetime.datetime)
    payment_link = Optional(str)
    weight = Optional(float)
    """In grams"""
    cost = Optional(float)
    print_time = Optional(int)
    """In seconds"""
    url_type = Optional(str)
    """UrlTypes Enum"""
    gcode_url = Optional(str)
    print_status = Required(str)
    """PrintStatus Enum"""
    payment_status = Optional(str)
    """PaymentStatus Enum"""
    failure_message = Optional(Message)
    """MessageNames Enum"""

    def Get_Name(self, job_name_only=False):
        if self.job_name and job_name_only:
            name = self.job_name
        elif self.job_name:
            name = self.job_name + '_' + str(self.job_id)
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
    def Get_All_By_Status(print_status: PrintStatus, serialize=False):
        query_result = select(pj for pj in PrintJob if pj.print_status == print_status.name)
        print_jobs = []
        for p in query_result:
            print_jobs.append(p)
        if serialize:
            return PrintJob.Serialize_Jobs(print_jobs)
        return print_jobs

    @staticmethod
    def Serialize_Jobs(jobs):
        result = []
        for j in jobs:
            result.append(j.To_Dict())
        return json.dumps(result)

    def Generate_Start_Message(self):
        startTime = datetime.datetime.now().strftime("%I:%M" '%p')
        if startTime[0] == '0':
            startTime = startTime[1:]
        text = "Print was started at: " + startTime + "\n"
        text += "Estimated print weight: " + str(self.weight) + "g\n"
        text += "Estimated print time: " + str(datetime.timedelta(seconds=self.print_time)) + "\n"
        text += "Estimated print cost: " + "${:,.2f}".format(self.cost)
        return text

    @db_session
    def Generate_Finish_Message(self):
        finishTime = datetime.datetime.now().strftime("%I:%M" '%p')
        if finishTime[0] == '0':
            finishTime = finishTime[1:]
        text = "{color:#00875A}Print completed successfully!{color}\n\n"
        text += "Print harvested at: " + finishTime + "\n"
        text += "Actual filament used: " + str(self.weight) + "g\n"
        text += "Actual print cost: " + "${:,.2f}".format(self.cost) + "\n\n"

        if self.permission_code:
            message = Message.get(name=MessageNames.FINISH_TEXT_TAX_EXEMPT.name)
            if message:
                text += message.text
        else:
            message = Message.get(name=MessageNames.FINISH_TEXT_WITH_TAX.name)
            if message:
                text += message.text

        return text

    def To_Dict(self):
        result = {'job_id': self.job_id, 'job_name': self.job_name, 'job_created_date': self.job_created_date, 'printer_model': self.printer_model.name, 'auto_start': self.printer_model.auto_start_prints, 'print_time': self.print_time}
        return result
