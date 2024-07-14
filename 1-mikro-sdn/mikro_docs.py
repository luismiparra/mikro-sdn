import os
import logging
from dotenv import load_dotenv
import json
import markdown
import yaml
import re
import ipaddress
from jinja2 import Environment, FileSystemLoader
import mikro_shared

#For bind config export enter domain
DOMAIN_NAME = "changeme.local"


load_dotenv()

pathconfig = os.environ.get("CONFIG")
pathsecrets = os.environ.get("SECRETS")
pathweb = os.environ.get("WEB")
list_localstring = json.loads(os.environ.get("LOCALSTRING"))
micro_user = os.environ.get("MIKRO_USER")
micro_pass = os.environ.get("MIKRO_PASSWORD")
debugmode = os.environ.get("DEBUGMODE")

globalbind_str_a = ""
globalbind_str_ptr = ""
global_doc_md= ""
global_dryrun_md="#CHANGES FILE MODE:\n"

def dryrun_add(txt):
    global global_dryrun_md
    global_dryrun_md = global_dryrun_md + txt

def saveDryrun():
    global global_dryrun_md

    #ofustate
    global_dryrun_md = re.sub(r"key': '.+?(?=',)","XXX_KEY_REMOVED_XXX",global_dryrun_md)
    global_dryrun_md = re.sub(r"password': '.+?(?=',)","XXX_KEY_REMOVED_XXX",global_dryrun_md)
    global_dryrun_md = re.sub(r"secret': '.+?(?=',)","XXX_KEY_REMOVED_XXX",global_dryrun_md)

    file_loader = FileSystemLoader("templates")
    env =Environment(loader=file_loader)
    template = env.get_template('web_header.j2')

    myweb = template.render( body = markdown.markdown(global_dryrun_md, extensions=['tables']))

    with open (f"{pathweb}/Changes.html", 'w') as file1:
        file1.write(myweb)
        file1.close()       

    with open (f"{pathweb}/Changes.md", 'w') as file1:
        file1.write(global_dryrun_md)
        file1.close()      

def get_globalbind_str_a():
    return globalbind_str_a

def get_globalbind_str_ptr():
    return globalbind_str_ptr

def saveGlobal():

    file_loader = FileSystemLoader("templates")
    env =Environment(loader=file_loader)
    with open (f"{pathweb}/bind_A.txt", 'w') as file1:
        file1.write(globalbind_str_a)
        file1.close()
    with open (f"{pathweb}/bind_PTR.txt", 'w') as file1:
        file1.write(globalbind_str_ptr)
        file1.close()

    template = env.get_template('web_header.j2')
    myweb = template.render( body = markdown.markdown(global_doc_md, extensions=['tables']))

    with open (f"{pathweb}/Global.html", 'w') as file1:
        file1.write(myweb)
        file1.close()       

    with open (f"{pathweb}/Global.md", 'w') as file1:
        file1.write(global_doc_md)
        file1.close()  

def bindzoneGenerator(config,device):
    global globalbind_str_a
    global globalbind_str_ptr

    a_list = []

    str_a = ""
    str_ptr = ""


    for item in config:
        if item['resource'] == '/ip/address':

            #Limit A resources to 1
            if (not f"{item['interface']}_{device['name']}" in a_list):
                str_a = str_a + f"{item['interface']}_{device['name']} \t A \t\t\t\t {item['address'].split('/')[0]} \n"
                a_list.append(f"{item['interface']}_{device['name']}")

            ipsplit = item['address'].split('/')[0].split('.')
            str_ptr = str_ptr + f"{ipsplit[3]}.{ipsplit[2]}.{ipsplit[1]} \t IN \t\t\t\t PTR \t {item['interface']}_{device['name']}.{DOMAIN_NAME} \n"



            #{item['address'].split('/')[0]}
    

    
    globalbind_str_a = globalbind_str_a + str_a
    globalbind_str_ptr = globalbind_str_ptr + str_ptr

    globalbind_str_a = globalbind_str_a.replace("_","-")
    globalbind_str_ptr = globalbind_str_ptr.replace("_","-")

