#General Lib

from yaml.loader import SafeLoader
import yaml
import json
import sys
import os
import logging
from dotenv import load_dotenv

#Mikro Lib
import mikro_shared
import mikro_fw
import mikro_lan
import mikro_wan
import mikro_autoupdate
import mikro_internet
import mikro_wg
import mikro_wifi
import mikro_netwatch
import mikro_radius_server
import mikro_docs
import mikro_log

#Multitask Lib
from concurrent.futures import ThreadPoolExecutor
WORKERS_MAX = 30
MULTIMODE= True



error_counter = 0

load_dotenv()

pathconfig = os.environ.get("CONFIG")
path_secrets = os.environ.get("SECRETS")
pathcontrol = os.environ.get("CONTROLPATH")
list_localstring = json.loads(os.environ.get("LOCALSTRING"))
micro_user = os.environ.get("MIKRO_USER")
micro_pass = os.environ.get("MIKRO_PASSWORD")
debugmode = os.environ.get("DEBUGMODE")

managed_roles = ["core" , "edge" ]

#CONFIG FOR PROD
#logging.basicConfig(level=logging.INFO)
#prod=True

#CONFIG FOR TEST
if debugmode:
    mikro_log.setup(level=logging.DEBUG)
    prod=False
else:
    mikro_log.setup(level=logging.INFO)
    prod=False


