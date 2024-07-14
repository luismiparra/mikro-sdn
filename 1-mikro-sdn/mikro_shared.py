from asyncio import format_helpers
import os
from pickle import TRUE
from typing import Counter
from dotenv import load_dotenv
import yaml
from yaml.loader import SafeLoader
import logging
import routeros_api
import ssl
import ipaddress
import sys
import json
from jinja2 import Environment, FileSystemLoader
import mikro_docs

STOP_ON_ERROR = TRUE
CSS_STYLE = "css1.j2"

load_dotenv()

pathconfig = os.environ.get("CONFIG")
list_localstring = json.loads(os.environ.get("LOCALSTRING"))
micro_user = os.environ.get("MIKRO_USER")
micro_pass = os.environ.get("MIKRO_PASSWORD")
pathsecrets = os.environ.get("SECRETS")
pathweb = os.environ.get("WEB")




def filesCreation():
    if not os.path.exists(f"{pathsecrets}"):
        os.makedirs(f"{pathsecrets}")
    #Create file if not exist
    if not os.path.exists(f'{pathsecrets}/secrets.json'):
        with open (f'{pathsecrets}/secrets.json', 'w') as file:
            json.dump({}, file)
            file.close()
    if not os.path.exists(f'{pathsecrets}/external/external.json'):
        with open (f'{pathsecrets}/secrets.json', 'w') as file:
            json.dump({}, file)
            file.close()
    if not os.path.exists(f'{pathsecrets}/external/external.yml'):
        with open (f'{pathsecrets}/secrets.json', 'w') as file:
            yaml.dump({}, file)
            file.close()

    #Create the folder if not exist
    if not os.path.exists(f"{pathsecrets}/external_export"):
        os.makedirs(f"{pathsecrets}/external_export")
        
    if not os.path.exists(f"{pathsecrets}/mgmt_export"):
        os.makedirs(f"{pathsecrets}/mgmt_export")

    if not os.path.exists(f"{pathweb}"):
        os.makedirs(f"{pathweb}")

    if not os.path.exists(f"{pathsecrets}/vpnconfig"):
        os.makedirs(f"{pathsecrets}/vpnconfig")

    if not os.path.exists(f"{pathsecrets}/external"):
        os.makedirs(f"{pathsecrets}/external")

    #Copy CSS to web

    file_loader = FileSystemLoader("templates")
    env =Environment(loader=file_loader)

    template = env.get_template(CSS_STYLE)
    mycss = template.render()

    with open (f"{pathweb}/style.css", 'w') as file1:
        file1.write(mycss)
        file1.close()       

    

#Get config by a tag, requiere   device config, resource, search, and tag or search
def getRunningBy(runningConfig,resource,search,tag):
    if resource in runningConfig.keys():
        for router_item in runningConfig[resource]:
            #We can have default objects withouth the search tag on them
            if tag in router_item.keys():
                if router_item[tag] == search:
                    return router_item
        return False
    else:
        return False


def needAnUpdate (item,router_item,device):
    #We check if has an ID if not automatically need and update
    if 'id' in router_item.keys():
        #Id found now check for all keys in desing config (item)
        for itemkey in item.keys():
            #exclude non config tags
            if itemkey != 'use_set' and itemkey !='resource' and itemkey !='order' and itemkey !='posi':
                #if not key in running check moving the dash
                if not itemkey in router_item.keys():
                    altitemkey=itemkey.replace('_','-')
                    #if not key in running after mooving the dash
                    if altitemkey in router_item.keys():
                        #CHECK PARAMETER WITH  DASH
                        if item[itemkey] != router_item[altitemkey]:
                            logging.info (f"{device['name']} -> A_Update needed at {item['resource']} -> {itemkey} --- candidate parameter: -> {item[itemkey]} --- run parameter -> {router_item[altitemkey]} ")
                            item['id'] = router_item['id']
                            return True
                    else:
                        logging.debug (f"{device['name']} -> Possible new tag on item or Error with key in --- Context: {item['resource']} --- candidate parameter: -> {item[itemkey]} ")
                        return True
                else:
                    #CHECK PARAMETER WIHOUTH DASH
                    if item[itemkey] != router_item[itemkey]:
                        logging.info (f"{device['name']} -> B_Update needed at {item['resource']} -> {itemkey} -> --- candidate parameter: -> {item[itemkey]} --- run parameter -> {router_item[itemkey]} ")
                        item['id'] = router_item['id']
                        return True
        #At this point all keys check and no need to update
        return False
    else:
        #no id allways updated
        item['id'] = None
        return True

