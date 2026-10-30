import requests
import os
requests.packages.urllib3.disable_warnings() 
import logging
from dotenv import load_dotenv

load_dotenv()

micro_user = os.environ.get("MIKRO_READ_USER")
micro_pass = os.environ.get("MIKRO_READ_PASSWORD")


#------------API MIKROTIK

def getMikrotikApiItem(device,resource):

    try:
        response = requests.get(f"https://{device['mgmt_int']}/rest{resource}", auth = (micro_user, micro_pass) , verify=False, timeout=1 )
        if response.status_code == 200:
            return response.json()
        else:
            return False

    except Exception as unknown_error:
            logging.error (f"Error getting device --> {device['name']} IP --> {device['mgmt_int']} Resource--> {resource} \n\n {unknown_error} \n\n")
            #errorStop() 
            return False