def generate_config ():
    logging.info("GENERAL -> ------------------------GENERATE CONFIG")

    logging.info ("GENERAL -> load inventory")
    my_inventory=mikro_shared.load_inventory()

    #------ADD SDN TO DEVICES
    logging.info ("GENERAL -> Prepare SDN wan info")
    for device in my_inventory:
        mikro_shared.prepare_sdn(device)

    #------PREPARE GLOBAL WAN CONFIG
    logging.info ("GENERAL -> Generate wan Config")
    wan_config=mikro_wan.loadWan(my_inventory)

    logging.info ("GENERAL -> Generate device config")
    configlet_rows = []
    for device in my_inventory:
        if not device['clean_config']:
            if device['role'] in managed_roles:

                global_config = []
                global_fw_config = []

                logging.debug (f"{device['name']} --> Generate config for: ---> {device['configlet']}")
                configlet_rows.append(device)
                
                #------------FW
                if 'fw' in device['configlet']:        

                    #Load Global FW config
                    my_config=mikro_shared.load_config('global',"firewall")
                    global_fw_config.extend(my_config)

                    #Load specific device FW config
                    if  os.path.exists(f"{pathconfig}/firewall/{device['name']}"):
                        my_config=mikro_shared.load_config(device['name'],"firewall")
                        global_fw_config.extend(my_config)
                    else:
                        logging.warning (f"{device['name']} --> Warning No specific FW config ")

                #------------General config
                if 'general' in device['configlet']:
                    my_config=mikro_shared.load_config(device['role'],"general")
                    global_config.extend(my_config)

                #------------LAN ROLE (bridge and vlans)
                if 'lan' in device['configlet']:
                    my_config=mikro_lan.load_config(device,my_inventory)
                    global_config.extend(my_config)

                #------------WAN (wireguard, bgp)
                if 'wan' in device['configlet']:
                    if device['name'] in wan_config.keys():
                        my_config=wan_config[device['name']]
                        global_config.extend(my_config)

                #------------DHCP leases 
                if 'dhcp' in device['configlet']:
                    my_config=mikro_shared.load_config_by_device("ipv4","dhcp",device['name'])
                    global_config.extend(my_config)

                #------------autoupdate
                if 'autoupdate' in device['configlet']:
                    my_config=mikro_autoupdate.load_config(device)
                    global_config.extend(my_config)            

                #------------INTERNET
                if 'internet' in device['configlet']:
                    my_config=mikro_internet.load_config(device)
                    global_config.extend(my_config)    

                #------------WG VPN
                if 'wg_vpn' in device['configlet']:
                    my_config=mikro_wg.load_config(device)
                    global_config.extend(my_config)  

                #------------WIFI ROLE (interface radius)
                if 'wifi' in device['configlet'] and 'lan' in device['configlet']:
                    my_config=mikro_wifi.load_config(device,my_inventory)
                    global_config.extend(my_config)  
    
                #------------NETWATCH ROLE 
                if 'netwatch' in device['configlet']:
                    my_config=mikro_netwatch.load_config(device)
                    global_config.extend(my_config)  

                #------------RADIUS SERVER ROLE 
                if 'radius_server' in device['configlet']:
                    my_config=mikro_radius_server.load_config(device)
                    global_config.extend(my_config)  

                #------------FILTER DUPLICATED
                #Is expected automation create duplicated objects like bgp filters this help to just implement them once
                global_config = mikro_shared.filterDuplicatedConfigRules(global_config)

                #------------ORGANIZE

                #copy from global to global fw fw rules
                for item in global_config:
                    if item['resource'] == '/ip/firewall/filter' or item['resource'] == '/ipv6/firewall/filter'  or item['resource'] == '/ip/firewall/nat'  or item['resource'] == '/ip/firewall/mangle' or item['resource'] == '/ipv6/firewall/mangle' :
                        global_fw_config.append(item)

                #Remove from glboal config all FW rules. They are already copy to global_fw_config
                global_config2=[]
                for item in global_config:
                    if item['resource'] != '/ip/firewall/filter' and item['resource'] != '/ipv6/firewall/filter' and item['resource'] != '/ip/firewall/nat' and item['resource'] != '/ip/firewall/mangle' and item['resource'] != '/ipv6/firewall/mangle' :
                        global_config2.append(item)
                global_config = global_config2

                #----------------SAVE PROPOSED CONFIG
                #Check if folder exist

                if not os.path.exists(f"{path_secrets}/proposed/"):
                    os.makedirs(f"{path_secrets}/proposed/")
                if not os.path.exists(f"{path_secrets}/old_proposed/"):
                    os.makedirs(f"{path_secrets}/old_proposed/")

                #if file exist move to old proposed
                if  os.path.exists(f"{path_secrets}/proposed/{device['name']}_fw.json"):
                    os.replace(f"{path_secrets}/proposed/{device['name']}_fw.json", f"{path_secrets}/old_proposed/{device['name']}_fw.json")

                if  os.path.exists(f"{path_secrets}/proposed/{device['name']}_global.json"):
                    os.replace(f"{path_secrets}/proposed/{device['name']}_global.json", f"{path_secrets}/old_proposed/{device['name']}_global.json")

                #Save config file
                with open (f"{path_secrets}/proposed/{device['name']}_fw.json", 'w') as file1:
                    json.dump(global_fw_config, file1)
                    file1.close()

                with open (f"{path_secrets}/proposed/{device['name']}_global.json", 'w') as file2:
                    json.dump(global_config, file2)
                    file2.close()

                #----------------SAVE PROPOSED CONFIG for humans
                with open (f"{path_secrets}/proposed/{device['name']}_fw.yml", 'w') as file1:
                    yaml.dump(global_fw_config, file1)
                    file1.close()

                with open (f"{path_secrets}/proposed/{device['name']}_global.yml", 'w') as file2:
                    yaml.dump(global_config, file2)
                    file2.close()

                #----------------SAVE PROPOSED CONFIG markdown and html

                mikro_docs.createDocs(device)

    configlet_report(configlet_rows)
    logging.debug (f"Config generation DONE \n\n")


def configlet_report(devices):
    #Device x configlet matrix, the configlets in the order they first appear
    configlets = []
    for device in devices:
        configlets.extend(item for item in device['configlet'] if item not in configlets)
    rows = [[device['name'], device['role']] + ["✅" if item in device['configlet'] else "·" for item in configlets]
            for device in devices]
    mikro_log.report("GENERAL -> Generated config", ["Device", "Role"] + configlets, rows)


def aux_address(device):
    #Alternative management address. mtmt_aux is the misspelled key of older inventories
    return device.get('mgmt_aux', device.get('mtmt_aux'))


