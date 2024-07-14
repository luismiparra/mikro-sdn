import logging
import mikro_shared
import os
from dotenv import load_dotenv
from yaml.loader import SafeLoader
import yaml
import wgconfig.wgexec as wgexec
import json
import mikro_docs
import ipaddress

myconfig = os.environ.get("CONFIG")
pathsecrets = os.environ.get("SECRETS")

#1)define
core_devices = []
edge_devices = []
external_devices = []
#Create list of global config
d_config = {}
externalconf = {}
empty_secrets = {}

PERSISTENT_KEEPALIVE="10s"
LOOPBACK_IP_PREFIX = '10.0.0'

def loadWan(inventory):

    global externalconf

    #Read secrets file
    with open(f'{pathsecrets}/secrets.json') as file:
        secrets = json.load(file)
        file.close()

    for device in inventory:
        if device['enabled']:
            if device['role'] == "core":
                core_devices.append(device)
                d_config[device['name']]=[]
            if device['role'] == "edge" or device['role'] == "external_edge" :
                edge_devices.append(device)
                d_config[device['name']]=[]
            #We also add external to externalconf
            if device['role'] == "external_edge":
                external_devices.append(device)
                externalconf[device['name']]={}

#--------------------MAIN VRF VPN

    #CORE TO CORE
    for core1 in core_devices:
        for core2 in core_devices:
            #Check if not the same device
            if core1['name'] != core2['name']:
                secrets = createConn(core1,core2,"wan",secrets,"main")

    #EDGE TO CORE
    for edge in edge_devices:
        for core in core_devices:
            secrets = createConn(edge,core,"edge",secrets,"main")

    #Save secrets file
    with open (f'{pathsecrets}/secrets.json', 'w') as file:
        secrets = json.dump(secrets, file)
        file.close()

    #Save external file
    with open (f'{pathsecrets}/external/external.yml', 'w') as file:
        yaml.dump(externalconf, file)
        file.close()
    with open (f'{pathsecrets}/external/external.json', 'w') as file:
        json.dump(externalconf, file)
    file.close()

    #Create external config files
    mikro_docs.externalFiles(externalconf)

    return d_config

