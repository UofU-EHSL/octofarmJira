# OctofarmJira
A layer between octofarm and jira so we can have a simple ticket to print system

## Octofarm setup
the docker compose file is now docker 3 and should work

$ docker swarm init
$ docker-compose up -d

## Running OctofarmJira

$ pip install -r requirements.yml
$ python3 flask/app.py

This will build the UI in a browser so go to 127.0.0.1:5000


# Example drop all tables and recreate DB:
db.generate_mapping(check_tables=False, create_tables=False)
db.drop_all_tables(with_all_data=True)
db.create_tables()

with db_session:
p1 = Printer(name='Prusa01', model=PrinterModel.PRUSA_MK3.name, ip='localhost:81', api_key='53148701F56E47368C7737DF546B1532', enabled=True)
p2 = Printer(name='Prusa02', model=PrinterModel.PRUSA_MK3.name, ip='localhost:82', api_key='2ECDDF5FCFF44C56A4E864AFC1ABABD9', enabled=True)
p3 = Printer(name='Prusa03', model=PrinterModel.PRUSA_MK3.name, ip='localhost:83', api_key='A004159B89CB4226BED7E66A442A76F6', enabled=True)
p4 = Printer(name='Prusa04', model=PrinterModel.PRUSA_MK3.name, ip='localhost:84', api_key='0E00C61D6C964722A0D39B3D2CD98DBA', enabled=True)
p5 = Printer(name='Prusa05', model=PrinterModel.PRUSA_MK3.name, ip='localhost:85', api_key='44D69C98F8B54EEA827988AFE667BA0A', enabled=True)