def getRunningConfig(api,config_rules,device):
    ##CACHE DEVICE STAUTS FIRST

    listOfResources = []

    #Get all needed resources according to config
    for item in config_rules:
        #if 'resource' in item.keys():
        if not item['resource'] in listOfResources:
            listOfResources.append(item['resource'])

    #Save all data in running Config
    runningConfig = {}
    for resource in listOfResources:
        try:
            runningConfig[resource] = api.get_resource(resource).get()

        except Exception as unknown_error:
            logging.error (f"{device['name']} -> Error getting running config resource: {resource} --- {unknown_error} ---")
            #errorStop() 
            return False

    
    return runningConfig

def removeDuplicatesInRunning(api,config_rules,dryrun,device):

    if dryrun:
        mikro_docs.dryrun_add(f"#### DUPLICATED IN RUNNING: \n")

    #-INFO is not expected to have duplicated in running but with the system of getting running.
    runningConfig = getRunningConfig(api,config_rules,device)

    for resource_key in runningConfig.keys():
        for item1 in runningConfig[resource_key]:
            for item2 in runningConfig[resource_key]:
                #Check if valid to find duplicates (just with id and comment)
                if 'id'in item1.keys() and 'id'in item2.keys() and 'comment'in item1.keys() and 'comment'in item2.keys():
                    if item1['id'] != item2['id'] and item1['comment'] == item2['comment']:
                        
                        #--- Item with dynamic tags:
                        if 'dynamic' in item1.keys() and 'dynamic' in item2.keys():
                            if item1['dynamic'] == 'true' and item2['dynamic'] == 'true':
                                #Ignore the duplicate due generated dynamic
                                pass
                            else:
                                logging.error(f"{device['name']} -> Duplicated in Running found --- item1: {item1} --- {item2} --- REMOVING ITEM 2")
                                if not dryrun:
                                    api.get_resource(resource_key).remove(id=item2['id'])
                                    #refresh running config after remove
                                    runningConfig = getRunningConfig(api,config_rules,device)
                                else:
                                    mikro_docs.dryrun_add(f"- REMOVE DUPLICATE IN RUNNING.  resource \n \t - {resource_key} item \n \t - {item2} \n")
                                    
                        #--- Item without dynamic tags:
                        else:
                            logging.error(f"{device['name']} -> Duplicated in Running found --- item1: {item1} --- {item2} --- REMOVING ITEM 2")
                            if not dryrun:
                                api.get_resource(resource_key).remove(id=item2['id'])
                                #refresh running config after remove
                                runningConfig = getRunningConfig(api,config_rules,device)
                            else:
                                mikro_docs.dryrun_add(f"- REMOVE DUPLICATE IN RUNNING.  resource \n \t - {resource_key} item \n \t - {item2} \n")

def filterDuplicatedConfigRules(config_rules):

    #-INFO is expected to have some duplicated rules generated by automation.
    filtered_config_rules = []

    for item1 in config_rules:
        if 'comment'in item1.keys():
            not_item_in_list = True
            for item2 in filtered_config_rules:
                if 'comment'in item2.keys():
                    if item1['comment'] == item2['comment']:
                        not_item_in_list = False
                        break
            if not_item_in_list:
                filtered_config_rules.append(item1)
        else:
            filtered_config_rules.append(item1)

    return filtered_config_rules

