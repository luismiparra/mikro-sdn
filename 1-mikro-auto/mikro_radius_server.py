import os
from yaml.loader import SafeLoader
import yaml

pathconfig = os.environ.get("CONFIG")
path_secrets = os.environ.get("SECRETS")
#Certificate (already imported on the router) the user manager uses. Empty: radius.<device domain>.crt
radius_certificate = os.environ.get("RADIUS_CERTIFICATE")

def load_config(device):

    my_config=[]

    #Read secrets file
    with open(f'{path_secrets}/radius_users.yml') as file:
        users = yaml.load(file, Loader=SafeLoader)
        file.close()

    with open(f'{path_secrets}/radius_routers.yml') as file:
        routers = yaml.load(file, Loader=SafeLoader)
        file.close()

    #user mgmt config
    mydict={}
    mydict['resource'] = '/user-manager'
    mydict['certificate'] = radius_certificate or f"radius.{device['domain']}.crt"
    mydict['enabled'] = 'yes'
    mydict['use_set'] = True
    my_config.append(mydict)

    #add users

    for user in users:
        mydict={}
        mydict['resource'] = '/user-manager/user'
        mydict['comment'] = f"radius_user_{user['user']}"
        mydict['name'] = user['user']
        mydict['password'] = user['password']
        mydict['shared_users'] = user['shared_users']
        mydict['use_set'] = False
        my_config.append(mydict)

    #add routers

    for router in routers:
        mydict={}
        mydict['resource'] = '/user-manager/router'
        mydict['comment'] = f"radius_router_{router['name']}_{router['ip']}"
        mydict['address'] = router['ip']
        mydict['name'] = router['name']
        mydict['shared_secret'] = router['secret']
        mydict['use_set'] = False
        my_config.append(mydict)

    return my_config
