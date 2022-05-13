from pony.orm import *
from classes.enumDefinitions import *
import requests
import datetime

db = Database()


class Printer(db.Entity):
    name = Required(str, unique=True)
    """Human friendly name for printer. Example: 'Prusa01' """
    model = Required(str)
    """Model of the printer."""
    ip = Required(str, unique=True)
    """IP address to send print files to and query print status from."""
    api_key = Required(str)
    """Required API key to communicate with printer."""
    stream_ip = Optional(str)
    """Optional IP address for a streaming camera."""
    material_type = Optional(str)
    material_color = Optional(str)
    material_density = Required(float)
    enabled = Required(bool)
    print_jobs = Set('PrintJob')
    """Used to relate print jobs to this printer. Not an actual field, just a Pony ORM thing"""

    def Get_Job_Url(self):
        return "http://" + self.ip + "/api/job"

    def Get_Upload_Url(self):
        return "http://" + self.ip + "/api/files/{}".format("local")

    def Get_Job_Request(self):
        headers = {
            "Accept": "application/json",
            "Host": self.ip,
            "X-Api-Key": self.api_key
        }
        return requests.request(
            "GET",
            self.Get_Job_Url(),
            headers=headers
        )

    def Upload_Job(self, job):
        openFile = open(job.Get_File_Name(), 'rb')
        fle = {'file': openFile, 'filename': job.Get_Name()}
        payload = {'select': 'true', 'print': 'true'}
        header = {'X-Api-Key': self.api_key}
        return requests.post(self.Get_Upload_Url(), files=fle, data=payload, headers=header)

    @staticmethod
    @db_session
    def Get_All():
        query_result = select(p for p in Printer)
        printers = []
        for p in query_result:
            printers.append(p)
        return printers

    @staticmethod
    @db_session
    def Get_All_Enabled():
        query_result = select(p for p in Printer if p.enabled is True)
        printers = []
        for p in query_result:
            printers.append(p)
        return printers

    @staticmethod
    @db_session
    def Get_All_By_Type(printer_model: PrinterModel):
        query_result = select(p for p in Printer if p.model == printer_model.name)
        printers = []
        for p in query_result:
            printers.append(p)
        return printers

    @staticmethod
    @db_session
    def Get_All_Print_Counts(enabled_only=True):
        """Counts any print that started on the printer, including failed jobs. Sorted with the smallest number of jobs first."""
        if enabled_only:
            query_result = left_join((p, count(pj)) for p in Printer if p.enabled for pj in p.print_jobs)[:]
        else:
            query_result = left_join((p, count(pj)) for p in Printer for pj in p.print_jobs)[:]
        printers = []
        for p in query_result:
            printers.append(p)
        printers.sort(key=lambda x: x[1])  # The second element of the tuple is the number of print jobs associated.
        return printers

    @staticmethod
    def Map_Request(printer, form_data):
        """
        Maps request data to a printer object.
        """
        printer.name = form_data['name']
        printer.model = PrinterModel(int(form_data['model'])).name
        printer.ip = form_data['ip']
        printer.api_key = form_data['api_key']
        printer.stream_ip = form_data['stream_ip']
        printer.material_type = form_data['material_type']
        printer.material_color = form_data['material_color']
        try:
            printer.material_density = float(form_data['material_density'])
        except:
            printer.material_density = None
        printer.enabled = form_data['enabled'] == 'true'

    @staticmethod
    @db_session
    def Add_From_Request(form_data):
        """
        Maps request data to a printer object.
        """
        name = form_data['name']
        model = PrinterModel(int(form_data['model'])).name
        ip = form_data['ip']
        api_key = form_data['api_key']
        stream_ip = form_data['stream_ip']
        material_type = form_data['material_type']
        material_color = form_data['material_color']
        try:
            material_density = float(form_data['material_density'])
        except:
            material_density = None
        enabled = form_data['enabled'] == 'true'

        Printer(name=name, model=model, ip=ip, api_key=api_key, stream_ip=stream_ip, material_type=material_type, material_color=material_color, material_density=material_density, enabled=enabled)