def proccessConfig(api,config_rules,device,dryrun):


    runningConfig = getRunningConfig(api,config_rules,device) 

    for item in config_rules:

        #Check if config has a comment
        ignoreupdate =  False  #flag for custom items to disable update

        if 'comment' in item.keys():
            router_item = getRunningBy(runningConfig,item['resource'],item['comment'],'comment')
            if router_item:
                if needAnUpdate(item,router_item,device):
                    if not dryrun:
                        newUpdateConfig(api,item,router_item,device)
                    mikro_docs.dryrun_add(f"- UPDATE config.   \n \t - local_item --> {item}  \n \t - router_item --> {router_item} \n")
            else:
                if not dryrun:
                    addConfig(api.get_resource(item['resource']),item,device)
                mikro_docs.dryrun_add(f"- ADD config.  \n \t - resource --> {item['resource']}  \n \t - local_item --> {item} \n")
        else:
            if item['use_set']:
                if 'name' in item.keys():
                    router_item = getRunningBy(runningConfig,item['resource'],item['name'],'name')
                    #If we get the item by name
                    if router_item:

                        #Exceptions start---------------

                        #---IP service remove name
                        if item['resource']=="/ip/service":
                            item.pop('name',None)

                        #Exceptions end---------------
                        if needAnUpdate(item,router_item,device):
                            if not dryrun:
                                newUpdateConfig(api,item,router_item,device)
                            #This is always updated no dry run
                            #mikro_docs.dryrun_add(f"- UPDATE config.   \n \t - local_item --> {item}  \n \t - router_item --> {router_item} \n")
                    else:
                        #we force the update if no name and no comment
                        if not dryrun:
                            newUpdateConfig(api,item,None,device)
                        #This is always updated no dry run
                        #mikro_docs.dryrun_add(f"- UPDATE config.   \n \t - local_item --> {item}\n")
                
                else:

                    #Exceptions ---------------

                    #---SNMP device name
                    if item['resource']=="/snmp":
                        item['location'] = device['location']                    
                    #---Identity 
                    if item['resource']=="/system/identity":
                        item['name'] = device['name']

                    #---netlow source ip
                    if item['resource']=="/ip/traffic-flow/target":
                        #We add source address
                        item['src-address'] = str(device['gatewayv4_list'][int(item['vlan_src'])])
                        item.pop('vlan_src',None)

                        #Determine if update or add based on number and not comment
                        netlow_rule = api.get_resource(item['resource']).get()
                        if not netlow_rule:
                            ignoreupdate = True
                            #not numbers allow in add
                            item.pop('numbers',None)
                            if not dryrun:
                                addConfig(api.get_resource(item['resource']),item,device)
                            mikro_docs.dryrun_add(f"- ADD config.  \n \t - resource --> {item['resource']}  \n \t - local_item --> {item} \n")
                    
                    #---system logging
                    if item['resource']=="/system/logging":
                        logging_rule = api.get_resource(item['resource']).get(action=item['action'])
                        if not logging_rule:
                            ignoreupdate = True
                            item.pop('numbers',None)
                            if not dryrun:
                                addConfig(api.get_resource(item['resource']),item,device)
                            mikro_docs.dryrun_add(f"- ADD config.  \n \t - resource --> {item['resource']}  \n \t - local_item --> {item} \n")

                    #---system logging actions
                    if item['resource']=="/system/logging/action":
                        item['src-address'] = str(device['gatewayv4_list'][int(item['vlan_src'])])
                        item.pop('vlan_src',None)

                    #Exceptions end---------------

                    if not ignoreupdate:
                        if not dryrun:
                            newUpdateConfig(api,item,None,device)
                        #This is always updated no dry run
                        #mikro_docs.dryrun_add(f"- UPDATE config.   \n \t - local_item --> {item}\n")
            else:
                logging.error(f"{device['name']} -> Error adding or Updating item. No comment and no use_set ---  {item}")
                errorStop() 

    #Set ipv6 status
    if device['disable-ipv6'] == 'yes':
        mydict={}
        mydict['resource'] = '/ipv6/settings'
        mydict['disable_ipv6'] = "yes"
        if not dryrun:
            newUpdateConfig(api,mydict,None,device)
        mikro_docs.dryrun_add(f"- UPDATE config.   \n \t - local_item --> {item}\n")
    else:
        mydict={}
        mydict['resource'] = '/ipv6/settings'
        mydict['disable_ipv6'] = "no"
        if not dryrun:
            newUpdateConfig(api,mydict,None,device)
        mikro_docs.dryrun_add(f"- UPDATE config.   \n \t - local_item --> {item}\n")

    removeDuplicatesInRunning(api,config_rules,dryrun,device)

def addConfig(api,item,device):

    #Get the resource to log in case of error
    localresource = item['resource']

    item.pop('use_set',None)
    item.pop('resource',None)

    try:
        api.add(**item)
        item['resource'] = localresource
    except Exception as unknown_error:
        logging.error (f"{device['name']} -> ADD cfg rule Error IN  {item} PATH {localresource} ---  {unknown_error}")
        item['resource'] = localresource
        #errorStop() 
        return False
    return True

