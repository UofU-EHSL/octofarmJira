# OctofarmJira
A layer between octofarm and jira so we can have a simple ticket to print system

## Octofarm setup
the docker compose file is now docker 3 and should work

$ docker swarm init
$ docker-compose up -d

## Running OctofarmJira
This will run forever if done right so we want to make sure it keeps going. I have a script that you run that will open the service in a 'screen' so that even if you close the terminal window it will still be running. I also plan on making another script to stop the service.
