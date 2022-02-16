import os
import json

### These functions are to be used by the flask front end ###

def delete(fileName):
    os.remove(fileName)

def deleteall():
    for f in os.listdir("projects"):
        os.remove(os.path.join("projects", f))

def downloadall(fileName):
    os.system("zip -r " + fileName + ".zip projects")
    os.system("mv " + fileName + ".zip projects")