def newUpdateConfig(api,item,router_item,device):

    #Remove custom tags

    if 'posi' in item.keys():
        localposi=item['posi']
        item.pop('posi',None)
    else:
        localposi=None

    localresource = item['resource']
    
    item.pop('use_set',None)
    item.pop('resource',None)  
    if 'order' in item.keys():
        item.pop('order',None)  
    
    #We specify what item to update in case include id
    if router_item:
        item['id'] = router_item['id']
    #Update resource
    try:
        api.get_resource(localresource).set(**item)
    except Exception as unknown_error:
        logging.error (f"{device['name']} -> UPDATE error on item   {item} PATH {localresource} ---  {unknown_error}")
        item['resource'] = localresource
        item['posi'] = localposi
        #errorStop() 
        return False

    #Re add custom tags
    item['resource'] = localresource
    item['posi'] = localposi

def connectionName(name1,name2):
    option1 = f"{name1}__{name2}"
    option2 = f"{name2}__{name1}"
    list = [option1,option2]
    list.sort()

    return list[0]

def login(myuser, mypassword, device_ip, device):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.set_ciphers('ADH:@SECLEVEL=0')
        connection = routeros_api.RouterOsApiPool(
            device_ip,
            username=myuser,
            password=mypassword,
            port=8729,
            use_ssl=True,
            ssl_context=ctx,
            plaintext_login=True
        )
        api = connection.get_api()
        return api
    except ConnectionError:
        logging.warning(f"{device['name']} -> Connection has either been refused, or the host is unreachable. Check if API is exposed on device.")
        return False
    except Exception as unknown_error:
        logging.warning(f"{device['name']} -> Error connecting to {device_ip} ---> {unknown_error}")
        return False

def loadConfig(roleconfig,resourceconfig):
    #Create list
    list=[]

    #Load all files config
    for filename in os.listdir(f"{pathconfig}/{resourceconfig}/{roleconfig}"):
        #Open each file and load data
        with open(f"{pathconfig}/{resourceconfig}/{roleconfig}/{filename}") as file:
            data = yaml.load(file, Loader=SafeLoader)
            #For each key in yml
            for key in data:
                for rule in data[key]:
                    rule['resource']=key
                    #Check if duplicated rule by comment
                    #First determine if comment is key or use_set since both can not exist at same time
                    if 'comment' in rule.keys():
                        if objectExists(list,rule['comment']):
                            logging.warning (f"Duplicated rule in config comment -> {rule['comment']}")
                        else:
                            list.append(rule)
                    elif 'use_set' in rule.keys():
                        if rule['use_set']:
                            list.append(rule)

    return list

def loadConfigByDevice(roleconfig,resourceconfig,name):
    #Create list
    list=[]

    #Load all files config
    for filename in os.listdir(f"{pathconfig}/{resourceconfig}/{roleconfig}/{name}"):
        #Open each file and load data
        with open(f"{pathconfig}/{resourceconfig}/{roleconfig}/{name}/{filename}") as file:
            data = yaml.load(file, Loader=SafeLoader)
            #For each key in yml
            for key in data:
                for rule in data[key]:
                    rule['resource']=key

                    #If not use set we just set to false
                    if not 'use_set' in rule.keys():
                        rule['use_set'] = False

                    #Check if duplicated rule by comment
                    #First determine if comment is key or use_set since both can not exist at same time

                    if 'comment' in rule.keys():
                        if objectExists(list,rule['comment']):
                            print (f"Duplicated rule in config comment -> {rule['comment']}")
                        else:
                            list.append(rule)
                    elif 'use_set' in rule.keys():
                        if rule['use_set']:
                            list.append(rule)
    return list

def loadInventory():
    #Create list
    list=[]

    #Load all files config
    for filename in os.listdir(f"{pathconfig}/inventory"):
        #Open each file and load data
        with open(f"{pathconfig}/inventory/{filename}") as file:
            data = yaml.load(file, Loader=SafeLoader)
            #For each key in yml
            for key in data:
                for rule in data[key]:
                    rule['role']=key
                    list.append(rule)
    return list    

def objectExists(list, comment):
    for item in list:
        if "comment" in item.keys():
            if item['comment'] == comment:
                return True
    return False

def objectExistsAddrList(list, comment):
    #list is the config   and comment is the remix comment with list_ip
    for item in list:
        if 'address' in item.keys():
            for addr in item['address']:
                if f"{item['comment']}_{addr}" == comment:
                    return True
    return False

