#!/usr/bin/python
import mikro_shared
import json
import logging
import os
import mikro_docs
from dotenv import load_dotenv

load_dotenv()

myconfig = os.environ.get("CONFIG")
list_localstring = json.loads(os.environ.get("LOCALSTRING"))
micro_user = os.environ.get("MIKRO_USER")
micro_pass = os.environ.get("MIKRO_PASSWORD")

def addFWRule(list,item,device):

    #Get the resource to log in case of error
    localresource=item['resource']


    item.pop('order',None)
    item.pop('resource',None)

    if 'posi' in item.keys():
        localposi=item['posi']
        item.pop('posi',None)
    else:
        localposi=None

    try:
        list.add(**item)
        item['resource']=localresource
        item['posi']=localposi
    except Exception as unknown_error:
        logging.error (f"{device['name']} -> ADD FW rule Error IN RULE {item['comment']} PATH {localresource} \n\n  {unknown_error} \n  ITEM_full--> {item}")
        #mikro_shared.errorStop() 
        return False
    return True

def moveFWRule(list,item,fwrule,device):

    #Get the resource to log in case of error
    try:
        list.call('move', {'numbers': fwrule['id'], 'destination': str(item['posi'])} )

    except Exception as unknown_error:
        logging.error (f"{device['name']} -> MOVE FW rule Error IN RULE {item['comment']} PATH {item['resource']} \n\n  {unknown_error}")
        #mikro_shared.errorStop() 
        return False
    return True

def cleanConfig(api,config_rules,dryrun,device):
    #Get FW rules to local
    list_ip_firewall_filter = api.get_resource('/ip/firewall/filter')
    list_ip_firewall_nat = api.get_resource('/ip/firewall/nat')
    list_ip_firewall_mangle = api.get_resource('/ip/firewall/mangle')
    list_ip_firewall_address_list = api.get_resource('/ip/firewall/address-list')

    list_ipv6_firewall_filter = api.get_resource('/ipv6/firewall/filter')
    list_ipv6_firewall_nat = api.get_resource('/ipv6/firewall/nat')
    list_ipv6_firewall_mangle = api.get_resource('/ipv6/firewall/mangle')
    list_ipv6_firewall_address_list = api.get_resource('/ipv6/firewall/address-list')

    list_all=[list_ip_firewall_filter,list_ip_firewall_nat,list_ip_firewall_mangle,list_ipv6_firewall_filter,list_ipv6_firewall_nat,list_ipv6_firewall_mangle]
    list_all_add_list=[list_ip_firewall_address_list,list_ipv6_firewall_address_list]

    #Remove non comment rules 

    #--------------ageneral rules
    for path_resource in list_all:
        for item in path_resource.get():

            if not "comment" in item.keys():
                logging.debug (f"{device['name']} -> Found FW rule without comment. Removing -> {item}")
                if not dryrun:
                    path_resource.remove(id=item['id'])
                mikro_docs.dryrun_add(f"- REMOVING No comment. \n \t - item {item} \n")
            elif not mikro_shared.objectExists(config_rules,item['comment']):
                #Verify if need to exclude item
                item_excluded =  False
                for localstring in list_localstring:
                    if localstring in item['comment']:
                        item_excluded = True
                if item_excluded:
                    logging.debug (f"{device['name']} -> Rule not at config excluded from removal -> {item}")
                else:
                    if 'dynamic' in item.keys():
                        if item['dynamic'] == 'false':
                            logging.info (f"{device['name']} -> general rule no dynamic Found rule not at the config, removing -> {item}")
                            if not dryrun:
                                path_resource.remove(id=item['id'])
                            mikro_docs.dryrun_add(f"- REMOVING No config. \n \t - item {item} \n")
                    else:
                            logging.info (f"{device['name']} -> general rule dynamic Found rule not at the config, removing -> {item}")
                            if not dryrun:
                                path_resource.remove(id=item['id'])
                            mikro_docs.dryrun_add(f"- REMOVING No config. \n \t - item {item} \n")

    #--------------addres rules
    for path_resource in list_all_add_list:
        for item in path_resource.get():

            if not "comment" in item.keys():
                logging.debug (f"{device['name']} -> Found FW rule without comment. Removing -> {item}")
                if not dryrun:
                    path_resource.remove(id=item['id'])
                mikro_docs.dryrun_add(f"- REMOVING No comment. \n \t - item {item} \n")
            elif not mikro_shared.objectExistsAddrList(config_rules,item['comment']):
                #Verify if need to exclude item
                item_excluded =  False
                for localstring in list_localstring:
                    if localstring in item['comment']:
                        item_excluded = True
                if item_excluded:
                    logging.debug (f"{device['name']} -> addr rule  item excluded Rule not at config excluded from removal -> {item}")
                else:
                    logging.info (f"{device['name']} -> addr rule item not excluded Found rule not at the config, removing -> {item}")
                    if not dryrun:
                        path_resource.remove(id=item['id'])
                    mikro_docs.dryrun_add(f"- REMOVING No config. \n \t - item {item} \n")

