#LAUNCH THIS FILE TO START AUTOMATION.


#General Lib

from operator import truediv
from routeros_api import connect
from yaml.loader import SafeLoader
import yaml
import json
import sys
import os
import logging
from dotenv import load_dotenv

#Mikro-sdn Lib
import mikro_shared
import mikro_fw
import mikro_lan
import mikro_wan
import mikro_autoupdate
import mikro_internet
import mikro_wg
import mikro_netwatch
import mikro_docs

#Multitaslk Lib
from concurrent.futures import ThreadPoolExecutor
WORKERS_MAX = 20
MULTIMODE= True



error_counter = 0

load_dotenv()

pathconfig = os.environ.get("CONFIG")
pathsecrets = os.environ.get("SECRETS")
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
    logging.basicConfig(level=logging.DEBUG)
    prod=False
else:
    logging.basicConfig(level=logging.INFO)
    prod=False


def generateConfig ():
    logging.info("GENERAL -> ------------------------GENERATE CONFIG")

    logging.info ("GENERAL -> load inventory")
    myinventory=mikro_shared.loadInventory()

    #------ADD SDN TO DEVICES
    logging.info ("GENERAL -> Prepare SDN wan info")
    for device in myinventory:
        mikro_shared.prepareSDN(device)

    #------PREPARE GLOBAL WAN CONFIG
    logging.info ("GENERAL -> Generate wan Config")
    wanconfig=mikro_wan.loadWan(myinventory)

    logging.info ("GENERAL -> Generate device config")
    for device in myinventory:
        if not device['cleanconfig']:
            if device['role'] in managed_roles:

                globalconfig = []
                globalfwconfig = []

                logging.info (f"\n\n{device['name']} --> Generate config for: ---> {device['configlet']}")
                
                #------------FW
                if 'fw' in device['configlet']:        

                    #Load Global FW config
                    myconfig=mikro_shared.loadConfig('global',"firewall")
                    globalfwconfig.extend(myconfig)

                    #Load specific device FW config
                    if  os.path.exists(f"{pathconfig}/firewall/{device['name']}"):
                        myconfig=mikro_shared.loadConfig(device['name'],"firewall")
                        globalfwconfig.extend(myconfig)
                    else:
                        logging.warning (f"{device['name']} --> Warning No specific FW config ")

                #------------General config
                if 'general' in device['configlet']:
                    myconfig=mikro_shared.loadConfig(device['role'],"general")
                    globalconfig.extend(myconfig)

                #------------LAN ROLE (bridge and vlans)
                if 'lan' in device['configlet']:
                    myconfig=mikro_lan.loadConfig(device,myinventory)
                    globalconfig.extend(myconfig)

                #------------WAN (wireguard, bgp)
                if 'wan' in device['configlet']:
                    if device['name'] in wanconfig.keys():
                        myconfig=wanconfig[device['name']]
                        globalconfig.extend(myconfig)

                #------------DHCP leases 
                if 'dhcp' in device['configlet']:
                    myconfig=mikro_shared.loadConfigByDevice("ipv4","dhcp",device['name'])
                    globalconfig.extend(myconfig)

                #------------autoupdate
                if 'autoupdate' in device['configlet']:
                    myconfig=mikro_autoupdate.loadConfig(device)
                    globalconfig.extend(myconfig)            

                #------------INTERNET
                if 'internet' in device['configlet']:
                    myconfig=mikro_internet.loadConfig(device)
                    globalconfig.extend(myconfig)    

                #------------WG VPN
                if 'wg_vpn' in device['configlet']:
                    myconfig=mikro_wg.loadConfig(device)
                    globalconfig.extend(myconfig)  

                #------------NETWATCH ROLE 
                if 'netwatch' in device['configlet']:
                    myconfig=mikro_netwatch.loadConfig(device)
                    globalconfig.extend(myconfig)  


                #------------FILTER DUPLICATED
                #Is expected automation create duplicated objets like bgp filters this help to just implement them once
                globalconfig = mikro_shared.filterDuplicatedConfigRules(globalconfig)

                #------------ORGANICE

                #copy from global to global fw fw rules
                for item in globalconfig:
                    if item['resource'] == '/ip/firewall/filter' or item['resource'] == '/ipv6/firewall/filter'  or item['resource'] == '/ip/firewall/nat'  or item['resource'] == '/ip/firewall/mangle' or item['resource'] == '/ipv6/firewall/mangle' :
                        globalfwconfig.append(item)

                #Remove from glboal config all FW rules. They are already copy to globalfwconfig
                globalconfig2=[]
                for item in globalconfig:
                    if item['resource'] != '/ip/firewall/filter' and item['resource'] != '/ipv6/firewall/filter' and item['resource'] != '/ip/firewall/nat' and item['resource'] != '/ip/firewall/mangle' and item['resource'] != '/ipv6/firewall/mangle' :
                        globalconfig2.append(item)
                globalconfig = globalconfig2

                #----------------SAVE PROPOSED CONFIG
                #Check if folder exist

                if not os.path.exists(f"{pathsecrets}/proposed/"):
                    os.makedirs(f"{pathsecrets}/proposed/")
                if not os.path.exists(f"{pathsecrets}/old_proposed/"):
                    os.makedirs(f"{pathsecrets}/old_proposed/")

                #if file exist move to old proposed
                if  os.path.exists(f"{pathsecrets}/proposed/{device['name']}_fw.json"):
                    os.replace(f"{pathsecrets}/proposed/{device['name']}_fw.json", f"{pathsecrets}/old_proposed/{device['name']}_fw.json")

                if  os.path.exists(f"{pathsecrets}/proposed/{device['name']}_global.json"):
                    os.replace(f"{pathsecrets}/proposed/{device['name']}_global.json", f"{pathsecrets}/old_proposed/{device['name']}_global.json")

                #Save config file
                with open (f"{pathsecrets}/proposed/{device['name']}_fw.json", 'w') as file1:
                    json.dump(globalfwconfig, file1)
                    file1.close()

                with open (f"{pathsecrets}/proposed/{device['name']}_global.json", 'w') as file2:
                    json.dump(globalconfig, file2)
                    file2.close()

                #----------------SAVE PROPOSED CONFIG for humans
                with open (f"{pathsecrets}/proposed/{device['name']}_fw.yml", 'w') as file1:
                    yaml.dump(globalfwconfig, file1)
                    file1.close()

                with open (f"{pathsecrets}/proposed/{device['name']}_global.yml", 'w') as file2:
                    yaml.dump(globalconfig, file2)
                    file2.close()

                #----------------SAVE PROPOSED CONFIG markdown and html

                mikro_docs.createDocs(device)

    logging.debug (f"Config generation DONE \n\n")