def cleanConfig(api,config_rules,dryrun,device):

    with open(f"{pathconfig}/clean_routes.yml") as file:
        cleanroutes = yaml.load(file, Loader=SafeLoader)
        file.close()

    #we search for keys that exist in config to clean them
    for key in cleanroutes:
        try:
            for item in api.get_resource(key).get():
                if not "comment" in item.keys():
                    if 'default' in item.keys():
                        if item['default'] == 'false':  #We can not remove default objets
                            logging.info (f"{device['name']} ->  Found config without comment. Removing -> {key} -> {item}")
                            if not dryrun:
                                api.get_resource(key).remove(id=item['id'])
                            mikro_docs.dryrun_add(f"- REMOVING No comment. \n \t - item {item} \n")
                    else:
                        if 'dynamic' in item.keys():
                            if item['dynamic'] == 'false':  #We can not remove dynamic objets
                                logging.info (f"{device['name']} -> Found config without comment. Removing -> {key} -> {item}")
                                if not dryrun:
                                    api.get_resource(key).remove(id=item['id'])
                                mikro_docs.dryrun_add(f"- REMOVING No comment. \n \t - item {item} \n")
                        else:
                            if not 'default-name' in item.keys():  #we can not remove items with default name
                                logging.info (f"{device['name']} -> Found config without comment. Removing -> {key} -> {item}")
                                if not dryrun:
                                    api.get_resource(key).remove(id=item['id'])
                                mikro_docs.dryrun_add(f"- REMOVING No comment. \n \t - item {item} \n")

                elif not objectExists(config_rules,item['comment']):
                    #Verify if need to exclude item
                    item_excluded =  False
                    for localstring in list_localstring:
                        if localstring in item['comment']:
                            item_excluded = True
                    if item_excluded:
                        logging.debug (f"{device['name']} -> Rule not at config excluded from removal -> {item}")
                    else:
                        if 'default' in item.keys():
                            if item['default'] == 'false':  #We can not remove default objets
                                logging.info (f"{device['name']} -> No default Found rule not at the config, removing -> {item}")
                                if not dryrun:
                                    api.get_resource(key).remove(id=item['id'])
                                mikro_docs.dryrun_add(f"- REMOVING No config. \n \t - item {item} \n")
                        else:
                            if 'builtin' in item.keys():
                                if item['builtin'] == 'false':
                                    logging.info (f"{device['name']} -> no builtin Found rule not at the config, removing -> {item}")
                                    if not dryrun:
                                        api.get_resource(key).remove(id=item['id'])
                                    mikro_docs.dryrun_add(f"- REMOVING No config. \n \t - item {item} \n")
                            else:
                                if not 'default-name' in item.keys():  #we can not remove items with default name     
                                #We can not remove dinamic
                                    if 'dynamic' in item.keys():
                                        if item['dynamic'] == 'false':
                                            logging.info (f"{device['name']} -> no default-name and not dynamic Found rule not at the config, removing -> {item}")
                                            if not dryrun:
                                                api.get_resource(key).remove(id=item['id'])
                                            mikro_docs.dryrun_add(f"- REMOVING No config. \n \t - item {item} \n")
                                    else:
                                            logging.info (f"{device['name']} -> no default-name Found rule not at the config last rule, removing -> {item}")
                                            if not dryrun:
                                                api.get_resource(key).remove(id=item['id'])
                                            mikro_docs.dryrun_add(f"- REMOVING No config. \n \t - item {item} \n")
                                else:
                                    #Item with default name, we can not remove it
                                    pass

        except Exception as unknown_error:
            ignore_keys = ['/interface/wireless','/user-manager/user']
            if key in ignore_keys:
                logging.debug  (f"{device['name']} -> No path in cleaning path: {key } ---  {unknown_error}")
            else:
                logging.error (f"{device['name']} -> Error cleaning path: {key } ---  {unknown_error}")
                #errorStop() 
            return False        