def clean_config (device,mode,dry_run,aux_ip=False):
    #Read file
    if device['push_clean']:
        mikro_shared.prepare_sdn(device)
        if device['clean_config']:
            global_config=[]
            global_fw_config=[]
        else:
            with open(f"{path_secrets}/proposed/{device['name']}_fw.json") as file1:
                global_fw_config = json.load(file1)
                file1.close()

            with open(f"{path_secrets}/proposed/{device['name']}_global.json") as file2:
                global_config = json.load(file2)
                file2.close()

        #------------login
        connected = False

        if aux_ip:
            api_device=mikro_shared.login (micro_user,micro_pass,aux_address(device),device) 
            if api_device:
                connected = True
            else:
                logging.error (f"{device['name']} ->--CONNECTION AUX ERROR!->>> at IP {aux_address(device)}")
                #mikro_shared.errorStop() 

        else:
            api_device=mikro_shared.login (micro_user,micro_pass,device['mgmt_int'],device)
            if api_device:
                connected = True
            else:
                api_device=mikro_shared.login (micro_user,micro_pass,device['mgmt_ext'],device)
                if api_device:
                    connected = True

                else:
                    logging.error (f"{device['name']} ->--CONNECTION ERROR!->>> at IP {device['mgmt_ext']}")
                    #mikro_shared.errorStop() 

        #Apply if connected
        if connected:
            logging.info (f"{device['name']} -> Start clean")
            if mode == 'firewall' or mode == 'global':
                mikro_docs.dry_run_add(f"###Clean firewall Rules \n")
                mikro_fw.clean_config(api_device,global_fw_config,dry_run,device)
            if mode == 'global':
                mikro_docs.dry_run_add(f"###Clean General confing \n")
                mikro_shared.clean_config(api_device,global_config,dry_run,device)
            logging.info (f"{device['name']} -> OK clean")

def push_config (device,mode,dry_run,aux_ip=False):
    #Read file
    if device['push_config'] and not device['clean_config']:
        mikro_shared.prepare_sdn(device)

        with open(f"{path_secrets}/proposed/{device['name']}_fw.json") as file1:
            global_fw_config = json.load(file1)
            file1.close()

        with open(f"{path_secrets}/proposed/{device['name']}_global.json") as file2:
            global_config = json.load(file2)
            file2.close()

        #------------login
        connected = False

        if aux_ip:
            api_device=mikro_shared.login (micro_user,micro_pass,aux_address(device),device) 
            if api_device:
                connected = True
            else:
                logging.error (f"{device['name']} ->--CONNECTION AUX ERROR!->>> at IP {aux_address(device)}")
                #mikro_shared.errorStop() 

        else:
            api_device=mikro_shared.login (micro_user,micro_pass,device['mgmt_int'],device)
            if api_device:
                connected = True
            else:
                api_device=mikro_shared.login (micro_user,micro_pass,device['mgmt_ext'],device)
                if api_device:
                    connected = True

                else:
                    logging.error (f"{device['name']} ->--CONNECTION ERROR!->>> at IP {device['mgmt_ext']}")
                    #mikro_shared.errorStop() 

        #Apply if connected
        if connected:
            logging.info (f"{device['name']} -> Start push")
            if mode == 'global':

                mikro_docs.dry_run_add(f"###Push general config \n")
                mikro_shared.process_config(api_device,global_config,device,dry_run)  
            if mode == 'firewall' or mode == 'global':

                mikro_docs.dry_run_add(f"###Push firewall rules \n")
                mikro_fw.process_fw_rules(api_device,global_fw_config,dry_run,device)
            logging.info (f"{device['name']} -> OK push")
    else:
        logging.info (f"{device['name']} -> Push Disabled")

def clean_and_push(device,mode,dry_run,aux_ip):

    if device['role'] in managed_roles:
        if dry_run:
            mikro_docs.dry_run_add(f"##SIMULATION DRY RUN\n")
        else:
            mikro_docs.dry_run_add(f"##PUSH MODE REAL\n")
            mikro_docs.dry_run_add(f"##DEVICE {device['name']}\n")
        clean_config(device,mode,dry_run,aux_ip)
        push_config(device,mode,dry_run,aux_ip)

    return True