def docGenerator(config,description,ignore_keys,external):

    tempdoc = ""
    done_resource = ['/system/scheduler','/snmp/community']
    


    tempdoc = tempdoc + f"## {description}  \n  \n"
    #Look for new resource
    if external:
        #to be done in case we want documents on external, be sure to exclude keys
        pass
    else:
        for firstitem in config:
            if not firstitem['resource'] in done_resource:

                #We add category as done
                done_resource.append(firstitem['resource'])

                #We find all posible keys for category
                list_of_keys=[]

                for  item in config:
                    if item['resource'] == firstitem['resource'] :
                        for mykey in item.keys():
                            if not mykey in list_of_keys:
                                list_of_keys.append(mykey)
                #Tittle of category
                tempdoc = tempdoc + f"### {firstitem['resource']}  \n"

                #Start of table

                for mykey in list_of_keys:
                    if mykey not in ignore_keys:
                        tempdoc = tempdoc + f"{mykey}|"
                tempdoc = tempdoc + f"\n"

                tempdoc = tempdoc + f"|"
                for mykey in list_of_keys:
                    if mykey not in ignore_keys:
                        tempdoc = tempdoc + f"---------|"
                tempdoc = tempdoc + f"\n"

                for item in config:
                    if item['resource'] == firstitem['resource']:
                        tempdoc = tempdoc + f"|"
                        for mykey in list_of_keys:
                            if mykey not in ignore_keys:
                                if mykey in item.keys():
                                    tempdoc = tempdoc + f"{item[mykey]}|"
                                else:
                                    tempdoc = tempdoc + f" - |"
                        tempdoc = tempdoc + f"\n"

                tempdoc = tempdoc + "\n"          
    return tempdoc

def createDocs (device):

    global global_doc_md

    file_loader = FileSystemLoader("templates")
    env =Environment(loader=file_loader)

    ignore_keys = ['resource','use_set','private_key','preshared_key','public_key','shared_secret','password']

    with open(f"{pathsecrets}/proposed/{device['name']}_fw.json") as file1:
        globalfwconfig = json.load(file1)
        file1.close()

    with open(f"{pathsecrets}/proposed/{device['name']}_global.json") as file2:
        globalconfig = json.load(file2)
        file2.close()

    sorted_globalconfig = sorted(globalconfig, key=lambda d: d['resource']) 
    sorted_globalfwconfig = sorted(globalfwconfig, key=lambda d: d['resource']) 

    mytempdns = ""
    mytempdoc = f"#DEVICE: {device['name']}\n\n"

    mytempdoc = mytempdoc + docGenerator(sorted_globalconfig,"General Config",ignore_keys,False)
    mytempdoc = mytempdoc + docGenerator(sorted_globalfwconfig,"Firewall Config",ignore_keys,False) 

    mytempdns = bindzoneGenerator(sorted_globalconfig,device)
    #print (mytempdns)

    #Save config file
    with open (f"{pathweb}/{device['name']}.md", 'w') as file1:
        file1.write(mytempdoc)
        file1.close()

    template = env.get_template('web_header.j2')
    myweb = template.render( body = markdown.markdown(mytempdoc, extensions=['tables']))

    with open (f"{pathweb}/{device['name']}.html", 'w') as file1:
        file1.write(myweb)
        file1.close()

    #Save to global
    global_doc_md = global_doc_md + mytempdoc


    #markdown.markdownFromFile(
    #    input=f"{pathsecrets}/proposed/{device['name']}.md",
    #    output=f"{pathsecrets}/proposed/{device['name']}.html",
    #    encoding='utf8',
    #    extensions=['tables']
    #)

def createExternal():

    ignore_keys = []

    with open(f"{pathsecrets}/external/external.json") as file1:
        externalconfig = json.load(file1)
        file1.close()

    
    mytempdoc = ""

    mytempdoc = mytempdoc + docGenerator(externalconfig,"ExternalConfig",ignore_keys,True)

    #Save config file
    with open (f"{pathsecrets}/external/external.md", 'w') as file1:
        file1.write(mytempdoc)
        file1.close()

    with open (f"{pathsecrets}/external/external.html", 'w') as file1:
        file1.write(markdown.markdown(mytempdoc, extensions=['tables']))
        file1.close()

    #markdown.markdownFromFile(
    #    input=f"{pathsecrets}/proposed/{device['name']}.md",
    #    output=f"{pathsecrets}/proposed/{device['name']}.html",
    #    encoding='utf8',
    #    extensions=['tables']
    #)