def createConn(item1,item2,resource,secrets,role):

    #identify devices help
    #where  item1 = edge  or core1
    #       item2 = core2


    global externalconf
    
    
    candidate = mikro_shared.connectionName(f"{item1['name']}_{role}",f"{item2['name']}_{role}")

    #Create temporal connections key just on execution
    if not 'connections' in item1.keys():
        item1['connections'] = []
    if not 'connections' in item2.keys():
        item2['connections'] = []

    #Check if connection already created
    if not candidate in item1['connections']:
        #Start creating connection
        item1['connections'].append(candidate)
        item2['connections'].append(candidate)

        #Create wireguard
        #If secret empty create list
        if secrets == None:
            secrets = {}

        #CHECK IF KEYS EXIST
        if not candidate in secrets:
            #Creating key
            item1_keys = wgexec.generate_keypair()
            item2_keys = wgexec.generate_keypair()
            preshared_key = wgexec.generate_presharedkey()
            secrets [candidate] = {f"{item1['name']}_{role}_private":item1_keys[0], f"{item1['name']}_{role}_public":item1_keys[1], f"{item2['name']}_{role}_private":item2_keys[0], f"{item2['name']}_{role}_public":item2_keys[1] , 'preshared':preshared_key }

        if not 'conn_number' in item1.keys():
            item1['conn_number'] = 0
        else:
            item1['conn_number'] +=1

        if not 'conn_number' in item2.keys():
            item2['conn_number'] = 0
        else:
            item2['conn_number'] +=1

        #logging.debug(f"wan generation conn {item1['name']}_{role} -> {item1['conn_number']}    {item2['name']}_{role} -> {item2['conn_number']}")

        #----------prepare external object with candidate
        if item1['role'] == 'external_edge':
            externalconf[item1['name']][candidate]={'connection':candidate}

        #-------------------------------------WIREGUARD

        #CREATE INT LIST WIREGUARD
        mydict={}
        mydict['comment'] = f"int_list_wireguard_{role}"
        mydict['resource'] = '/interface/list'
        mydict['include'] = 'static'
        mydict['name'] = f'list_wireguard_{role}'
        mydict['use_set'] = False

        if item1['role'] == 'external_edge':
            pass
        else:
            d_config[item1['name']].append(mydict)


        mydict={}
        mydict['comment'] = f"int_list_wireguard_{role}"
        mydict['resource'] = '/interface/list'
        mydict['include'] = 'static'
        mydict['name'] = f'list_wireguard_{role}'
        mydict['use_set'] = False
        d_config[item2['name']].append(mydict)

        #CREATE INT LIST WIREGUARD EXTERNAL
        mydict={}
        mydict['comment'] = f"int_list_external_wireguard_{role}"
        mydict['resource'] = '/interface/list'
        mydict['include'] = 'static'
        mydict['name'] = f'list_external_wireguard_{role}'
        mydict['use_set'] = False
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)


        mydict={}
        mydict['comment'] = f"int_list_external_wireguard_{role}"
        mydict['resource'] = '/interface/list'
        mydict['include'] = 'static'
        mydict['name'] = f'list_external_wireguard_{role}'
        mydict['use_set'] = False
        d_config[item2['name']].append(mydict)


        #INTERFACE WIREGUARD
        #ITEM 1
        mydict={}
        mydict['comment'] = f"int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['resource'] = '/interface/wireguard'
        mydict['mtu'] = item1['wg_mtu']
        mydict['name'] = f"int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['listen_port'] = str(51820+item1['conn_number'])
        mydict['private_key'] = secrets[candidate][f"{item1['name']}_{role}_private"]
        mydict['use_set'] = False
        if item1['role'] == 'external_edge':
            externalconf[item1['name']][candidate]['wireguard_interface'] = mydict 
        else:
            d_config[item1['name']].append(mydict)


        #ITEM 2
        mydict={}
        mydict['comment'] = f"int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['resource'] = '/interface/wireguard'
        mydict['mtu'] = item2['wg_mtu']
        mydict['name'] = f"int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"

        if item1['role'] == 'external_edge' and 'external_wg_main_port' in item1.keys():
            mydict['listen_port'] = str(item1['external_wg_main_port'])
        else:
            mydict['listen_port'] = str(51820+item2['conn_number'])

        mydict['private_key'] = secrets[candidate][f"{item2['name']}_{role}_private"]
        mydict['use_set'] = False
        d_config[item2['name']].append(mydict)


        #--------------ADD FIREWALL RULES TO ALLOW INBOUND FROM THIS WIREGUARD INTERFACE.
    
        #ITEM1: 
        #ipv4
        if item1['rp_external']:
            pass
        else:
            mydict={}
            mydict['comment'] = f"fw_v4_forward_wgmain_in_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ip/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            if item2['role'] == 'external_edge':
                pass
                
            else:
                d_config[item2['name']].append(mydict)
            #ipv6
            mydict={}
            mydict['comment'] = f"fw_v6_forward_wgmain_in_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ipv6/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            if item2['role'] == 'external_edge':
                pass
                
            else:
                d_config[item2['name']].append(mydict)

        #ITEM2: 
        if item2['rp_external']:
            pass
        else:
            #ipv4
            mydict={}
            mydict['comment'] = f"fw_v4_forward_wgmain_in_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ip/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            if item1['role'] == 'external_edge':
                pass
                
            else:
                d_config[item1['name']].append(mydict)

            #ipv6
            mydict={}
            mydict['comment'] = f"fw_v6_forward_wgmain_in_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ipv6/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            if item1['role'] == 'external_edge':
                pass
                
            else:
                d_config[item1['name']].append(mydict)


        if item2['rp_external']:
            #ITEM1 add to list external
            mydict={}
            mydict['comment'] = f"list_external_item_int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['resource'] = '/interface/list/member'
            mydict['interface'] = f"int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['list'] = f'list_external_wireguard_{role}'
            mydict['use_set'] = False
            if item1['role'] == 'external_edge':
                pass
                
            else:
                d_config[item1['name']].append(mydict)

        else:
            #ITEM1 add to list
            mydict={}
            mydict['comment'] = f"list_item_int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['resource'] = '/interface/list/member'
            mydict['interface'] = f"int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['list'] = f'list_wireguard_{role}'
            mydict['use_set'] = False
            if item1['role'] == 'external_edge':
                pass
                
            else:
                d_config[item1['name']].append(mydict)

        if item1['rp_external']:    
            #ITEM2 add to listexternal
            mydict={}
            mydict['comment'] = f"list_external_item_int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['resource'] = '/interface/list/member'
            mydict['interface'] = f"int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['list'] = f'list_external_wireguard_{role}'
            mydict['use_set'] = False
            d_config[item2['name']].append(mydict)
        else: 
            #ITEM2 add to list
            mydict={}
            mydict['comment'] = f"list_item_int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['resource'] = '/interface/list/member'
            mydict['interface'] = f"int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['list'] = f'list_wireguard_{role}'
            mydict['use_set'] = False
            d_config[item2['name']].append(mydict)

        #ITEM 1 FW external
        #ipv4
        mydict={}
        mydict['comment'] = f"fw_in_wireguard_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = str(51820+item1['conn_number'])
        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ipv6
        mydict={}
        mydict['comment'] = f"fwv6_in_wireguard_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = str(51820+item1['conn_number'])
        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)       

        #ITEM 2 FW external
        #ipv4
        mydict={}
        mydict['comment'] = f"fw_in_wireguard_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'

        if item1['role'] == 'external_edge' and 'external_wg_main_port' in item1.keys():
            mydict['dst_port'] = str(item1['external_wg_main_port'])
        else:
            mydict['dst_port'] = str(51820+item2['conn_number'])

        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[item2['name']].append(mydict)     

        #ipv6
        mydict={}
        mydict['comment'] = f"fwv6_in_wireguard_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'

        if item1['role'] == 'external_edge' and 'external_wg_main_port' in item1.keys():
            mydict['dst_port'] = str(item1['external_wg_main_port'])
        else:
            mydict['dst_port'] = str(51820+item2['conn_number'])

        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[item2['name']].append(mydict)   

        #INTERFACE WIREGUARD PEER
        #ITEM 1
        mydict={}
        mydict['name'] = f"int_wg_peer_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['comment'] = f"int_wg_peer_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['resource'] = '/interface/wireguard/peers'
        mydict['allowed_address'] = '0.0.0.0/0,::/0'
        mydict['endpoint_address'] = item2['external_endpoint']
        #mydict['is_responder'] = 'no'

        if item1['role'] == 'external_edge' and 'external_wg_main_port' in item1.keys():
            mydict['endpoint_port'] = str(item1['external_wg_main_port'])
        else:
            mydict['endpoint_port'] = str(51820+item2['conn_number'])

        mydict['interface'] = f"int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['preshared_key'] = secrets[candidate]['preshared']
        mydict['public_key'] = secrets[candidate][f"{item2['name']}_{role}_public"]
        mydict['persistent_keepalive'] = PERSISTENT_KEEPALIVE
        mydict['use_set'] = False
        if item1['role'] == 'external_edge':
            externalconf[item1['name']][candidate]['wireguard_peer'] = mydict
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2
        mydict={}
        mydict['name'] = f"int_wg_peer_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['comment'] = f"int_wg_peer_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['resource'] = '/interface/wireguard/peers'
        mydict['allowed_address'] = '0.0.0.0/0,::/0'
        
        #ENDPOINT JUST TO CORE
        if item1['role'] == 'core':
            mydict['endpoint_address'] = item1['external_endpoint']
            #mydict['is_responder'] = 'no'
        else:
            mydict['is_responder'] = 'true'

        mydict['endpoint_port'] = str(51820+item1['conn_number'])
        mydict['interface'] = f"int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['preshared_key'] = secrets[candidate]['preshared']
        mydict['public_key'] = secrets[candidate][f"{item1['name']}_{role}_public"]
        mydict['persistent_keepalive'] = PERSISTENT_KEEPALIVE
        mydict['use_set'] = False
        d_config[item2['name']].append(mydict)

        #WIREGUARD PEERS CHANGE PORT SCRIPT 
        #ITEM1
        if item1['role'] == 'edge':
            mydict={}
            mydict['comment'] = f"script_PORT_RANDOM_wg_peer_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['resource'] = '/system/scheduler'
            mydict['name'] = f"script_PORT_RANDOM_wg_peer_{item1['name']}_{role}_to_{item2['name']}_{role}"
            mydict['use_set'] = False
            mydict['policy'] = "reboot,read,write,test,password,sniff,sensitive,romon"
            mydict['start-date'] = "2022-01-01"
            mydict['start-time'] = "00:00:00"
            mydict['interval'] = "6h"

            #Check if site id can be from 1 to 255. Here we just asign ports all between 11100 and 12950
            if item2['site_id'] < 10:
                start_number = item2['site_id'] * 1000 + 100 + 10000
                end_number = item2['site_id'] * 1000 + 200 + 10000 
            else:
                if item2['site_id'] < 100:
                    start_number = item2['site_id'] * 100 + 200 + 10000
                    end_number = item2['site_id'] * 100 + 300 + 10000
                else:
                    if item2['site_id'] < 255:
                        start_number = item2['site_id'] * 10 + 300 + 10000
                        end_number = item2['site_id'] * 10 + 400 + 10000

            mydict['on-event'] = f"/interface wireguard set int_w_{item1['name']}_{role}_to_{item2['name']}_{role} listen-port=[:rndnum from={start_number} to={end_number}]"
            mydict['disabled'] = "false"
            d_config[item1['name']].append(mydict)

        #WIREGUARD PEERS DDNS SCRIPT
        #ITEM1
        mydict={}
        mydict['comment'] = f"script_DDNS_wg_peer_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['resource'] = '/system/scheduler'
        mydict['name'] = f"script_DDNS_wg_peer_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['use_set'] = False
        mydict['policy'] = "reboot,read,write,test,password,sniff,sensitive,romon"
        mydict['start-date'] = "2022-01-01"
        mydict['start-time'] = "00:00:00"
        mydict['interval'] = "30m"
        mydict['on-event'] = f"\
:local wgPeerComment\r\
\n:local wgPeerDns\r\
\n\r\
\n:set wgPeerComment \"int_wg_peer_{item1['name']}_{role}_to_{item2['name']}_{role}\"\r\
\n:set wgPeerDns \"{item2['external_endpoint']}\"\r\
\n\r\
\n\r\
\n:if ([interface wireguard peers get number=[find comment=\"$wgPeerComment\"] value-name=endpoint-address] != [resolve $wgPeerDns]) do={{\r\
\n  interface wireguard peers set number=[find comment=\"$wgPeerComment\"] endpoint-address=[/resolve $wgPeerDns]\r\
\n}}\r\
\n\r\
\n\r\
\n"
        #Just apply ddns if not fixed ip on the config
        if item2['external_ddns']:
            d_config[item1['name']].append(mydict)

        #ITEM2
        #Just if peer is core
        if item1['role'] == 'core':
            mydict={}
            mydict['comment'] = f"script_DDNS_wg_peer_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['resource'] = '/system/scheduler'
            mydict['name'] = f"script_DDNS_wg_peer_{item2['name']}_{role}_to_{item1['name']}_{role}"
            mydict['use_set'] = False
            mydict['policy'] = "reboot,read,write,test,password,sniff,sensitive,romon"
            mydict['start-date'] = "2022-01-01"
            mydict['start-time'] = "00:00:00"
            mydict['interval'] = "30m"
            mydict['on-event'] = f"\
:local wgPeerComment\r\
\n:local wgPeerDns\r\
\n\r\
\n:set wgPeerComment \"int_wg_peer_{item2['name']}_{role}_to_{item1['name']}_{role}\"\r\
\n:set wgPeerDns \"{item1['external_endpoint']}\"\r\
\n\r\
\n\r\
\n:if ([interface wireguard peers get number=[find comment=\"$wgPeerComment\"] value-name=endpoint-address] != [resolve $wgPeerDns]) do={{\r\
\n  interface wireguard peers set number=[find comment=\"$wgPeerComment\"] endpoint-address=[/resolve $wgPeerDns]\r\
\n}}\r\
\n\r\
\n\r\
\n"
            #Just apply ddns if not fixed ip on the config
            if item1['external_ddns']:
                d_config[item2['name']].append(mydict)

        #ipv4 address
        if resource == "wan":
            subnet_transit_var_v4 = "subnet_transit_core_v4"
            subnet_transit_var_v6 = "subnet_transit_core_v6"
        if resource == "edge" or "external_edge":
            subnet_transit_var_v4 = "subnet_transitv4"
            subnet_transit_var_v6 = "subnet_transitv6"

        
        #ITEM 1
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ip/address'
        mydict['interface'] = f"int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['comment'] = f"ip_wg_{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}_{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}"
        mydict['address'] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}"
        if item1['role'] == 'external_edge':
            externalconf[item1['name']][candidate]['ip_address'] = mydict
        else:
            d_config[item1['name']].append(mydict)
            #Document for external use the ip of the peer
            item1[f"self_from_{item1['name']}_to_{item2['name']}"] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}"
            item1[f"peer_from_{item1['name']}_to_{item2['name']}"] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}"


        #ITEM 2
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ip/address'
        mydict['interface'] = f"int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['comment'] = f"ip_wg_{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}_{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}"
        mydict['address'] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}"
        d_config[item2['name']].append(mydict)
        #Document for external use the ip of the peer.
        item2[f"self_from_{item2['name']}_to_{item1['name']}"] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}"
        item2[f"peer_from_{item2['name']}_to_{item1['name']}"] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}"

        #Netwatch monitoring for each peer
        #ITEM 1

        mydict={}
        mydict['comment'] = f"netwatch_wg_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['resource'] = '/tool/netwatch'
        mydict['host'] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}"
        mydict['interval'] = "30s"
        mydict['type'] = "icmp"
        d_config[item1['name']].append(mydict)       

        #ITEM 2

        mydict={}
        mydict['comment'] = f"netwatch_wg_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['resource'] = '/tool/netwatch'
        mydict['host'] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}"
        mydict['interval'] = "30s"
        mydict['type'] = "icmp"
        d_config[item2['name']].append(mydict)

        #IPV4 CHECK IF CORE INTERNET DEFAULT TRANSIT
        #item1
        if item1['role'] == 'core' and item2['role'] == 'core':
            if item2['core_internet_transit']:
                item1[f'internet_vpn_ip'] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}"

            if item1['core_internet_transit']:
                item2[f'internet_vpn_ip'] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}"            

        if item1['role'] == 'edge' and item2['role'] == 'core':
            if item2['core_internet_transit']:
                item1[f'internet_vpn_ip'] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}"         

        #IPV4 CORE_TRANSIT_RULES Add the information to transit to all cores that is then used in other services.
        if not 'core_transits' in item1.keys():
            item1['core_transits']=[]
        if not 'core_transits' in item2.keys():
            item2['core_transits']=[]

        if item1['role'] == 'core' and item2['role'] == 'core':
            item1[f'core_transits'].append( { 'transit_device' : item2['name'] , 'ipv4' : f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}"})

            item2[f'core_transits'].append( { 'transit_device' : item1['name'] , 'ipv4' : f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}"})            

        if item1['role'] == 'edge' and item2['role'] == 'core' :
            item1[f'core_transits'].append( { 'transit_device' : item2['name'] , 'ipv4' : f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}"})

        #ipv6 address
        #ITEM 1
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ipv6/address'
        mydict['interface'] = f"int_w_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['comment'] = f"ip_wg_{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip1'])}_{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}"
        mydict['address'] = f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}"
        if item1['role'] == 'external_edge':
            externalconf[item1['name']][candidate]['ipv6_address'] = mydict
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ipv6/address'
        mydict['interface'] = f"int_w_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['comment'] = f"ip_wg_{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip2'])}_{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}"
        mydict['address'] = f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}"
        d_config[item2['name']].append(mydict)

        #ITEM 1 FW internal bgp ipv4
        mydict={}
        mydict['comment'] = f"fw_in_bgp_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '179'
        mydict['protocol'] = 'tcp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2 FW internal bgp ipv4
        mydict={}
        mydict['comment'] = f"fw_in_bgp_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '179'
        mydict['protocol'] = 'tcp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[item2['name']].append(mydict)    

        #ITEM 1 FW internal bgp ipv6
        mydict={}
        mydict['comment'] = f"fw_in_bgpv6_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '179'
        mydict['protocol'] = 'tcp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2 FW internal bgp ipv6
        mydict={}
        mydict['comment'] = f"fw_in_bgpv6_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '179'
        mydict['protocol'] = 'tcp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[item2['name']].append(mydict)  

        #ITEM 1 FW internal bfd ipv4
        mydict={}
        mydict['comment'] = f"fw_in_bfd_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '3784'
        mydict['protocol'] = 'udp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2 FW internal bfd ipv4
        mydict={}
        mydict['comment'] = f"fw_in_bfd_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '3784'
        mydict['protocol'] = 'udp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v4][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[item2['name']].append(mydict)    

        #ITEM 1 FW internal bfd ipv6
        mydict={}
        mydict['comment'] = f"fw_in_bfdv6_{item1['name']}_{role}_to_{item2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '3784'
        mydict['protocol'] = 'udp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2 FW internal bfd ipv6
        mydict={}
        mydict['comment'] = f"fw_in_bfdv6_{item2['name']}_{role}_to_{item1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '3784'
        mydict['protocol'] = 'udp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip2'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip1'])}/{str(item1[subnet_transit_var_v6][item1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[item2['name']].append(mydict)

        #---------------------------------route filter subnets rule
        #routing filter ipv4
        #EXTERNAL EDGE 

        #ITEM 1 add external subnet
        if item1['role'] == 'external_edge':
            mydict={}
            mydict['use_set'] = False
            mydict['resource'] = '/routing/filter/rule'
            mydict['comment'] = f"filter_external_v4_{item1['location']}"
            mydict['chain'] = f"filter_external_v4_{item1['location']}"
            mydict['disabled'] = 'false'
            mydict['rule'] = f"if (dst in {item1['allow_out_prefix_v4']} || dst in {LOOPBACK_IP_PREFIX}.{item1['site_id']}/32 ) {{accept}}"
            d_config[item2['name']].append(mydict)

        if item1['role'] == 'external_edge':
            mydict={}
            mydict['use_set'] = False
            mydict['resource'] = '/routing/filter/rule'
            mydict['comment'] = f"filter_external_v6_{item1['location']}"
            mydict['chain'] = f"filter_external_v6_{item1['location']}"
            mydict['disabled'] = 'false'
            mydict['rule'] = f"if (dst in {item1['allow_out_prefix_v6']}) {{accept}}"
            d_config[item2['name']].append(mydict)

        #ITEM 1a filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_{item2['location']}"
        mydict['chain'] = f"filter_v4_{item2['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {item2['subnetv4']} || dst in {LOOPBACK_IP_PREFIX}.{item2['site_id']}/32) {{accept}}"
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2a filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_{item1['location']}"
        mydict['chain'] = f"filter_v4_{item1['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {item1['subnetv4']} || dst in {LOOPBACK_IP_PREFIX}.{item1['site_id']}/32) {{accept}}"
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 1b filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_{item2['location']}"
        mydict['chain'] = f"filter_v4_{item2['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {item2['subnetv4']} || dst in {LOOPBACK_IP_PREFIX}.{item2['site_id']}/32) {{accept}}"
        d_config[item2['name']].append(mydict)

        #ITEM 2b filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_{item1['location']}"
        mydict['chain'] = f"filter_v4_{item1['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {item1['subnetv4']} || dst in {LOOPBACK_IP_PREFIX}.{item1['site_id']}/32) {{accept}}"
        d_config[item2['name']].append(mydict)

        #routing filter ipv4
        #ITEM 1 filter any
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_any"
        mydict['chain'] = f"filter_v4_any"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in 10.0.0.0/8) {{set bgp-path-peer-prepend 2; accept}}"
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2 filter any
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_any"
        mydict['chain'] = f"filter_v4_any"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in 10.0.0.0/8) {{set bgp-path-peer-prepend 2; accept}}"
        d_config[item2['name']].append(mydict)

        #ITEM 1 filter any priority
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_any_priority"
        mydict['chain'] = f"filter_v4_any_priority"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in 10.0.0.0/8) {{set bgp-path-peer-prepend 1; accept}}"
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2 filter any priority
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_any_priority"
        mydict['chain'] = f"filter_v4_any_priority"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in 10.0.0.0/8) {{set bgp-path-peer-prepend 1; accept}}"
        d_config[item2['name']].append(mydict)

        #routing filter ipv6
        #ITEM 1a filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_{item2['location']}"
        mydict['chain'] = f"filter_v6_{item2['location']}"
        mydict['disabled'] = 'false'
        
        mydict['rule'] = f"if (dst in {item2['subnetv6']} || dst in {item2['subnetv6slaac']}) {{accept}}"
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2a filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_{item1['location']}"
        mydict['chain'] = f"filter_v6_{item1['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {item1['subnetv6']} || dst in {item1['subnetv6slaac']}) {{accept}}"
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 1b filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_{item2['location']}"
        mydict['chain'] = f"filter_v6_{item2['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {item2['subnetv6']} || dst in {item2['subnetv6slaac']} ) {{accept}}"
        d_config[item2['name']].append(mydict)

        #ITEM 2b filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_{item1['location']}"
        mydict['chain'] = f"filter_v6_{item1['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {item1['subnetv6']} || dst in {item1['subnetv6slaac']}) {{accept}}"
        d_config[item2['name']].append(mydict)

        #routing filter ipv6
        #ITEM 1 filter any
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_any"
        mydict['chain'] = f"filter_v6_any"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in ::/0) {{set bgp-path-peer-prepend 2; accept}}"
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2 filter any
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_any"
        mydict['chain'] = f"filter_v6_any"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in ::/0) {{set bgp-path-peer-prepend 2; accept}}"
        d_config[item2['name']].append(mydict)

        #ITEM 1 filter any priority
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_any_priority"
        mydict['chain'] = f"filter_v6_any_priority"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in ::/0) {{set bgp-path-peer-prepend 1; accept}}"
        if item1['role'] == 'external_edge':
            pass
            
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2 filter any priority
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_any_priority"
        mydict['chain'] = f"filter_v6_any_priority"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in ::/0) {{set bgp-path-peer-prepend 1; accept}}"
        d_config[item2['name']].append(mydict)

        #---------------------------------BGP
        #bgp ipv4
        #ITEM 1
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/bgp/connection'
        mydict['comment'] = f"bgp_v4_{candidate}"
        mydict['name'] = f"bgp_v4_{candidate}"
        mydict['as'] = item1['as']
        mydict['disabled'] = 'false'
        mydict['local.role'] = 'ebgp'
        mydict['output.redistribute'] = 'connected'
        mydict['remote.address'] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip2'])}"
        mydict['remote.as'] = item2['as']
        mydict['router-id'] = item1['mgmt_int']
        mydict['routing_table'] = role
        mydict['vrf'] = role
        mydict['use-bfd'] = 'true'

        #We check priority for inbound and any  
        if item2['core_priority']:
            mydict['input.filter'] = "filter_v4_any_priority"
        else:
            mydict['input.filter'] = "filter_v4_any"

        if item1['role'] == 'core' and item2['role'] == 'core':
            mydict['output.filter_chain'] = "filter_v4_any"
        if item1['role'] == 'edge' and item2['role'] == 'core':
            mydict['output.filter_chain'] = f"filter_v4_{item1['location']}"

        if item1['role'] == 'external_edge':
            externalconf[item1['name']][candidate]['ipv4_bgp_config'] = mydict
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/bgp/connection'
        mydict['comment'] = f"bgp_v4_{candidate}"
        mydict['name'] = f"bgp_v4_{candidate}"
        mydict['as'] = item2['as']
        mydict['disabled'] = 'false'
        mydict['local.role'] = 'ebgp'
        mydict['output.redistribute'] = 'connected'
        mydict['remote.address'] = f"{str(item1[subnet_transit_var_v4][item1['conn_number']]['ip1'])}"
        mydict['remote.as'] = item1['as']
        mydict['router-id'] = item2['mgmt_int']
        mydict['routing_table'] = role
        mydict['vrf'] = role
        mydict['use-bfd'] = 'true'

        if item1['role'] == 'core' and item2['role'] == 'core':
            #We check priority for inbound and any  
            if item1['core_priority']:
                mydict['input.filter'] = "filter_v4_any_priority"
            else:
                mydict['input.filter'] = "filter_v4_any"
        if item1['role'] == 'edge' and item2['role'] == 'core':
            mydict['input.filter'] = f"filter_v4_{item1['location']}"

        if item1['role'] == 'external_edge' and item2['role'] == 'core':
            mydict['input.filter'] = f"filter_external_v4_{item1['location']}"

        mydict['output.filter_chain'] = "filter_v4_any"
        d_config[item2['name']].append(mydict)

        #bgp ipv6
        #ITEM 1
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/bgp/connection'
        mydict['comment'] = f"bgp_v6_{candidate}"
        mydict['name'] = f"bgp_v6_{candidate}"
        mydict['as'] = item1['as']
        mydict['disabled'] = 'false'
        mydict['local.role'] = 'ebgp'

        if 'ipv6_advertise_static' in item1.keys():
            if item1['ipv6_advertise_static']:
                mydict['output.redistribute'] = 'connected,static'
            else:
                mydict['output.redistribute'] = 'connected'
        else:
            mydict['output.redistribute'] = 'connected'   

        mydict['remote.address'] = f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip2'])}"
        mydict['remote.as'] = item2['as']
        mydict['router-id'] = item1['mgmt_int']
        mydict['routing_table'] = role
        mydict['vrf'] = role
        mydict['use-bfd'] = 'true'
        #We check priority for inbound and any  
        if item2['core_priority']:
            mydict['input.filter'] = "filter_v6_any_priority"
        else:
            mydict['input.filter'] = "filter_v6_any"

        if item1['role'] == 'core' and item2['role'] == 'core':
            mydict['output.filter_chain'] = "filter_v6_any"
        if item1['role'] == 'edge' and item2['role'] == 'core':
            mydict['output.filter_chain'] = f"filter_v6_{item1['location']}"

        mydict['address_families'] = 'ipv6'
        if item1['role'] == 'external_edge':
            externalconf[item1['name']][candidate]['ipv6_bgp_config'] = mydict
        else:
            d_config[item1['name']].append(mydict)

        #ITEM 2
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/bgp/connection'
        mydict['comment'] = f"bgp_v6_{candidate}"
        mydict['name'] = f"bgp_v6_{candidate}"
        mydict['as'] = item2['as']
        mydict['disabled'] = 'false'
        mydict['local.role'] = 'ebgp'

        if 'ipv6_advertise_static' in item2.keys():
            if item2['ipv6_advertise_static']:
                mydict['output.redistribute'] = 'connected,static'
            else:
                mydict['output.redistribute'] = 'connected'
        else:
            mydict['output.redistribute'] = 'connected'   

        mydict['remote.address'] = f"{str(item1[subnet_transit_var_v6][item1['conn_number']]['ip1'])}"
        mydict['remote.as'] = item1['as']
        mydict['router-id'] = item2['mgmt_int']
        mydict['routing_table'] = role
        mydict['vrf'] = role
        mydict['use-bfd'] = 'true'

        if item1['role'] == 'core' and item2['role'] == 'core':
            #We check priority for inbound and any  
            if item1['core_priority']:
                mydict['input.filter'] = "filter_v6_any_priority"
            else:
                mydict['input.filter'] = "filter_v6_any"

        if item1['role'] == 'edge' and item2['role'] == 'core':
            mydict['input.filter'] = f"filter_v6_{item1['location']}"
        if item1['role'] == 'external_edge' and item2['role'] == 'core':
            mydict['input.filter'] = f"filter_external_v6_{item1['location']}"

        mydict['output.filter_chain'] = "filter_v6_any"

        mydict['address_families'] = 'ipv6'
        d_config[item2['name']].append(mydict)

    return secrets