def cleanConfig (device,mode,dryrun):
    #Read file
    if device['push_clean']:
        mikro_shared.prepareSDN(device)
        if device['cleanconfig']:
            globalconfig=[]
            globalfwconfig=[]
        else:
            with open(f"{pathsecrets}/proposed/{device['name']}_fw.json") as file1:
                globalfwconfig = json.load(file1)
                file1.close()

            with open(f"{pathsecrets}/proposed/{device['name']}_global.json") as file2:
                globalconfig = json.load(file2)
                file2.close()

        #------------login
        connected = False
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
                mikro_docs.dryrun_add(f"###Clean firewall Rules \n")
                mikro_fw.cleanConfig(api_device,globalfwconfig,dryrun,device)
            if mode == 'global':
                mikro_docs.dryrun_add(f"###Clean General confing \n")
                mikro_shared.cleanConfig(api_device,globalconfig,dryrun,device)
            logging.info (f"{device['name']} -> OK clean")

def pushConfig (device,mode,dryrun):
    #Read file
    if device['push_config'] and not device['cleanconfig']:
        mikro_shared.prepareSDN(device)

        with open(f"{pathsecrets}/proposed/{device['name']}_fw.json") as file1:
            globalfwconfig = json.load(file1)
            file1.close()

        with open(f"{pathsecrets}/proposed/{device['name']}_global.json") as file2:
            globalconfig = json.load(file2)
            file2.close()

        #------------login
        connected = False
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

                mikro_docs.dryrun_add(f"###Push general config \n")
                mikro_shared.proccessConfig(api_device,globalconfig,device,dryrun)  
            if mode == 'firewall' or mode == 'global':

                mikro_docs.dryrun_add(f"###Push firewall rules \n")
                mikro_fw.proccessFWRules(api_device,globalfwconfig,dryrun,device)
            logging.info (f"{device['name']} -> OK push")
    else:
        logging.info (f"{device['name']} -> Push Disabled")

