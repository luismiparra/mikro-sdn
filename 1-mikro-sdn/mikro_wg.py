import mikro_shared
import yaml
import wgconfig.wgexec as wgexec
import os
from dotenv import load_dotenv
from yaml.loader import SafeLoader
import qrcode
import logging
import json
from jinja2 import Environment, FileSystemLoader

#pip install pillow (needed for qrencode)

load_dotenv()

pathconfig = os.environ.get("CONFIG")
list_localstring = json.loads(os.environ.get("LOCALSTRING"))
pathsecrets = os.environ.get("SECRETS")

def loadConfig(device):

    file_loader = FileSystemLoader("templates")
    env =Environment(loader=file_loader)

    myconfig=[]
    #Create file if not exist
    if not os.path.exists(f'{pathsecrets}/secrets.json'):
        open(f'{pathsecrets}/secrets.json', 'w').close()

    #Read secrets file
    with open(f'{pathsecrets}/secrets.json') as file:
        secrets = json.load(file)
        file.close()

    #CREATE INT LIST WIREGUARD admins
    mydict={}
    mydict['comment'] = f"list_wg_vpn_admins"
    mydict['resource'] = '/interface/list'
    mydict['include'] = 'static'
    mydict['name'] = f"list_wg_vpn_admins"
    mydict['use_set'] = False
    myconfig.append(mydict)      

    #CREATE INT LIST WIREGUARD regular
    mydict={}
    mydict['comment'] = f"list_wg_vpn_default"
    mydict['resource'] = '/interface/list'
    mydict['include'] = 'static'
    mydict['name'] = f"list_wg_vpn_default"
    mydict['use_set'] = False
    myconfig.append(mydict)   
    
    for tunnel in device['wg-vpn']:
        candidate = f"{device['name']}_wgvpn_{tunnel['id']}"

        if not candidate in secrets:
            secrets [candidate] = {}

            preshared_key = wgexec.generate_presharedkey()
            server_keys = wgexec.generate_keypair()

            secrets [candidate]['server_private'] = server_keys[0]
            secrets [candidate]['server_public'] = server_keys[1]
            secrets [candidate]['preshared_key'] = preshared_key

            for peer in range(2,tunnel['number_client']):
                client_keys =  wgexec.generate_keypair()
                secrets [candidate][f'client_private_{peer}'] = client_keys[0]
                secrets [candidate][f'client_public_{peer}'] = client_keys[1]
        
        #INTERFACE WIREGUARD
        mydict={}
        if tunnel['mgmt_vpn']:
            mydict['comment'] = f"{list_localstring[0]}_int_w_vpn_{tunnel['name']}"
        else:
            mydict['comment'] = f"int_w_vpn_{tunnel['name']}"
            
        mydict['resource'] = '/interface/wireguard'
        mydict['mtu'] = device['wg_mtu']
        mydict['name'] = f"int_w_vpn_{tunnel['name']}"
        mydict['listen_port'] = str(tunnel['port'])
        mydict['private_key'] = secrets[candidate]['server_private']
        mydict['use_set'] = False
        myconfig.append(mydict) 

        #ADD RULES AUTOMATICALLY FOR ADMINS AND MGMT
        # 
        if tunnel['admin']:
            #Create rule to allow inbound and forward
            #ipv4
            #forward
            mydict={}
            mydict['comment'] = f"fw_v4_forward_vpn_admin_in_{tunnel['name']}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ip/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_vpn_{tunnel['name']}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            myconfig.append(mydict) 
            #input
            mydict={}
            mydict['comment'] = f"fw_v4_input_vpn_admin_in_{tunnel['name']}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ip/firewall/filter'
            mydict['chain'] = 'input'
            mydict['in_interface'] = f"int_w_vpn_{tunnel['name']}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            myconfig.append(mydict) 
            #ipv6
            #forward
            mydict={}
            mydict['comment'] = f"fw_v6_forward_vpn_admin_in_{tunnel['name']}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ipv6/firewall/filter'
            mydict['chain'] = 'forward'
            mydict['in_interface'] = f"int_w_vpn_{tunnel['name']}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            myconfig.append(mydict) 
            #input
            mydict={}
            mydict['comment'] = f"fw_v6_input_vpn_admin_in_{tunnel['name']}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ipv6/firewall/filter'
            mydict['chain'] = 'input'
            mydict['in_interface'] = f"int_w_vpn_{tunnel['name']}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            myconfig.append(mydict) 

        if tunnel['mgmt_vpn']:
            #Create rule to allow inbound
            #ipv4
            #input
            mydict={}
            mydict['comment'] = f"fw_v4_input_vpn_mgmt_in_{tunnel['name']}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ip/firewall/filter'
            mydict['chain'] = 'input'
            mydict['in_interface'] = f"int_w_vpn_{tunnel['name']}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            myconfig.append(mydict) 
            #ipv6
            #input
            mydict={}
            mydict['comment'] = f"fw_v6_input_vpn_mgmt_in_{tunnel['name']}"
            mydict['order'] = 'top'
            mydict['resource'] = '/ipv6/firewall/filter'
            mydict['chain'] = 'input'
            mydict['in_interface'] = f"int_w_vpn_{tunnel['name']}"
            mydict['disabled'] = 'false'
            mydict['action'] = 'accept'
            myconfig.append(mydict) 

        #add to list
        mydict={}
        if tunnel['mgmt_vpn']:
            mydict['comment'] = f"{list_localstring[0]}_list_item_int_w_vpn_{tunnel['name']}"
        else:
            mydict['comment'] = f"list_item_int_w_vpn_{tunnel['name']}"
        
        mydict['resource'] = '/interface/list/member'
        mydict['interface'] = f"int_w_vpn_{tunnel['name']}"
        if tunnel['admin']:
            mydict['list'] = f'list_wg_vpn_admins'
        else:
            mydict['list'] = f'list_wg_vpn_default'
        mydict['use_set'] = False
        myconfig.append(mydict) 

        #add to firewall
        #ipv4
        mydict={}
        if tunnel['mgmt_vpn']:
            mydict['comment'] = f"{list_localstring[0]}_fw_in_w_vpn_{tunnel['name']}"
        else:
            mydict['comment'] = f"fw_in_w_vpn_{tunnel['name']}"
        
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = str(tunnel['port'])
        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        myconfig.append(mydict) 

        #ipv6
        mydict={}
        if tunnel['mgmt_vpn']:
            mydict['comment'] = f"{list_localstring[0]}_fwv6_in_w_vpn_{tunnel['name']}"
        else:
            mydict['comment'] = f"fwg6_in_w_vpn_{tunnel['name']}"
        
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = str(tunnel['port'])
        mydict['protocol'] = 'udp'        
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        myconfig.append(mydict) 

        #peers
        for peer in range(2,tunnel['number_client']):
            mydict={}
            if tunnel['mgmt_vpn']:
                mydict['comment'] = f"{list_localstring[0]}_peer_wgvpn_{tunnel['name']}_{peer}"
                mydict['name'] = f"{list_localstring[0]}_peer_wgvpn_{tunnel['name']}_{peer}"
            else:
                mydict['comment'] = f"peer_wgvpn_{tunnel['name']}_{peer}"
                mydict['name'] = f"peer_wgvpn_{tunnel['name']}_{peer}"
            
            mydict['resource'] = '/interface/wireguard/peers'
            mydict['allowed_address'] = f"{device['subnetsv4_list'][tunnel['subnet']][peer]}/32,{device['subnetsv6_list'][tunnel['subnet']][peer]}/128"
            mydict['interface'] = f"int_w_vpn_{tunnel['name']}"
            mydict['preshared_key'] = secrets[candidate]['preshared_key']
            mydict['public_key'] = secrets[candidate][f'client_public_{peer}']
            mydict['use_set'] = False
            mydict['is_responder'] = 'true'

            if peer in tunnel['disabled_peers']:
                mydict['disabled'] = 'true'
            else:
                mydict['disabled'] = 'false'

            if tunnel['persistent_keepalive_enable']:
                mydict['persistent_keepalive'] = f"{tunnel['persistent_keepalive_seconds']}s"
                
            myconfig.append(mydict) 

        #ip address
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ip/address'
        mydict['interface'] = f"int_w_vpn_{tunnel['name']}"

        if tunnel['mgmt_vpn']:
            mydict['comment'] = f"{list_localstring[0]}_ip_wgvpn_{tunnel['name']}_{device['subnetsv4_list'][tunnel['subnet']][1]}"
        else:
            mydict['comment'] = f"ip_wgvpn_{tunnel['name']}_{device['subnetsv4_list'][tunnel['subnet']][1]}"
        
        mydict['address'] = f"{device['subnetsv4_list'][tunnel['subnet']][1]}/{str(device['subnetsv4_list'][tunnel['subnet']].prefixlen)}"
        myconfig.append(mydict) 

        #ipv6 address
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ipv6/address'
        mydict['interface'] = f"int_w_vpn_{tunnel['name']}"

        if tunnel['mgmt_vpn']:
            mydict['comment'] = f"{list_localstring[0]}_ipv6_wgvpn_{tunnel['name']}_{device['subnetsv6_list'][tunnel['subnet']][1]}"
        else:
            mydict['comment'] = f"ipv6_wgvpn_{tunnel['name']}_{device['subnetsv6_list'][tunnel['subnet']][1]}"
        
        mydict['address'] = f"{device['subnetsv6_list'][tunnel['subnet']][1]}/{str(device['subnetsv6_list'][tunnel['subnet']].prefixlen)}"
        myconfig.append(mydict) 

        #vpn config file
        #Create the folder if not exist
        if not os.path.exists(f"{pathsecrets}/vpnconfig/{device['name']}_{tunnel['name']}"):
            os.makedirs(f"{pathsecrets}/vpnconfig/{device['name']}_{tunnel['name']}")

        logging.debug (f"{device['name']} -> Wireguar Client VPN file generation.    This can take time...")
        for peer in range(2,tunnel['number_client']):
            mystring=f"#Network WG VPN config \n#VPN name {tunnel['name']}\n#Client {peer}\n"
            mystring=mystring+f"[Interface]\n"
            mystring=mystring+f"Address = {device['subnetsv4_list'][tunnel['subnet']][peer]}/{str(device['subnetsv4_list'][tunnel['subnet']].prefixlen)},{device['subnetsv6_list'][tunnel['subnet']][peer]}/{str(device['subnetsv6_list'][tunnel['subnet']].prefixlen)}\n"
            mystring=mystring+f"PrivateKey = {secrets[candidate][f'client_private_{peer}']}\n"
            mystring=mystring+f"DNS = {device['dns1']},{device['dns2']}\n"
            mystring=mystring+"[Peer]\n"
            mystring=mystring+f"PublicKey = {secrets[candidate]['server_public']}\n"
            mystring=mystring+f"PresharedKey = {secrets[candidate]['preshared_key']}\n"
            mystring=mystring+f"AllowedIPs = {tunnel['allowed_ips']}\n"
            mystring=mystring+f"Endpoint = {device['external_endpoint']}:{tunnel['port']}\n"
            if tunnel['persistent_keepalive_enable']:
                mystring=mystring+f"PersistentKeepalive = {tunnel['persistent_keepalive_seconds']}\n"
            mystring=mystring+f"#"

            #Create onboarding files for mikrotik if mgmt
            if tunnel['mgmt_vpn']:
                template = env.get_template('device_onboard.j2')
                mystring2 = template.render(\
                    wg_comment = f"local_rp_mgmt_vpn_mgmt_vpn",\
                    wg_name = f"int_w_vpn_mgmt_vpn",\
                    wg_private_key = secrets[candidate][f'client_private_{peer}'],\
                    peer_allowed_address = f"{tunnel['allowed_ips']}",\
                    peer_comment = f"local_rp_peer_wgvpn_mgmt_vpn_{peer}",\
                    endpoint_address = f"{device['external_endpoint']}",\
                    peer_endpoint_port = f"{tunnel['port']}",\
                    peer_interface =f"int_w_vpn_mgmt_vpn",\
                    peer_persistent_keepalive = f"{tunnel['persistent_keepalive_seconds']}s",\
                    peer_preshared_key = f"{secrets[candidate]['preshared_key']}",\
                    peer_public_key = f"{secrets[candidate]['server_public']}",\
                    ip_address =f"{device['subnetsv4_list'][tunnel['subnet']][peer]}/{str(device['subnetsv4_list'][tunnel['subnet']].prefixlen)}" ,\
                    ip_comment =f"local_rp_ip_wgvpn_mgmt_vpn_{peer}" ,\
                    portchange_comment =f"local_rp_script_PORT_RANDOM_WG_MGMT_{peer}" ,\
                )

            if device['save_wg_files']:
                #Save external file
                vpnprefixname = ""
                if tunnel['mgmt_vpn']:
                    vpnprefixname = "MGMT"
                elif tunnel['admin']:
                    vpnprefixname = "ADM"
                else:
                    vpnprefixname = "USR"

                with open (f"{pathsecrets}/vpnconfig/{device['name']}_{tunnel['name']}/{vpnprefixname}_{device['location']}_{peer}.conf", 'w') as clientfile:
                    clientfile.write(mystring)   
                    clientfile.close()

                img = qrcode.make(mystring)
                img.save(f"{pathsecrets}/vpnconfig/{device['name']}_{tunnel['name']}/{vpnprefixname}_{device['location']}_{peer}.png")

                if tunnel['mgmt_vpn']:
                    with open (f"{pathsecrets}/mgmt_export/mikro_mgmt_{peer}.txt", 'w') as clientfile:
                        clientfile.write(mystring2)   
                        clientfile.close()                    
    
    #Save secrets file
    with open (f'{pathsecrets}/secrets.json', 'w') as file:
        secrets = json.dump(secrets, file)
        file.close()

    return myconfig