def externalFiles(externaldata):
    lastconn={}
    for devicekey in externaldata.keys():
        for connkey in externaldata[devicekey].keys():
            conn = externaldata[devicekey][connkey]
            lastconn = conn
            #Generate wireguard file

            mystring=f"#Network External config for wireguard \n#VPN name {conn['wireguard_interface']['name']}\n"
            mystring=mystring+f"[Interface]\n"
            mystring=mystring+f"Address = {conn['ip_address']['address']},{conn['ipv6_address']['address']}\n"
            mystring=mystring+f"Table = off\n"
            mystring=mystring+f"Fwmark = 0xa\n"    
            mystring=mystring+f"ListenPort = {conn['wireguard_interface']['listen_port']}\n"       
            mystring=mystring+f"PrivateKey = {conn['wireguard_interface']['private_key']}\n"
            mystring=mystring+f"MTU = {conn['wireguard_interface']['mtu']}\n"
            mystring=mystring+"[Peer]\n"
            mystring=mystring+f"PublicKey = {conn['wireguard_peer']['public_key']}\n"
            mystring=mystring+f"PresharedKey = {conn['wireguard_peer']['preshared_key']}\n"
            mystring=mystring+f"AllowedIPs = {conn['wireguard_peer']['allowed_address']}\n"
            mystring=mystring+f"Endpoint = {conn['wireguard_peer']['endpoint_address']}:{conn['wireguard_peer']['endpoint_port']}\n"

            #We remove the "s from seconds in keepalive"
            temp_keepalive = re.sub('\D', '', conn['wireguard_peer']['persistent_keepalive'])
            mystring=mystring+f"PersistentKeepalive = {temp_keepalive}\n"

            with open (f"{pathsecrets}/external_export/wg_{devicekey}_{conn['connection']}.conf", 'w') as file1:
                file1.write(mystring)
                file1.close()

        #Generate BGP config
        mystring=f"!Network External config BGP for frr\n"
        mystring=mystring+f"router bgp {lastconn['ipv4_bgp_config']['as']}\n"
        mystring=mystring+f" bgp router-id {lastconn['ipv4_bgp_config']['router-id']}\n"
        mystring=mystring+f" neighbor EBGP_RP peer-group\n"
        
        for connkey in externaldata[devicekey].keys():
            conn = externaldata[devicekey][connkey]
            mystring=mystring+f" neighbor {conn['ipv4_bgp_config']['remote.address']} remote-as {conn['ipv4_bgp_config']['remote.as']}\n"
            mystring=mystring+f" neighbor {conn['ipv4_bgp_config']['remote.address']} peer-group EBGP_RP\n"
            mystring=mystring+f" neighbor {conn['ipv6_bgp_config']['remote.address']} remote-as {conn['ipv6_bgp_config']['remote.as']}\n"

        mystring=mystring+f" address-family ipv4 unicast\n"
        mystring=mystring+f"  redistribute connected\n"
        mystring=mystring+f"  neighbor EBGP_RP route-map rpv4 in  \n"
        mystring=mystring+f"  neighbor EBGP_RP route-map rpv4 out  \n"

        for connkey in externaldata[devicekey].keys():
            conn = externaldata[devicekey][connkey]        
            mystring=mystring+f"  no neighbor {conn['ipv6_bgp_config']['remote.address']} activate\n"

        mystring=mystring+f" exit-address-family  \n"
        mystring=mystring+f" address-family ipv6 unicast  \n"
        mystring=mystring+f"  redistribute connected \n"

        for connkey in externaldata[devicekey].keys():
            conn = externaldata[devicekey][connkey]
            mystring=mystring+f"  neighbor {conn['ipv6_bgp_config']['remote.address']} activate\n"
            mystring=mystring+f"  neighbor {conn['ipv6_bgp_config']['remote.address']} route-map rpv6 in\n"
            mystring=mystring+f"  neighbor {conn['ipv6_bgp_config']['remote.address']} route-map rpv6 out\n"
        mystring=mystring+f" exit-address-family\n"
        mystring=mystring+f"ip prefix-list rpv4 seq 1 permit 0.0.0.0/0 le 32 \n"
        mystring=mystring+f"ipv6 prefix-list rpv6 seq 1 permit ::/0 le 128\n"
        mystring=mystring+f"! \n"
        mystring=mystring+f"! \n"
        mystring=mystring+f"route-map rpv4 permit 10 \n"
        mystring=mystring+f" match ip address prefix-list rpv4 \n"
        mystring=mystring+f"route-map rpv6 permit 10 \n"
        mystring=mystring+f" match ipv6 address prefix-list rpv6 \n"

        with open (f"{pathsecrets}/external_export/frr_{devicekey}.conf", 'w') as file1:
            file1.write(mystring)
            file1.close()
