import os
from dotenv import load_dotenv
import yaml
from yaml.loader import SafeLoader
import json
import requests
import logging

requests.packages.urllib3.disable_warnings() 


STOP_ON_ERROR = True
CSS_STYLE = "css1.j2"

load_dotenv()

pathconfig = os.environ.get("CONFIG")
pathcontrol = os.environ.get("CONTROLPATH")
micro_user = os.environ.get("MIKRO_USER")
micro_pass = os.environ.get("MIKRO_PASSWORD")


def loadControl():
    with open(f"{pathcontrol}/control.yml") as file:
            return yaml.load(file, Loader=SafeLoader)


def load_inventory():
    #Create list
    list=[]

    #Load all files config. Sorted to keep the order independent of the filesystem
    for filename in sorted(os.listdir(f"{pathconfig}/inventory")):
        #Skip non-inventory files (e.g. .DS_Store, editor temp files)
        if not filename.endswith((".yml", ".yaml")):
            continue
        #Open each file and load data
        with open(f"{pathconfig}/inventory/{filename}") as file:
            data = yaml.load(file, Loader=SafeLoader)
            #For each key in yml
            for key in data:
                for rule in data[key]:
                    rule['role']=key
                    list.append(rule)

    return list    



def getItem(device,resource):

    try:
        response = requests.get(f"https://{device['mgmt_int']}/rest{resource}", auth = (micro_user, micro_pass) , verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            return False

    except Exception as unknown_error:
            logging.error (f"Error getting device --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {unknown_error} \n\n")
            #errorStop() 
            return False


def postItem(device,resource,mydata):
    try:
        myheaders = {'content-type': 'application/json'}
        response = requests.post(f"https://{device['mgmt_int']}/rest{resource}", auth = (micro_user, micro_pass) , data=json.dumps(mydata), headers=myheaders, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error (f"Error on response to --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {response.json()} \n\n")
            return False

    except Exception as unknown_error:
            logging.error (f"Error getting device --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {unknown_error} \n\n")
            #errorStop() 
            return False


def patchItem(device,resource,mydata,id):
    try:
        myheaders = {'content-type': 'application/json'}
        response = requests.patch(f"https://{device['mgmt_int']}/rest{resource}/{id}", auth = (micro_user, micro_pass) , data=json.dumps(mydata), headers=myheaders, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error (f"Error on response to --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {response.json()} \n\n")
            return False

    except Exception as unknown_error:
            logging.error (f"Error getting device --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {unknown_error} \n\n")
            #errorStop() 
            return False

def putItem(device,resource,mydata):
    try:
        myheaders = {'content-type': 'application/json'}
        response = requests.put(f"https://{device['mgmt_int']}/rest{resource}", auth = (micro_user, micro_pass) , data=json.dumps(mydata), headers=myheaders, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error (f"Error on response to --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {response.json()} \n\n")
            return False

    except Exception as unknown_error:
            logging.error (f"Error getting device --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {unknown_error} \n\n")
            #errorStop() 
            return False

def deleteItem(device,resource,id):
    try:
        myheaders = {'content-type': 'application/json'}
        response = requests.delete(f"https://{device['mgmt_int']}/rest{resource}/{id}", auth = (micro_user, micro_pass) , headers=myheaders, verify=False)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error (f"Error on response to --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {response.json()} \n\n")
            return False

    except Exception as unknown_error:
            logging.error (f"Error getting device --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {unknown_error} \n\n")
            #errorStop() 
            return False