def proccessFWRules(api,config_rules,dryrun,device):

    runningConfig = mikro_shared.getRunningConfig(api,config_rules,device) 

    bot_config=[]
    posi_config=[]
    #Update or add TOP rules

    for item in config_rules:

        #--------------addr list (allow to use a list in YML but paremeters need a map)
        if "address-list" in item['resource']:
            for addr in item['address']:
                local_item={'comment': f"{item['comment']}_{addr}" , 'list': item['comment'], 'address':addr, 'resource': item['resource'] }
                #Check if add or update:
                router_item = mikro_shared.getRunningBy(runningConfig,item['resource'],f"{local_item['comment']}",'comment')
                
                if router_item:
                    if mikro_shared.needAnUpdate(local_item,router_item,device):
                        if not dryrun:
                            mikro_shared.newUpdateConfig(api,local_item,router_item,device)
                        mikro_docs.dryrun_add(f"- UPDATE adl config.   \n \t - local_item --> {local_item}  \n \t - router_item --> {router_item} \n")
                else:
                    if not dryrun:
                        addFWRule(api.get_resource(item['resource']),local_item,device)
                    mikro_docs.dryrun_add(f"- ADD adl config.  \n \t - resource --> {item['resource']}  \n \t - local_item --> {item} \n")

        #--------------ageneral rules
        else:
            if item['order'] == "bot":
                #Check if rule to be added at end
                bot_config.append(item)
            else:
                #Collect rules at posi position
                if item['order'] == "posi":
                    posi_config.append(item)
                #Rule at top
                #Check if add or update:

                router_item = mikro_shared.getRunningBy(runningConfig,item['resource'],item['comment'],'comment')

                if router_item:
                    if mikro_shared.needAnUpdate(item,router_item,device):
                        if not dryrun:
                            mikro_shared.newUpdateConfig(api,item,router_item,device)
                        mikro_docs.dryrun_add(f"- UPDATE fw config.   \n \t - local_item --> {item}  \n \t - router_item --> {router_item} \n")
                else:
                    if not dryrun:
                        addFWRule(api.get_resource(item['resource']),item,device)
                    mikro_docs.dryrun_add(f"- ADD fw config.  \n \t - resource --> {item['resource']}  \n \t - local_item --> {item} \n")

    #Rule at bot
    if not dryrun:
        for item in bot_config:
            router_item = mikro_shared.getRunningBy(runningConfig,item['resource'],item['comment'],'comment')
            if router_item:
                #If exist we remove and add at the end
                api.get_resource(item['resource']).remove(id=router_item['id'])
                addFWRule(api.get_resource(item['resource']),item,device)
            else:
                #If not exist just add at the end
                addFWRule(api.get_resource(item['resource']),item,device)

        #Rule at posi         
        for item in posi_config:
            fw_rule=api.get_resource(item['resource']).get(comment=item['comment'])
            if fw_rule:
                moveFWRule(api.get_resource(item['resource']),item,fw_rule[0],device)
    else:
        pass
        #mikro_docs.dryrun_add(f"- Extra rules at FW bot.  List --> {bot_config}  \n")
        #mikro_docs.dryrun_add(f"- Extra rules specific posi.  List --> {posi_config}  \n")
