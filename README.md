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
