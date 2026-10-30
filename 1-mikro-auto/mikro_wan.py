import logging
import mikro_shared
import os
import yaml
import wgconfig.wgexec as wgexec
import json
import mikro_docs
import ipaddress

PERSISTENT_KEEPALIVE="10s"
LOOPBACK_IP_PREFIX = '10.0.0'

TRANSIT_NETWORK_V4 = "subnet_transitv4"
TRANSIT_NETWORK_V6 = "subnet_transitv6"
#Number of transit subnets prepared per device in mikro_shared.prepare_sdn
TRANSIT_SUBNETS = 64

my_config = os.environ.get("CONFIG")
path_secrets = os.environ.get("SECRETS")

#Classify devices
core_devices = []
edge_devices = []
external_devices = []
#Create list of global config for hole wan
d_config = {}
externalconf = {}
empty_secrets = {}



def loadWan(inventory):

    global externalconf

    #Get secrets file
    with open(f'{path_secrets}/secrets.json') as file:
        secrets = json.load(file)
        file.close()

    #Classify devices
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

    #CREATE BGP INSTANCE starting version >= ROS 7.20
    for device in core_devices:
        if device['api_version'] >= 720:
            mydict={}
            mydict['comment'] = f"bgp_instance_main_{device['name']}"
            mydict['resource'] = '/routing/bgp/instance'
            mydict['name'] = f"bgp_instance_main_{device['name']}"
            mydict['as'] = device['as']
            mydict['router_id'] = device['mgmt_int']
            mydict['use_set'] = False
            d_config[device['name']].append(mydict)
    for device in edge_devices:
        if device['role'] != 'external_edge':
            if device['api_version'] >= 720:
                mydict={}
                mydict['comment'] = f"bgp_instance_main_{device['name']}"
                mydict['resource'] = '/routing/bgp/instance'
                mydict['name'] = f"bgp_instance_main_{device['name']}"
                mydict['as'] = device['as']
                mydict['router_id'] = device['mgmt_int']
                mydict['use_set'] = False
                d_config[device['name']].append(mydict)

    #CREATE CONNECTIONS
    for device1,device2 in wan_pairs(core_devices,edge_devices):
        secrets = create_connection(device1,device2,secrets,"main")

    #Save secrets file. Secrets persistency to avoid regenerating keys each time
    with open (f'{path_secrets}/secrets.json', 'w') as file:
        secrets = json.dump(secrets, file)
        file.close()

    #Save external device config files
    with open (f'{path_secrets}/external/external.yml', 'w') as file:
        yaml.dump(externalconf, file)
        file.close()
    with open (f'{path_secrets}/external/external.json', 'w') as file:
        json.dump(externalconf, file)
    file.close()

    #Create external config files
    mikro_docs.external_files(externalconf)

    return d_config


def wan_pairs(core_devices,edge_devices,role="main"):

    #Objective: the links of the wan mesh, one entry per link, in a stable order.
    #Shared by loadWan and by the mikro_ports report so both always see the same mesh.

    #Order the cores by wan_order. On a core-core link the transit subnet is taken from the
    #block of the first core of the pair (device1), so which core is device1 must depend only
    #on wan_order and never on the order the inventory files happen to load in (filename order
    #and wan_order can diverge when a core is added whose name doesn't sort like its wan_order).
    core_devices = sorted(core_devices, key=lambda item: item['wan_order'])

    pairs = []
    seen = []

    #CORE TO CORE
    for core1 in core_devices:
        for core2 in core_devices:
            if core1['name'] != core2['name']:
                candidate = mikro_shared.connection_name(f"{core1['name']}_{role}",f"{core2['name']}_{role}")
                if not candidate in seen:
                    seen.append(candidate)
                    pairs.append((core1,core2))

    #EDGE TO CORE
    for edge in edge_devices:
        for core in core_devices:
            candidate = mikro_shared.connection_name(f"{edge['name']}_{role}",f"{core['name']}_{role}")
            if not candidate in seen:
                seen.append(candidate)
                pairs.append((edge,core))

    return pairs

def conn_slot(device,peer):

    #Objective: slot of peer inside device, the position peer takes in the wan_order
    #sequence once device itself is taken out of it. Only moves if wan_order is edited.

    if peer['wan_order'] > device['wan_order']:
        slot = peer['wan_order'] - 1
    else:
        slot = peer['wan_order']

    #The slot indexes the transit subnets built in mikro_shared.prepare_sdn (64 of them)
    if slot >= TRANSIT_SUBNETS:
        logging.error(f"{device['name']} -> wan slot {slot} for peer {peer['name']} is out of the {TRANSIT_SUBNETS} available transit subnets. Renumber wan_order")
        mikro_shared.errorStop()

    return slot