def prepareSDN (device):

    #-----------JUST IF LAN
    if 'lan' in device.keys() or 'wg_vpn' in device.keys():
        numbersubnets=250
        numbersubnets+=1

        #---------IPV4

        myvar = (ipaddress.ip_network(device['subnetv4']).subnets(8))

        subnetsv4 = []
        gatewayv4 = []

        limit=0
        for i in myvar:
            subnetsv4.append(i)
            gatewayv4.append( (ipaddress.IPv4Network(i)[device['gateway_number']]) )
            limit+=1
            if limit >= numbersubnets:
                break

        #---------IPV6
        myvar = (ipaddress.ip_network(device['subnetv6']).subnets(16))

        subnetsv6 = []
        gatewayv6 = []

        limit=0
        for i in myvar:
            subnetsv6.append(i)
            gatewayv6.append( (ipaddress.IPv6Network(i)[device['gateway_number']]) )
            limit+=1
            if limit > numbersubnets:
                break
        
        #---------IPV6_SLAAC
        myvar = (ipaddress.ip_network(device['subnetv6slaac']).subnets(11))

        subnetsv6slaac = []
        gatewayv6slaac = []

        limit=0
        for i in myvar:
            subnetsv6slaac.append(i)
            gatewayv6slaac.append( (ipaddress.IPv6Network(i)[device['gateway_number']]) )
            limit+=1
            if limit > numbersubnets:
                break


        device['subnetsv4_list'] = subnetsv4
        device['gatewayv4_list'] = gatewayv4

        device['subnetsv6_list'] = subnetsv6
        device['gatewayv6_list'] = gatewayv6

        device['subnetsv6slaac_list'] = subnetsv6slaac
        device['gatewayv6slaac_list'] = gatewayv6slaac

    #-----------GLOBAL TO ALL HOST

    #---------IPV4_TRANSIT

    numbersubnetstransit=250+1
    mytransitnet=""
    myvar = (ipaddress.ip_network(device['subnetv4']).subnets(8))

    limit=0
    for i in myvar:
        limit+=1
        if limit >= numbersubnetstransit:
            mytransitnet=i
            break

    numbersubnetstransit=64
    myvar2 = (ipaddress.ip_network(mytransitnet).subnets(6))

    subnet_transitv4 = []
    subnet_transitv4_dict = []

    limit=0
    for i in myvar2:
        subnet_transitv4.append(i)
        limit+=1
        if limit >= numbersubnetstransit:
            break    
    
    for i in range (0, len(subnet_transitv4)):
        transit_host = {}
        ip_gen = subnet_transitv4[i].hosts()
        myip1 = next(ip_gen)
        myip2 = next(ip_gen)
        transit_host['subnet'] = subnet_transitv4[i]
        transit_host['ip1'] = myip1
        transit_host['ip2'] = myip2
        subnet_transitv4_dict.append(transit_host)

    #---------IPV6_TRANSIT

    numbersubnetstransit=250+1
    mytransitnet=""
    myvar = (ipaddress.ip_network(device['subnetv6']).subnets(16))

    limit=0
    for i in myvar:
        limit+=1
        if limit >= numbersubnetstransit:
            mytransitnet=i
            break

    numbersubnetstransit=64
    myvar2 = (ipaddress.ip_network(mytransitnet).subnets(15))

    subnet_transitv6 = []
    subnet_transitv6_dict = []

    limit=0
    for i in myvar2:
        subnet_transitv6.append(i)
        limit+=1
        if limit >= numbersubnetstransit:
            break    
    
    for i in range (0, len(subnet_transitv6)):
        transit_host = {}
        ip_gen = subnet_transitv6[i].hosts()
        myip1 = next(ip_gen)
        myip2 = next(ip_gen)
        transit_host['subnet'] = subnet_transitv6[i]
        transit_host['ip1'] = myip1
        transit_host['ip2'] = myip2
        subnet_transitv6_dict.append(transit_host)

 #---------IPV4_TRANSIT_2

    numbersubnetstransit=250+2
    mytransitnet=""
    myvar = (ipaddress.ip_network(device['subnetv4']).subnets(8))

    limit=0
    for i in myvar:
        limit+=1
        if limit >= numbersubnetstransit:
            mytransitnet=i
            break

    numbersubnetstransit=64
    myvar2 = (ipaddress.ip_network(mytransitnet).subnets(6))

    subnet_transitv4 = []
    subnet_transitv4_dict_2 = []

    limit=0
    for i in myvar2:
        subnet_transitv4.append(i)
        limit+=1
        if limit >= numbersubnetstransit:
            break    
    
    for i in range (0, len(subnet_transitv4)):
        transit_host = {}
        ip_gen = subnet_transitv4[i].hosts()
        myip1 = next(ip_gen)
        myip2 = next(ip_gen)
        transit_host['subnet'] = subnet_transitv4[i]
        transit_host['ip1'] = myip1
        transit_host['ip2'] = myip2
        subnet_transitv4_dict_2.append(transit_host)

    #---------IPV6_TRANSIT_2

    numbersubnetstransit=250+2
    mytransitnet=""
    myvar = (ipaddress.ip_network(device['subnetv6']).subnets(16))

    limit=0
    for i in myvar:
        limit+=1
        if limit >= numbersubnetstransit:
            mytransitnet=i
            break

    numbersubnetstransit=64
    myvar2 = (ipaddress.ip_network(mytransitnet).subnets(15))

    subnet_transitv6 = []
    subnet_transitv6_dict_2 = []

    limit=0
    for i in myvar2:
        subnet_transitv6.append(i)
        limit+=1
        if limit >= numbersubnetstransit:
            break    
    
    for i in range (0, len(subnet_transitv6)):
        transit_host = {}
        ip_gen = subnet_transitv6[i].hosts()
        myip1 = next(ip_gen)
        myip2 = next(ip_gen)
        transit_host['subnet'] = subnet_transitv6[i]
        transit_host['ip1'] = myip1
        transit_host['ip2'] = myip2
        subnet_transitv6_dict_2.append(transit_host)

    device['subnet_transitv4'] = subnet_transitv4_dict
    device['subnet_transitv6'] = subnet_transitv6_dict

    device['subnet_transit_core_v4'] = subnet_transitv4_dict_2
    device['subnet_transit_core_v6'] = subnet_transitv6_dict_2

    return device

