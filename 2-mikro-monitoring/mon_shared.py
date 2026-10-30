from dotenv import load_dotenv
import os
import requests
import logging
import yaml
import json


from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


from yaml.loader import SafeLoader
requests.packages.urllib3.disable_warnings() 
from datetime import timedelta
import re

UNITS = {"s":"seconds", "m":"minutes", "h":"hours", "d":"days", "w":"weeks"}

load_dotenv()
micro_user = os.environ.get("MIKRO_READ_USER")
micro_pass = os.environ.get("MIKRO_READ_PASSWORD")
debugmode = os.environ.get("DEBUGMODE")
influx_key = os.environ.get("INFLUX_API_KEY")
influx_url = os.environ.get("INFLUX_URL")
influx_org = os.environ.get("INFLUX_ORG")
influx_bucket = os.environ.get("INFLUX_BUCKET")


def sendToInflux(data):
    if data:
        with InfluxDBClient(url=influx_url, token=influx_key, org=influx_org) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            write_api.write(influx_bucket, influx_org, data)


#Convert time like 1w2h3s to seconds
def convert_to_seconds(s):
    return int(timedelta(**{
        UNITS.get(m.group('unit').lower(), 'seconds'): float(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)', s, flags=re.I)
    }).total_seconds())


def load_inventory(path):
    #Create list
    list=[]

    #Load all files config. Sorted to keep the order independent of the filesystem
    for filename in sorted(os.listdir(f"{path}")):
        #Skip non-inventory files (e.g. .DS_Store, editor temp files)
        if not filename.endswith((".yml", ".yaml")):
            continue
        #Open each file and load data
        with open(f"{path}/{filename}") as file:
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