#This path use all the automation to create all and push
def control_automation(mode,dry_run,specific_device_name,aux_ip):

    logging.info (f"GENERAL -> ------------------------AUTOMATION LOAD INVENTORY") 
    my_inventory=mikro_shared.load_inventory()

    #Create minimum needed files
    logging.info (f"GENERAL -> ------------------------CREATE FILES") 
    #CREATE FILE STRUCTURE
    mikro_shared.create_files()
    if  mode == 'config':    
        logging.warning (f"GENERAL -> MODE JUST CONFIG") 
    #GENERATE CONFIGS
    if mode == 'firewall' or mode == 'global' or mode == 'config':
        generate_config ()

    if not specific_device_name:
        #PUSH CONFIGS
        #if mode config we do not push
        if mode == 'firewall' or mode == 'global':

            if MULTIMODE:
                logging.info (f"GENERAL -> PUSH MODE MULTI THREAD") 
                #-------------MULTI TASK
                with ThreadPoolExecutor(max_workers=WORKERS_MAX) as executor:
                    for i in range(0, len(my_inventory), WORKERS_MAX):
                        batch = my_inventory[i:i+WORKERS_MAX]
                        futures = [executor.submit(clean_and_push, device, mode, dry_run, False  ) for device in batch]
                        # Wait for all tasks in the current batch to complete
                        for future in futures:
                            future.result()

            else:
                #-------------SINGLE TASK
                logging.info (f"GENERAL -> PUSH MODE SINGLE THREAD") 
                for device in my_inventory:

                        clean_and_push(device,mode,dry_run, False)


        #----------------GENERATE MARKDOWN AND HTML
        logging.info (f"GENERAL -> Start Creating DOCS")    
        mikro_docs.create_external()
        #Save globals
        mikro_docs.save_global()
        #Safe dry_run
        mikro_docs.savedry_run()
        logging.info (f"GENERAL -> DONE Creating DOCS")  

        if mode == 'firewall' or mode == 'global':
            mikro_log.device_report("GENERAL -> Push result", [device['name'] for device in my_inventory if device['role'] in managed_roles])

        logging.info (f"GENERAL -> ------------------------AUTOMATION END MIKRO AUTO")    
    else:
        logging.info (f"ONEHOST MODE -> START ONE HOST - >{specific_device_name} ")  
        #find device
        target_device = None
        for device in my_inventory:
            if device['name'] == specific_device_name:
                target_device = device
                break

        device = target_device
        if device:
            logging.info (f"ONEHOST MODE -> SPECIFIC HOST found -> {device['name']}")  
            #PUSH CONFIGS
            #if mode config we do not push
            if mode == 'firewall' or mode == 'global':
                if device['role'] in managed_roles:
                    clean_and_push(device,mode,dry_run,aux_ip)    
                    logging.info (f"ONEHOST MODE -> OK -> {device['name']}") 
                    mikro_log.device_report("ONEHOST MODE -> Push result", [device['name']])
        else:
            logging.error (f"ONEHOST MODE -> SPECIFIC HOST not found {specific_device_name}")
        logging.info (f"ONEHOST MODE -> DONE ONE HOST - >{specific_device_name}")  

def control(specific_device_name,aux_ip=False):

    with open(f"{pathcontrol}/control.yml") as file:
        data_control = yaml.load(file, Loader=SafeLoader)

        if 'run_1_mikro_auto' in data_control.keys():
            if data_control['run_1_mikro_auto'] or specific_device_name:
                #Execute
                control_automation(data_control['mikro_auto_mode'],data_control['mikro_auto_dry_run'],specific_device_name,aux_ip)
            else:
                logging.warning (f"MAIN CONTROL->  ------------------------MIKRO AUTO DISABLED")   
        else:
            logging.warning (f"MAIN CONTROL->  ------------------------MIKRO AUTO NOT CONFIG START")   

#------------------------------------------EXEC START HERE:

#START AUTO EXECUTION

if __name__ == "__main__":
    target_device_env = os.environ.get("TARGET_DEVICE")
    
    if len(sys.argv) > 1:
        # Safe argument handling
        device_name = sys.argv[1]
        aux_ip = False
        if len(sys.argv) > 2:
            aux_ip = sys.argv[2]
        control(device_name, aux_ip)
    elif target_device_env and target_device_env.strip():
        # Support for usage via environment variable (useful for GitHub Actions)
        logging.info(f"GENERAL -> TARGET_DEVICE found in env: {target_device_env}")
        control(target_device_env, False)
    else:
        logging.info (f"\n ---- MIKRO-SDN START---- \n\n") 
        control(False)