def cleanAndPush(device,mode,dryrun):

    if device['role'] in managed_roles:
        if dryrun:
            mikro_docs.dryrun_add(f"##SIMULATION DRY RUN\n")
        else:
            mikro_docs.dryrun_add(f"##PUSH MODE REAL\n")
            mikro_docs.dryrun_add(f"##DEVICE {device['name']}\n")
        cleanConfig(device,mode,dryrun)
        pushConfig(device,mode,dryrun)

    return True

#This path use all the automation to create all and push
def controlAutomation(mode,dryrun,specific_device_name):

    logging.info (f"GENERAL -> ------------------------AUTOMATION LOAD INVENTORY") 
    myinventory=mikro_shared.loadInventory()

    if not specific_device_name:
        #Create minimun needed files
        logging.info (f"GENERAL -> ------------------------CREATE FILES") 
        #CREATE FILE STRUCTURE
        mikro_shared.filesCreation()
        if  mode == 'config':    
            logging.warning (f"GENERAL -> MODE JUST CONFIG") 
        #GENERATE CONFIGS
        if mode == 'firewall' or mode == 'global' or mode == 'config':
            generateConfig ()

        #PUSH CONFIGS
        #if mode config we do not push
        if mode == 'firewall' or mode == 'global':

            if MULTIMODE:
                logging.info (f"GENERAL -> PUSH MODE MULTI THREAD") 
                #-------------MULTI TASK
                with ThreadPoolExecutor(max_workers=WORKERS_MAX) as executor:
                    for i in range(0, len(myinventory), WORKERS_MAX):
                        batch = myinventory[i:i+WORKERS_MAX]
                        futures = [executor.submit(cleanAndPush, device, mode, dryrun  ) for device in batch]
                        # Wait for all tasks in the current batch to complete
                        for future in futures:
                            future.result()

            else:
                #-------------SINGLE TASK
                logging.info (f"GENERAL -> PUSH MODE SINGLE THREAD") 
                for device in myinventory:

                        cleanAndPush(device,mode,dryrun)


        #----------------GENERATE MARKDOWN AND HTML
        logging.info (f"GENERAL -> Start Creating DOCS")    
        mikro_docs.createExternal()
        #Save globals
        mikro_docs.saveGlobal()
        #Safe dryrun
        mikro_docs.saveDryrun()
        logging.info (f"GENERAL -> DONE Creating DOCS")  


        logging.info (f"GENERAL -> ------------------------AUTOMATION END MIKRO AUTO")    
    else:
        logging.info (f"ONEHOST MODE -> START ONE HOST - >{specific_device_name} ")  
        #find device
        target_device = None
        for device in myinventory:
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
                    cleanAndPush(device,mode,dryrun)    
                    logging.info (f"ONEHOST MODE -> OK -> {device['name']}") 
        else:
            logging.error (f"ONEHOST MODE -> SPECIFIC HOST not found {specific_device_name}")
        logging.info (f"ONEHOST MODE -> DONE ONE HOST - >{specific_device_name}")  

def control(specific_device_name):

    with open(f"{pathcontrol}/control.yml") as file:
        data_control = yaml.load(file, Loader=SafeLoader)

        if 'run_1_mikro_auto' in data_control.keys():
            if data_control['run_1_mikro_auto'] or specific_device_name:
                #Execute
                controlAutomation(data_control['mikro_auto_mode'],data_control['mikro_auto_dryrun'],specific_device_name)
            else:
                logging.warning (f"MAIN CONTROL->  ------------------------MIKRO AUTO DISABLED")   
        else:
            logging.warning (f"MAIN CONTROL->  ------------------------MIKRO AUTO NOT CONFIG START")   

#------------------------------------------EXEC START HERE:

#START AUTO EXECUTION

if __name__ == "__main__":
    if len(sys.argv) > 1:
        control(sys.argv[1])
    else:
        logging.info (f"\n ----MIKRO SDN NETWORK-AUTOMATION START---- \n\n") 
        control(False)