def create_connection(device1,device2,secrets,role):

    #Objective: Create wireguard + bgp connection between two devices
    #       device1 = edge  or core1
    #       device2 = core2

    global externalconf
    
    #Candidate is a unique name for the connection on both devices. Used on secrets and to avoid recreating connections.
    candidate = mikro_shared.connection_name(f"{device1['name']}_{role}",f"{device2['name']}_{role}")

    #Connection list tracking in execution is created if not exist already inside device object
    if not 'connections' in device1.keys():
        device1['connections'] = []
    if not 'connections' in device2.keys():
        device2['connections'] = []

    #Check if connection already exists
    if not candidate in device1['connections']:
        device1['connections'].append(candidate)
        device2['connections'].append(candidate)

        #Create wireguard
        #If secret empty create list
        if secrets == None:
            secrets = {}

        #CHECK IF KEYS EXIST
        if not candidate in secrets:
            #Creating key
            device1_keys = wgexec.generate_keypair()
            device2_keys = wgexec.generate_keypair()
            preshared_key = wgexec.generate_presharedkey()
            secrets [candidate] = {f"{device1['name']}_{role}_private":device1_keys[0], f"{device1['name']}_{role}_public":device1_keys[1], f"{device2['name']}_{role}_private":device2_keys[0], f"{device2['name']}_{role}_public":device2_keys[1] , 'preshared':preshared_key }

        #conn_number is the wireguard slot of this connection on each device: it sets the
        #listen port (51820+slot) and the transit subnet index. It is derived from the
        #wan_order pinned in the inventory instead of a running counter, so it never depends
        #on the order the inventory files are loaded in.
        device1['conn_number'] = conn_slot(device1,device2)
        device2['conn_number'] = conn_slot(device2,device1)

        #logging.debug(f"wan generation conn {device1['name']}_{role} -> {device1['conn_number']}    {device2['name']}_{role} -> {device2['conn_number']}")

        #----------prepare external object with candidate
        if device1['role'] == 'external_edge':
            externalconf[device1['name']][candidate]={'connection':candidate}

        #-------------------------------------WIREGUARD

        #CREATE INT LIST WIREGUARD
        mydict={}
        mydict['comment'] = f"int_list_wireguard_{role}"
        mydict['resource'] = '/interface/list'
        mydict['include'] = 'static'
        mydict['name'] = f'list_wireguard_{role}'
        mydict['use_set'] = False

        if device1['role'] == 'external_edge':
            pass
        else:
            d_config[device1['name']].append(mydict)


        mydict={}
        mydict['comment'] = f"int_list_wireguard_{role}"
        mydict['resource'] = '/interface/list'
        mydict['include'] = 'static'
        mydict['name'] = f'list_wireguard_{role}'
        mydict['use_set'] = False
        d_config[device2['name']].append(mydict)

        #CREATE INT LIST WIREGUARD EXTERNAL
        mydict={}
        mydict['comment'] = f"int_list_external_wireguard_{role}"
        mydict['resource'] = '/interface/list'
        mydict['include'] = 'static'
        mydict['name'] = f'list_external_wireguard_{role}'
        mydict['use_set'] = False
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)


        mydict={}
        mydict['comment'] = f"int_list_external_wireguard_{role}"
        mydict['resource'] = '/interface/list'
        mydict['include'] = 'static'
        mydict['name'] = f'list_external_wireguard_{role}'
        mydict['use_set'] = False
        d_config[device2['name']].append(mydict)


        #INTERFACE WIREGUARD
        #ITEM 1
        mydict={}
        mydict['comment'] = f"int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['resource'] = '/interface/wireguard'
        mydict['mtu'] = device1['wg_mtu']
        mydict['name'] = f"int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['listen_port'] = str(51820+device1['conn_number'])
        mydict['private_key'] = secrets[candidate][f"{device1['name']}_{role}_private"]
        mydict['use_set'] = False
        if device1['role'] == 'external_edge':
            externalconf[device1['name']][candidate]['wireguard_interface'] = mydict 
        else:
            d_config[device1['name']].append(mydict)


        #ITEM 2
        mydict={}
        mydict['comment'] = f"int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['resource'] = '/interface/wireguard'
        mydict['mtu'] = device2['wg_mtu']
        mydict['name'] = f"int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"

        if device1['role'] == 'external_edge' and 'external_wg_main_port' in device1.keys():
            mydict['listen_port'] = str(device1['external_wg_main_port'])
        else:
            mydict['listen_port'] = str(51820+device2['conn_number'])

        mydict['private_key'] = secrets[candidate][f"{device2['name']}_{role}_private"]
        mydict['use_set'] = False
        d_config[device2['name']].append(mydict)


        #--------------ADD FIREWALL RULES TO ALLOW INBOUND FROM THIS WIREGUARD INTERFACE.
    
        #device1: 
        #ipv4
        if device1['backbone_untrusted']:
            pass
        else:
            mydict={}
            mydict['comment'] = f"fw_v4_forward_wgmain_in_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ip/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            if device2['role'] == 'external_edge':
                pass
                
            else:
                d_config[device2['name']].append(mydict)
            #ipv6
            mydict={}
            mydict['comment'] = f"fw_v6_forward_wgmain_in_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ipv6/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            if device2['role'] == 'external_edge':
                pass
                
            else:
                d_config[device2['name']].append(mydict)

        #device2: 
        if device2['backbone_untrusted']:
            pass
        else:
            #ipv4
            mydict={}
            mydict['comment'] = f"fw_v4_forward_wgmain_in_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ip/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            if device1['role'] == 'external_edge':
                pass
                
            else:
                d_config[device1['name']].append(mydict)

            #ipv6
            mydict={}
            mydict['comment'] = f"fw_v6_forward_wgmain_in_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ipv6/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            if device1['role'] == 'external_edge':
                pass
                
            else:
                d_config[device1['name']].append(mydict)


        if device2['backbone_untrusted']:
            #device1 add to list external
            mydict={}
            mydict['comment'] = f"list_external_item_int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['resource'] = '/interface/list/member'
            mydict['interface'] = f"int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['list'] = f'list_external_wireguard_{role}'
            mydict['use_set'] = False
            if device1['role'] == 'external_edge':
                pass
                
            else:
                d_config[device1['name']].append(mydict)

        else:
            #device1 add to list
            mydict={}
            mydict['comment'] = f"list_item_int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['resource'] = '/interface/list/member'
            mydict['interface'] = f"int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['list'] = f'list_wireguard_{role}'
            mydict['use_set'] = False
            if device1['role'] == 'external_edge':
                pass
                
            else:
                d_config[device1['name']].append(mydict)

        if device1['backbone_untrusted']:    
            #device2 add to listexternal
            mydict={}
            mydict['comment'] = f"list_external_item_int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['resource'] = '/interface/list/member'
            mydict['interface'] = f"int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['list'] = f'list_external_wireguard_{role}'
            mydict['use_set'] = False
            d_config[device2['name']].append(mydict)
        else: 
            #device2 add to list
            mydict={}
            mydict['comment'] = f"list_item_int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['resource'] = '/interface/list/member'
            mydict['interface'] = f"int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['list'] = f'list_wireguard_{role}'
            mydict['use_set'] = False
            d_config[device2['name']].append(mydict)

        #ITEM 1 FW external
        #ipv4
        mydict={}
        mydict['comment'] = f"fw_in_wireguard_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = str(51820+device1['conn_number'])
        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ipv6
        mydict={}
        mydict['comment'] = f"fwv6_in_wireguard_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = str(51820+device1['conn_number'])
        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)       

        #ITEM 2 FW external
        #ipv4
        mydict={}
        mydict['comment'] = f"fw_in_wireguard_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'

        if device1['role'] == 'external_edge' and 'external_wg_main_port' in device1.keys():
            mydict['dst_port'] = str(device1['external_wg_main_port'])
        else:
            mydict['dst_port'] = str(51820+device2['conn_number'])

        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[device2['name']].append(mydict)     

        #ipv6
        mydict={}
        mydict['comment'] = f"fwv6_in_wireguard_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'

        if device1['role'] == 'external_edge' and 'external_wg_main_port' in device1.keys():
            mydict['dst_port'] = str(device1['external_wg_main_port'])
        else:
            mydict['dst_port'] = str(51820+device2['conn_number'])

        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[device2['name']].append(mydict)   

        #INTERFACE WIREGUARD PEER
        #ITEM 1
        mydict={}
        mydict['name'] = f"int_wg_peer_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['comment'] = f"int_wg_peer_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['resource'] = '/interface/wireguard/peers'
        mydict['allowed_address'] = '0.0.0.0/0,::/0'
        mydict['endpoint_address'] = device2['external_endpoint']
        #if device1['api_version'] >= 717:
            #mydict['responder'] = 'no'
        #if device1['api_version'] >= 715 and device1['api_version'] <= 716:
            #mydict['is_responder'] = 'no'

        if device1['role'] == 'external_edge' and 'external_wg_main_port' in device1.keys():
            mydict['endpoint_port'] = str(device1['external_wg_main_port'])
        else:
            mydict['endpoint_port'] = str(51820+device2['conn_number'])

        mydict['interface'] = f"int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['preshared_key'] = secrets[candidate]['preshared']
        mydict['public_key'] = secrets[candidate][f"{device2['name']}_{role}_public"]
        mydict['persistent_keepalive'] = PERSISTENT_KEEPALIVE
        mydict['use_set'] = False
        if device1['role'] == 'external_edge':
            externalconf[device1['name']][candidate]['wireguard_peer'] = mydict
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2
        mydict={}
        mydict['name'] = f"int_wg_peer_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['comment'] = f"int_wg_peer_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['resource'] = '/interface/wireguard/peers'
        mydict['allowed_address'] = '0.0.0.0/0,::/0'
        
        #ENDPOINT JUST TO CORE
        if device1['role'] == 'core':
            mydict['endpoint_address'] = device1['external_endpoint']
            #if device2['api_version'] >= 717:
                #mydict['responder'] = 'no'
            #if device2['api_version'] >= 715 and device2['api_version'] <= 716:
                #mydict['is_responder'] = 'no'
        else:
            if device2['api_version'] >= 717:
                mydict['responder'] = 'true'
            if device2['api_version'] >= 715 and device2['api_version'] <= 716:
                mydict['is_responder'] = 'true'

        mydict['endpoint_port'] = str(51820+device1['conn_number'])
        mydict['interface'] = f"int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['preshared_key'] = secrets[candidate]['preshared']
        mydict['public_key'] = secrets[candidate][f"{device1['name']}_{role}_public"]
        mydict['persistent_keepalive'] = PERSISTENT_KEEPALIVE
        mydict['use_set'] = False
        d_config[device2['name']].append(mydict)

        #WIREGUARD PEERS CHANGE PORT SCRIPT 
        #device1
        if device1['role'] == 'edge':
            mydict={}
            mydict['comment'] = f"script_PORT_RANDOM_wg_peer_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['resource'] = '/system/scheduler'
            mydict['name'] = f"script_PORT_RANDOM_wg_peer_{device1['name']}_{role}_to_{device2['name']}_{role}"
            mydict['use_set'] = False
            mydict['policy'] = "reboot,read,write,test,password,sniff,sensitive,romon"
            mydict['start-date'] = "2022-01-01"
            mydict['start-time'] = "00:00:00"
            mydict['interval'] = "6h"

            #Check if site id can be from 1 to 255. Here we just assign ports all between 11100 and 12950
            if device2['site_id'] < 10:
                start_number = device2['site_id'] * 1000 + 100 + 10000
                end_number = device2['site_id'] * 1000 + 200 + 10000 
            else:
                if device2['site_id'] < 100:
                    start_number = device2['site_id'] * 100 + 200 + 10000
                    end_number = device2['site_id'] * 100 + 300 + 10000
                else:
                    if device2['site_id'] < 255:
                        start_number = device2['site_id'] * 10 + 300 + 10000
                        end_number = device2['site_id'] * 10 + 400 + 10000

            mydict['on-event'] = f"/interface wireguard set int_w_{device1['name']}_{role}_to_{device2['name']}_{role} listen-port=[:rndnum from={start_number} to={end_number}]"
            mydict['disabled'] = "false"
            d_config[device1['name']].append(mydict)

        #WIREGUARD PEERS DDNS SCRIPT
        #device1
        mydict={}
        mydict['comment'] = f"script_DDNS_wg_peer_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['resource'] = '/system/scheduler'
        mydict['name'] = f"script_DDNS_wg_peer_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['use_set'] = False
        mydict['policy'] = "reboot,read,write,test,password,sniff,sensitive,romon"
        mydict['start-date'] = "2022-01-01"
        mydict['start-time'] = "00:00:00"
        mydict['interval'] = "30m"
        mydict['on-event'] = f"\
:local wgPeerComment\r\
\n:local wgPeerDns\r\
\n\r\
\n:set wgPeerComment \"int_wg_peer_{device1['name']}_{role}_to_{device2['name']}_{role}\"\r\
\n:set wgPeerDns \"{device2['external_endpoint']}\"\r\
\n\r\
\n\r\
\n:if ([interface wireguard peers get number=[find comment=\"$wgPeerComment\"] value-name=endpoint-address] != [resolve $wgPeerDns]) do={{\r\
\n  interface wireguard peers set number=[find comment=\"$wgPeerComment\"] endpoint-address=[/resolve $wgPeerDns]\r\
\n}}\r\
\n\r\
\n\r\
\n"
        #Just apply ddns if not fixed ip on the config
        if device2['external_ddns']:
            d_config[device1['name']].append(mydict)

        #device2
        #Just if peer is core
        if device1['role'] == 'core':
            mydict={}
            mydict['comment'] = f"script_DDNS_wg_peer_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['resource'] = '/system/scheduler'
            mydict['name'] = f"script_DDNS_wg_peer_{device2['name']}_{role}_to_{device1['name']}_{role}"
            mydict['use_set'] = False
            mydict['policy'] = "reboot,read,write,test,password,sniff,sensitive,romon"
            mydict['start-date'] = "2022-01-01"
            mydict['start-time'] = "00:00:00"
            mydict['interval'] = "30m"
            mydict['on-event'] = f"\
:local wgPeerComment\r\
\n:local wgPeerDns\r\
\n\r\
\n:set wgPeerComment \"int_wg_peer_{device2['name']}_{role}_to_{device1['name']}_{role}\"\r\
\n:set wgPeerDns \"{device1['external_endpoint']}\"\r\
\n\r\
\n\r\
\n:if ([interface wireguard peers get number=[find comment=\"$wgPeerComment\"] value-name=endpoint-address] != [resolve $wgPeerDns]) do={{\r\
\n  interface wireguard peers set number=[find comment=\"$wgPeerComment\"] endpoint-address=[/resolve $wgPeerDns]\r\
\n}}\r\
\n\r\
\n\r\
\n"
            #Just apply ddns if not fixed ip on the config
            if device1['external_ddns']:
                d_config[device2['name']].append(mydict)

        #Pool Vars: Even if now work as constants here for future changes and apply logic if needed


        
        #ITEM 1
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ip/address'
        mydict['interface'] = f"int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['comment'] = f"ip_wg_{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}_{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}"
        mydict['address'] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}"
        if device1['role'] == 'external_edge':
            externalconf[device1['name']][candidate]['ip_address'] = mydict
        else:
            d_config[device1['name']].append(mydict)
            #Document for external use the ip of the peer
            device1[f"self_from_{device1['name']}_to_{device2['name']}"] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}"
            device1[f"peer_from_{device1['name']}_to_{device2['name']}"] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}"


        #ITEM 2
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ip/address'
        mydict['interface'] = f"int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['comment'] = f"ip_wg_{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}_{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}"
        mydict['address'] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}"
        d_config[device2['name']].append(mydict)
        #Document for external use the ip of the peer.
        device2[f"self_from_{device2['name']}_to_{device1['name']}"] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}"
        device2[f"peer_from_{device2['name']}_to_{device1['name']}"] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}"

        #Netwatch monitoring for each peer
        #ITEM 1

        mydict={}
        mydict['comment'] = f"netwatch_wg_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['resource'] = '/tool/netwatch'
        mydict['host'] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}"
        mydict['type'] = "icmp"
        if 'mqtt_netwatch_monitor' in device1.keys():
            if device1['mqtt_netwatch_monitor']:
                mydict['interval'] = "30s"
                mydict['test_script'] = f"\
/iot mqtt publish message=$\"rtt-avg\" broker=\"auto_mqtt_broker_1\" topic=\"mikrotik/rtt-avg/{device1['name']}/{device2['name']}\"\r\
\n"
            else:
                mydict['interval'] = "30s"
                mydict['test_script'] = "# no test configure"
        else:
            mydict['interval'] = "30s"
            mydict['test_script'] = "# no test configure"
        d_config[device1['name']].append(mydict)       

        #ITEM 2

        mydict={}
        mydict['comment'] = f"netwatch_wg_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['resource'] = '/tool/netwatch'
        mydict['host'] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}"
        mydict['type'] = "icmp"
        if 'mqtt_netwatch_monitor' in device2.keys():
            if device2['mqtt_netwatch_monitor']:
                mydict['interval'] = "30s"
                mydict['test_script'] = f"\
/iot mqtt publish message=$\"rtt-avg\" broker=\"auto_mqtt_broker_1\" topic=\"mikrotik/rtt-avg/{device2['name']}/{device1['name']}\"\r\
\n"
            else:
                mydict['interval'] = "30s"
                mydict['test_script'] = "# no test configure"
        else:
            mydict['interval'] = "30s"
            mydict['test_script'] = "# no test configure"
        d_config[device2['name']].append(mydict)

        #IPV4 CHECK IF CORE INTERNET DEFAULT TRANSIT
        #device1
        if device1['role'] == 'core' and device2['role'] == 'core':
            if device2['core_internet_transit']:
                device1[f'internet_vpn_ip'] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}"

            if device1['core_internet_transit']:
                device2[f'internet_vpn_ip'] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}"            

        if device1['role'] == 'edge' and device2['role'] == 'core':
            if device2['core_internet_transit']:
                device1[f'internet_vpn_ip'] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}"         

        #IPV4 CORE_TRANSIT_RULES Add the information to transit to all cores that is then used in other services.
        if not 'core_transits' in device1.keys():
            device1['core_transits']=[]
        if not 'core_transits' in device2.keys():
            device2['core_transits']=[]

        if device1['role'] == 'core' and device2['role'] == 'core':
            device1[f'core_transits'].append( { 'transit_device' : device2['name'] , 'ipv4' : f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}"})

            device2[f'core_transits'].append( { 'transit_device' : device1['name'] , 'ipv4' : f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}"})            

        if device1['role'] == 'edge' and device2['role'] == 'core' :
            device1[f'core_transits'].append( { 'transit_device' : device2['name'] , 'ipv4' : f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}"})

        #ipv6 address
        #ITEM 1
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ipv6/address'
        mydict['interface'] = f"int_w_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['comment'] = f"ip_wg_{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip1'])}_{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}"
        mydict['address'] = f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}"
        if device1['role'] == 'external_edge':
            externalconf[device1['name']][candidate]['ipv6_address'] = mydict
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ipv6/address'
        mydict['interface'] = f"int_w_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['comment'] = f"ip_wg_{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip2'])}_{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}"
        mydict['address'] = f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}"
        d_config[device2['name']].append(mydict)

        #ITEM 1 FW internal bgp ipv4
        mydict={}
        mydict['comment'] = f"fw_in_bgp_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '179'
        mydict['protocol'] = 'tcp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2 FW internal bgp ipv4
        mydict={}
        mydict['comment'] = f"fw_in_bgp_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '179'
        mydict['protocol'] = 'tcp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[device2['name']].append(mydict)    

        #ITEM 1 FW internal bgp ipv6
        mydict={}
        mydict['comment'] = f"fw_in_bgpv6_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '179'
        mydict['protocol'] = 'tcp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2 FW internal bgp ipv6
        mydict={}
        mydict['comment'] = f"fw_in_bgpv6_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '179'
        mydict['protocol'] = 'tcp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[device2['name']].append(mydict)  

        #ITEM 1 FW internal bfd ipv4
        mydict={}
        mydict['comment'] = f"fw_in_bfd_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '3784'
        mydict['protocol'] = 'udp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2 FW internal bfd ipv4
        mydict={}
        mydict['comment'] = f"fw_in_bfd_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '3784'
        mydict['protocol'] = 'udp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[device2['name']].append(mydict)    

        #ITEM 1 FW internal bfd ipv6
        mydict={}
        mydict['comment'] = f"fw_in_bfdv6_{device1['name']}_{role}_to_{device2['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '3784'
        mydict['protocol'] = 'udp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2 FW internal bfd ipv6
        mydict={}
        mydict['comment'] = f"fw_in_bfdv6_{device2['name']}_{role}_to_{device1['name']}_{role}"
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '3784'
        mydict['protocol'] = 'udp'
        mydict['src_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip2'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['dst_address'] = str(ipaddress.ip_network(f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip1'])}/{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['subnet'].prefixlen)}", strict=False))
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        d_config[device2['name']].append(mydict)

        #---------------------------------route filter subnets rule
        #routing filter ipv4
        #EXTERNAL EDGE 

        #ITEM 1 add external subnet
        if device1['role'] == 'external_edge':
            mydict={}
            mydict['use_set'] = False
            mydict['resource'] = '/routing/filter/rule'
            mydict['comment'] = f"filter_external_v4_{device1['location']}"
            mydict['chain'] = f"filter_external_v4_{device1['location']}"
            mydict['disabled'] = 'false'
            mydict['rule'] = f"if (dst in {device1['allow_out_prefix_v4']} || dst in {LOOPBACK_IP_PREFIX}.{device1['site_id']}/32 ) {{accept}}"
            d_config[device2['name']].append(mydict)

        if device1['role'] == 'external_edge':
            mydict={}
            mydict['use_set'] = False
            mydict['resource'] = '/routing/filter/rule'
            mydict['comment'] = f"filter_external_v6_{device1['location']}"
            mydict['chain'] = f"filter_external_v6_{device1['location']}"
            mydict['disabled'] = 'false'
            mydict['rule'] = f"if (dst in {device1['allow_out_prefix_v6']}) {{accept}}"
            d_config[device2['name']].append(mydict)

        #ITEM 1a filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_{device2['location']}"
        mydict['chain'] = f"filter_v4_{device2['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {device2['subnetv4']} || dst in {LOOPBACK_IP_PREFIX}.{device2['site_id']}/32) {{accept}}"
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2a filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_{device1['location']}"
        mydict['chain'] = f"filter_v4_{device1['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {device1['subnetv4']} || dst in {LOOPBACK_IP_PREFIX}.{device1['site_id']}/32) {{accept}}"
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 1b filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_{device2['location']}"
        mydict['chain'] = f"filter_v4_{device2['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {device2['subnetv4']} || dst in {LOOPBACK_IP_PREFIX}.{device2['site_id']}/32) {{accept}}"
        d_config[device2['name']].append(mydict)

        #ITEM 2b filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_{device1['location']}"
        mydict['chain'] = f"filter_v4_{device1['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {device1['subnetv4']} || dst in {LOOPBACK_IP_PREFIX}.{device1['site_id']}/32) {{accept}}"
        d_config[device2['name']].append(mydict)

        #routing filter ipv4
        #ITEM 1 filter any
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_any"
        mydict['chain'] = f"filter_v4_any"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in 10.0.0.0/8) {{set bgp-path-peer-prepend 2; accept}}"
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2 filter any
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_any"
        mydict['chain'] = f"filter_v4_any"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in 10.0.0.0/8) {{set bgp-path-peer-prepend 2; accept}}"
        d_config[device2['name']].append(mydict)

        #ITEM 1 filter any priority
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_any_priority"
        mydict['chain'] = f"filter_v4_any_priority"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in 10.0.0.0/8) {{set bgp-path-peer-prepend 1; accept}}"
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2 filter any priority
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v4_any_priority"
        mydict['chain'] = f"filter_v4_any_priority"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in 10.0.0.0/8) {{set bgp-path-peer-prepend 1; accept}}"
        d_config[device2['name']].append(mydict)

        #routing filter ipv6
        #ITEM 1a filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_{device2['location']}"
        mydict['chain'] = f"filter_v6_{device2['location']}"
        mydict['disabled'] = 'false'
        
        mydict['rule'] = f"if (dst in {device2['subnetv6']} || dst in {device2['subnetv6slaac']}) {{accept}}"
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2a filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_{device1['location']}"
        mydict['chain'] = f"filter_v6_{device1['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {device1['subnetv6']} || dst in {device1['subnetv6slaac']}) {{accept}}"
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 1b filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_{device2['location']}"
        mydict['chain'] = f"filter_v6_{device2['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {device2['subnetv6']} || dst in {device2['subnetv6slaac']} ) {{accept}}"
        d_config[device2['name']].append(mydict)

        #ITEM 2b filter peer subnet
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_{device1['location']}"
        mydict['chain'] = f"filter_v6_{device1['location']}"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in {device1['subnetv6']} || dst in {device1['subnetv6slaac']}) {{accept}}"
        d_config[device2['name']].append(mydict)

        #routing filter ipv6
        #ITEM 1 filter any
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_any"
        mydict['chain'] = f"filter_v6_any"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in ::/0) {{set bgp-path-peer-prepend 2; accept}}"
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2 filter any
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_any"
        mydict['chain'] = f"filter_v6_any"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in ::/0) {{set bgp-path-peer-prepend 2; accept}}"
        d_config[device2['name']].append(mydict)

        #ITEM 1 filter any priority
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_any_priority"
        mydict['chain'] = f"filter_v6_any_priority"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in ::/0) {{set bgp-path-peer-prepend 1; accept}}"
        if device1['role'] == 'external_edge':
            pass
            
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2 filter any priority
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/filter/rule'
        mydict['comment'] = f"filter_v6_any_priority"
        mydict['chain'] = f"filter_v6_any_priority"
        mydict['disabled'] = 'false'
        mydict['rule'] = f"if (dst in ::/0) {{set bgp-path-peer-prepend 1; accept}}"
        d_config[device2['name']].append(mydict)

        #---------------------------------BGP        

        #bgp ipv4
        #ITEM 1
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/bgp/connection'
        mydict['comment'] = f"bgp_v4_{candidate}"
        mydict['name'] = f"bgp_v4_{candidate}"
        mydict['as'] = device1['as']
        mydict['disabled'] = 'false'
        mydict['local.role'] = 'ebgp'
        mydict['output.redistribute'] = 'connected'
        mydict['remote.address'] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip2'])}"
        mydict['remote.as'] = device2['as']
        if device1['role'] != 'external_edge':
            if device1['api_version'] >= 720:
                mydict['instance'] = f"bgp_instance_main_{device1['name']}"
            else:
                mydict['router-id'] = device1['mgmt_int']
        else:
            mydict['router-id'] = device1['mgmt_int']
        mydict['routing_table'] = role
        mydict['vrf'] = role
        if device1['use_bfd'] and device2['use_bfd']:
            mydict['use-bfd'] = 'true'
        else:
            mydict['use-bfd'] = 'false'


        #We check priority for inbound and any  
        if device2['core_priority']:
            mydict['input.filter'] = "filter_v4_any_priority"
        else:
            mydict['input.filter'] = "filter_v4_any"

        if device1['role'] == 'core' and device2['role'] == 'core':
            mydict['output.filter_chain'] = "filter_v4_any"
        if device1['role'] == 'edge' and device2['role'] == 'core':
            mydict['output.filter_chain'] = f"filter_v4_{device1['location']}"

        if device1['role'] == 'external_edge':
            externalconf[device1['name']][candidate]['ipv4_bgp_config'] = mydict
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/bgp/connection'
        mydict['comment'] = f"bgp_v4_{candidate}"
        mydict['name'] = f"bgp_v4_{candidate}"
        mydict['as'] = device2['as']
        mydict['disabled'] = 'false'
        mydict['local.role'] = 'ebgp'
        mydict['output.redistribute'] = 'connected'
        mydict['remote.address'] = f"{str(device1[TRANSIT_NETWORK_V4][device1['conn_number']]['ip1'])}"
        mydict['remote.as'] = device1['as']
        if device2['role'] != 'external_edge':
            if device2['api_version'] >= 720:
                mydict['instance'] = f"bgp_instance_main_{device2['name']}"
            else:
                mydict['router-id'] = device2['mgmt_int']
        else:
            mydict['router-id'] = device2['mgmt_int']
        mydict['routing_table'] = role
        mydict['vrf'] = role
        if device1['use_bfd'] and device2['use_bfd']:
            mydict['use-bfd'] = 'true'
        else:
            mydict['use-bfd'] = 'false'

        if device1['role'] == 'core' and device2['role'] == 'core':
            #We check priority for inbound and any  
            if device1['core_priority']:
                mydict['input.filter'] = "filter_v4_any_priority"
            else:
                mydict['input.filter'] = "filter_v4_any"
        if device1['role'] == 'edge' and device2['role'] == 'core':
            mydict['input.filter'] = f"filter_v4_{device1['location']}"

        if device1['role'] == 'external_edge' and device2['role'] == 'core':
            mydict['input.filter'] = f"filter_external_v4_{device1['location']}"

        mydict['output.filter_chain'] = "filter_v4_any"
        d_config[device2['name']].append(mydict)

        #bgp ipv6
        #ITEM 1
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/bgp/connection'
        mydict['comment'] = f"bgp_v6_{candidate}"
        mydict['name'] = f"bgp_v6_{candidate}"
        mydict['as'] = device1['as']
        mydict['disabled'] = 'false'
        mydict['local.role'] = 'ebgp'

        if 'ipv6_advertise_static' in device1.keys():
            if device1['ipv6_advertise_static']:
                mydict['output.redistribute'] = 'connected,static'
            else:
                mydict['output.redistribute'] = 'connected'
        else:
            mydict['output.redistribute'] = 'connected'   

        mydict['remote.address'] = f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip2'])}"
        mydict['remote.as'] = device2['as']
        if device1['role'] != 'external_edge':
            if device1['api_version'] >= 720:
                mydict['instance'] = f"bgp_instance_main_{device1['name']}"
            else:
                mydict['router-id'] = device1['mgmt_int']
        else:
            mydict['router-id'] = device1['mgmt_int']
        mydict['routing_table'] = role
        mydict['vrf'] = role
        if device1['use_bfd'] and device2['use_bfd']:
            mydict['use-bfd'] = 'true'
        else:
            mydict['use-bfd'] = 'false'
        #We check priority for inbound and any  
        if device2['core_priority']:
            mydict['input.filter'] = "filter_v6_any_priority"
        else:
            mydict['input.filter'] = "filter_v6_any"

        if device1['role'] == 'core' and device2['role'] == 'core':
            mydict['output.filter_chain'] = "filter_v6_any"
        if device1['role'] == 'edge' and device2['role'] == 'core':
            mydict['output.filter_chain'] = f"filter_v6_{device1['location']}"

        if "api_version" in device1.keys():
            if device1['api_version'] >= 719:
                mydict['afi'] = 'ipv6'
            else:
                mydict['address_families'] = 'ipv6'
        else:
            mydict['address_families'] = 'ipv6'


        if device1['role'] == 'external_edge':
            externalconf[device1['name']][candidate]['ipv6_bgp_config'] = mydict
        else:
            d_config[device1['name']].append(mydict)

        #ITEM 2
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/routing/bgp/connection'
        mydict['comment'] = f"bgp_v6_{candidate}"
        mydict['name'] = f"bgp_v6_{candidate}"
        mydict['as'] = device2['as']
        mydict['disabled'] = 'false'
        mydict['local.role'] = 'ebgp'

        if 'ipv6_advertise_static' in device2.keys():
            if device2['ipv6_advertise_static']:
                mydict['output.redistribute'] = 'connected,static'
            else:
                mydict['output.redistribute'] = 'connected'
        else:
            mydict['output.redistribute'] = 'connected'   

        mydict['remote.address'] = f"{str(device1[TRANSIT_NETWORK_V6][device1['conn_number']]['ip1'])}"
        mydict['remote.as'] = device1['as']
        if device2['role'] != 'external_edge':
            if device2['api_version'] >= 720:
                mydict['instance'] = f"bgp_instance_main_{device2['name']}"
            else:
                mydict['router-id'] = device2['mgmt_int']
        else:
            mydict['router-id'] = device2['mgmt_int']
        mydict['routing_table'] = role
        mydict['vrf'] = role
        if device1['use_bfd'] and device2['use_bfd']:
            mydict['use-bfd'] = 'true'
        else:
            mydict['use-bfd'] = 'false'

        if device1['role'] == 'core' and device2['role'] == 'core':
            #We check priority for inbound and any  
            if device1['core_priority']:
                mydict['input.filter'] = "filter_v6_any_priority"
            else:
                mydict['input.filter'] = "filter_v6_any"

        if device1['role'] == 'edge' and device2['role'] == 'core':
            mydict['input.filter'] = f"filter_v6_{device1['location']}"
        if device1['role'] == 'external_edge' and device2['role'] == 'core':
            mydict['input.filter'] = f"filter_external_v6_{device1['location']}"

        mydict['output.filter_chain'] = "filter_v6_any"

        if "api_version" in device2.keys():
            if device2['api_version'] >= 719:
                mydict['afi'] = 'ipv6'
            else:
                mydict['address_families'] = 'ipv6'
        else:
            mydict['address_families'] = 'ipv6'

        d_config[device2['name']].append(mydict)

    return secrets


