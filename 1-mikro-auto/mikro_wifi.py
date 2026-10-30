import os
from yaml.loader import SafeLoader
import yaml


BRIDGE_VLAN_NAME = 'bridge-vlans'

#RAIUS_SECRET is the old (misspelled) name, still read so existing setups keep working
radius_password = os.environ.get("RADIUS_SECRET") or os.environ.get("RAIUS_SECRET")
pathconfig = os.environ.get("CONFIG")
path_secrets = os.environ.get("SECRETS")



def load_config(device,inventory):

    
    my_config=[]
    #Read secrets file
    with open(f'{path_secrets}/{device["wifi_profile"]}.yml') as file:
        secrets_wifi = yaml.load(file, Loader=SafeLoader)
        file.close()

    #Read secrets file
    with open(f'{path_secrets}/mac_addr.yml') as file:
        mac_acl = yaml.load(file, Loader=SafeLoader)
        file.close()
    if 'radius_core' in device.keys():
        if device['radius_core']:
            #core radius server
            #Get list of servers:
            core_radius_servers=[]
            for item in inventory:
                if item['role'] == "core":
                    core_radius_servers.append(item['name'])


            for server in core_radius_servers:
                mydict={}
                mydict['comment'] = f"radius_{server}"
                mydict['resource'] = '/radius'
                mydict['address'] = device[f"peer_from_{device['name']}_to_{server}"]
                mydict['secret'] = radius_password
                mydict['service'] = 'wireless' #Just wireless
                mydict['src_address'] = device[f"self_from_{device['name']}_to_{server}"]
                mydict['timeout'] = '5s'
                my_config.append(mydict)

        else:
            #local radius server
            for radius in secrets_wifi['radius_server']:
                mydict={}
                mydict['comment'] = radius['name']
                mydict['resource'] = '/radius'
                mydict['address'] = radius['ip']
                mydict['secret'] = radius_password
                mydict['service'] = radius['service']
                if radius['vlan_src'] == '0':
                    mydict['src_address'] = '127.0.0.1'
                else:
                    mydict['src_address'] = str(device['gatewayv4_list'][int(radius['vlan_src'])])
                mydict['timeout'] = radius['timeout']
                my_config.append(mydict)

    #wireless security profiles 1:1 config from yml adding supplicant_identity from device

    for item in secrets_wifi['sec_profile']:
        item['supplicant_identity']=device['name']
        item['resource']='/interface/wireless/security-profiles'
        my_config.append(item)       

    for item in secrets_wifi['int_wifi']:
        item['resource']='/interface/wireless'
        my_config.append(item)  

    #Add interfaces to list

    for item in secrets_wifi['int_wifi']:
        mydict={}
        mydict['comment'] = f"list_item_int_v_{item['name']}"
        mydict['resource'] = '/interface/list/member'
        mydict['interface'] = item['name']
        mydict['list'] = 'list_inside'
        my_config.append(mydict)

    for item in secrets_wifi['int_wifi']:    

        mydict={}
        mydict['resource'] = '/interface/bridge/port'
        mydict['comment'] = f"int_br_1SAFE_access_{item['name']}"
        mydict['interface'] = item['name']
        mydict['ingress_filtering'] = 'true'
        mydict['bridge'] = BRIDGE_VLAN_NAME 
        mydict['pvid'] = item['vlan_id']
        mydict['use_set'] = False
        my_config.append(mydict)

    #Add mac address to approved list
    for item in mac_acl:
        mydict={}
        mydict['resource'] = '/interface/wireless/access-list'
        mydict['comment'] = f"wifi_mac_{item}"
        mydict['mac_address'] = item.upper()
        mydict['use_set'] = False
        my_config.append(mydict)   

    return my_config