def errorStop():
    debugmode = os.environ.get("DEBUGMODE")
    if STOP_ON_ERROR:
        if debugmode:
            input(f"Errors detected press enter to continue or ctl+c to cancel")
        else:
            sys.exit('Error detected stoping execution')

#----------------------------DEPRECATED 

def updateConfig(api,item,myid):
    
    #Get object to determine if update is needed:
    needToUpdate = False
    if myid:
        routerConfig = api.get(id=myid)
        for itemkey in item.keys():
            if itemkey != 'use_set' and itemkey !='resource':
                if not itemkey in routerConfig[0].keys():
                    altitemkey=itemkey.replace('_','-')
                    if altitemkey in routerConfig[0].keys():

                        #CHECK PARAMETER WITH  DASH
                        if item[itemkey] != routerConfig[0][altitemkey]:
                            logging.debug (f"A_Update needed at {api} -> {itemkey} --- candidate parameter: -> {item[itemkey]} --- run parameter -> {routerConfig[0][altitemkey]} ")
                            needToUpdate = True
                    else:
                        logging.debug (f"Error with key in --- Context: {item} --- candidate parameter: -> {item[itemkey]} --- run parameter -> {routerConfig[0][altitemkey]} ")
                else:
                    #CHECK PARAMETER WIHOUTH DASH
                    if item[itemkey] != routerConfig[0][itemkey]:
                        logging.debug (f"B_Update needed at {api} -> {itemkey} -> --- candidate parameter: -> {item[itemkey]} --- run parameter -> {routerConfig[0][itemkey]} ")
                        needToUpdate = True
    else:
        #no id allways updated
        needToUpdate = True 

    if needToUpdate:
        #Get the resource to log in case of error
        localresource = item['resource']
        if myid != None:
            item['id'] = myid

        item.pop('use_set',None)
        item.pop('resource',None)  

        try:
            api.set(**item)
            item['resource'] = localresource

        except Exception as unknown_error:
            logging.error (f"UPDATE cfg rule Error IN  {item} PATH {localresource} ---  {unknown_error} ---")
            item['resource'] = localresource
            #errorStop() 
            return False

    return True

def forceUpdateConfig(api,item,myid):

    #Get the resource to log in case of error
    localresource = item['resource']
    if myid != None:
        item['id'] = myid

    item.pop('use_set',None)
    item.pop('resource',None)  

    try:
        api.set(**item)
        item['resource'] = localresource

    except Exception as unknown_error:
        logging.error (f"UPDATE cfg rule Error IN  {item} PATH {localresource} ---  {unknown_error} ---")
        item['resource'] = localresource
        #errorStop() 
        return False

    return True
