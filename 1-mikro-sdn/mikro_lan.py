import mikro_shared
import ipaddress

ISSOLATED_VLAN_ID = '999'
BRIDGE_VLAN_NAME = 'bridge-vlans'
#max /26 for ip pool ipv4 and limited to 62 also in ipv6
IP_VIP_LIMIT = 62
LOOPBACK_IP_PREFIX = '10.0.0'
VXLAN_PORT = 8472
VXLAN_LOOP_PROTECT = 'on'
VXLAN_DONT_FRAGMENT = 'inherit'

def loadConfig(device,myinventory):
    myconfig=[]


    #Create loopback
    mydict={}
    mydict['use_set'] = False
    mydict['resource'] = '/ip/address'
    mydict['interface'] = 'lo'
    mydict['comment'] = f"ip_lo_{LOOPBACK_IP_PREFIX}.{device['site_id']}"
    mydict['address'] = f"{LOOPBACK_IP_PREFIX}.{device['site_id']}/32"

    #Just enable if VLAN
    mydict['disabled'] = "true"
    if device['role'] == 'core' or device['role'] == 'edge':
        if device['enable_vxlan']:
            mydict['disabled'] = "false"
    myconfig.append(mydict)

    #Bridge 
    mydict={}
    mydict['comment'] = BRIDGE_VLAN_NAME
    mydict['resource'] = '/interface/bridge'
    mydict['name'] = BRIDGE_VLAN_NAME
    mydict['ingress_filtering'] = 'false'
    mydict['pvid'] = ISSOLATED_VLAN_ID
    mydict['vlan_filtering'] = 'true'
    mydict['use_set'] = False
    myconfig.append(mydict)

    #CREATE INT LIST inside
    mydict={}
    mydict['comment'] = f"int_list_inside"
    mydict['resource'] = '/interface/list'
    mydict['include'] = 'static'
    mydict['name'] = 'list_inside'
    mydict['use_set'] = False
    myconfig.append(mydict) 

    #interface vlan
    for item in device['lan']['vlans']:
        mydict={}
        mydict['comment'] = f"vlan_{item['name']}"
        mydict['resource'] = '/interface/vlan'
        mydict['name'] = item['name']
        mydict['vlan_id'] = str(item['id'])
        mydict['interface'] =  BRIDGE_VLAN_NAME
        mydict['use_set'] = False
        myconfig.append(mydict)

    #Manual creation of issolated 
    
    mydict={}
    mydict['comment'] = f"vlan_isolated"
    mydict['resource'] = '/interface/vlan'
    mydict['name'] = 'isolated'
    mydict['vlan_id'] = ISSOLATED_VLAN_ID
    mydict['interface'] =  BRIDGE_VLAN_NAME
    mydict['use_set'] = False
    myconfig.append(mydict)

    #interface vlan add to list
    for item in device['lan']['vlans']:
        mydict={}
        mydict['comment'] = f"list_item_int_v_{item['name']}"
        mydict['resource'] = '/interface/list/member'
        mydict['interface'] = item['name']
        mydict['list'] = 'list_inside'
        mydict['use_set'] = False
        myconfig.append(mydict)

    #interface bridge port
    if device['lan']['trunk_ports'] != None:
        if device['lan']['trunk_ports'] != None:
            for port in device['lan']['trunk_ports']:
                mydict={}
                mydict['resource'] = '/interface/bridge/port'
                mydict['comment'] = f'int_br_TRUNK_{port}'
                mydict['interface'] = port
                mydict['ingress_filtering'] = 'true'
                mydict['bridge'] = BRIDGE_VLAN_NAME 
                if device['lan']['issolated_trunk']:
                    mydict['pvid'] = ISSOLATED_VLAN_ID
                else:
                    mydict['pvid'] = '1'
                mydict['use_set'] = False
                myconfig.append(mydict)
    if device['lan']['safe_ports'] != None:
        for port in device['lan']['safe_ports']:
            mydict={}
            mydict['resource'] = '/interface/bridge/port'
            mydict['comment'] = f'int_br_1SAFE_access_{port}'
            mydict['interface'] = port
            mydict['ingress_filtering'] = 'true'
            mydict['bridge'] = BRIDGE_VLAN_NAME 
            mydict['pvid'] = '1'
            mydict['use_set'] = False
            myconfig.append(mydict)
    
    #Allow any vlan to work 
    # Example in inventory:
    #
    # access_ports:
    #   - port: 'ether4'
    #     vlan: 2

    if 'access_ports' in device['lan'].keys():
        for item in device['lan']['access_ports']:
            mydict={}
            mydict['resource'] = '/interface/bridge/port'
            mydict['comment'] = f"int_br_vlan_{item['vlan']}_access_{item['port']}"
            mydict['interface'] = item['port']
            mydict['ingress_filtering'] = 'true'
            mydict['bridge'] = BRIDGE_VLAN_NAME 
            mydict['pvid'] = item['vlan']
            mydict['use_set'] = False
            myconfig.append(mydict)

    #interface bridge vlan
    for item in device['lan']['vlans']:   
        mydict={}
        mydict['resource'] = '/interface/bridge/vlan'
        mydict['comment'] = f"int_br_vlan_{str(item['id'])}"
        myinterfaces=""
        if device['lan']['trunk_ports'] != None:
            for name in device['lan']['trunk_ports']:
                if (item['id'] == 1) and not (device['lan']['issolated_trunk']):
                    #this port is a mixed port safe will be untagged
                    pass
                else:
                    myinterfaces = myinterfaces + "," + name

            mydict['tagged'] = f"{BRIDGE_VLAN_NAME}{myinterfaces}"
            mydict['vlan_ids'] = str(item['id'])
            mydict['use_set'] = False
            mydict['bridge'] = BRIDGE_VLAN_NAME
            myconfig.append(mydict)

    #ipv4 address
    for item in device['lan']['vlans']:   
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ip/address'
        mydict['interface'] = item['name']
        mydict['comment'] = f"ip_{item['name']}_{str(device['gatewayv4_list'][item['id']])}"  
        mydict['address'] = f"{str(device['gatewayv4_list'][item['id']])}/{str(device['subnetsv4_list'][item['id']].prefixlen)}"
        myconfig.append(mydict)

    #ipv6 address
    for item in device['lan']['vlans']:   
        if item['ipv6']:
            mydict={}
            mydict['use_set'] = False
            mydict['resource'] = '/ipv6/address'
            mydict['interface'] = item['name']
            mydict['comment'] = f"ip_{item['name']}_{str(device['gatewayv6_list'][item['id']])}"  
            mydict['address'] = f"{str(device['gatewayv6_list'][item['id']])}/{str(device['subnetsv6_list'][item['id']].prefixlen)}"
            myconfig.append(mydict)
            

    #ipv6 address
    for item in device['lan']['vlans']:   
        if item['ipv6slaac']:
            mydict={}
            mydict['use_set'] = False
            mydict['resource'] = '/ipv6/address'
            mydict['interface'] = item['name']
            mydict['comment'] = f"ip_{item['name']}_{str(device['gatewayv6slaac_list'][item['id']])}_slaac"  
            mydict['address'] = f"{str(device['gatewayv6slaac_list'][item['id']])}/{str(device['subnetsv6slaac_list'][item['id']].prefixlen)}"
            myconfig.append(mydict)

    #ipv4_vip
    for item in device['lan']['vlans']:
        if 'ipv4_vip_pool' in item.keys():
            if item['ipv4_vip_pool'] != None:
                for subnet in item['ipv4_vip_pool']:
                    counter_of_vip = 0
                    for myip in list(ipaddress.ip_network(subnet).hosts()):
                        mydict={}
                        mydict['use_set'] = False
                        mydict['resource'] = '/ip/address'
                        mydict['interface'] = item['name']
                        mydict['comment'] = f"ip_VIP_{item['name']}_{myip}"  
                        mydict['address'] = f"{myip}/{str(ipaddress.IPv4Network(subnet).prefixlen)}"
                        myconfig.append(mydict)
                        #Limit amount of ips    
                        counter_of_vip += 1
                        if counter_of_vip >= IP_VIP_LIMIT:
                            break

    #ipv6_vip
    for item in device['lan']['vlans']:
        if 'ipv6_vip_pool' in item.keys():
            if item['ipv6_vip_pool'] != None:
                for subnet in item['ipv6_vip_pool']:
                    counter_of_vip = 0
                    for myip in list(ipaddress.ip_network(subnet).hosts()):
                        mydict={}
                        mydict['use_set'] = False
                        mydict['resource'] = '/ipv6/address'
                        mydict['interface'] = item['name']
                        mydict['comment'] = f"ipv6_VIP_{item['name']}_{myip}"  
                        mydict['address'] = f"{myip}/{str(ipaddress.IPv6Network(subnet).prefixlen)}"
                        myconfig.append(mydict)
                        #Limit amount of ips    
                        counter_of_vip += 1
                        if counter_of_vip >= IP_VIP_LIMIT:
                            break

    #ipv4 pool
    for item in device['lan']['vlans']:   
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ip/pool'
        mydict['comment'] = f"pool_{str(device['subnetsv4_list'][item['id']])}" 
        mydict['name'] = f"pool_{str(device['subnetsv4_list'][item['id']])}" 
        mydict['ranges'] = f"{device['subnetsv4_list'][item['id']][device['dhcp_pool_start']]}-{device['subnetsv4_list'][item['id']][device['dhcp_pool_end']]}"
        myconfig.append(mydict)

    #ipv6 pool
    for item in device['lan']['vlans']:   
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ipv6/pool'
        mydict['comment'] = f"pool_{str(device['subnetsv6_list'][item['id']])}" 
        mydict['name'] = f"pool_{str(device['subnetsv6_list'][item['id']])}" 
        mydict['prefix'] = str(device['subnetsv6_list'][item['id']])
        mydict['prefix_length'] = str(device['subnetsv6_list'][item['id']].prefixlen)
        myconfig.append(mydict)

    #ipv4 dhcp-server
    for item in device['lan']['vlans']:   
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ip/dhcp-server'
        mydict['comment'] = f"dhcpV4_{item['name']}" 
        mydict['name'] = f"dhcpV4_{item['name']}" 
        mydict['address_pool'] = f"pool_{str(device['subnetsv4_list'][item['id']])}"
        mydict['interface'] = item['name']
        mydict['lease_time'] = device['lease-time']
        myconfig.append(mydict)

    #ipv4 dhcp-server network
    for item in device['lan']['vlans']:   
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ip/dhcp-server/network'
        mydict['comment'] = f"dhcp_netV4_{item['name']}" 
        mydict['address'] = f"{device['subnetsv4_list'][item['id']]}"
        mydict['dns_server'] = f"{device['dns1']},{device['dns2']}"
        mydict['ntp_server'] = f"{device['ntp1']}"
        mydict['gateway'] = f"{str(device['gatewayv4_list'][item['id']])}"
        mydict['domain'] = f"{device['domain']}"
        myconfig.append(mydict)

    #ipv4 dhcp-server network FW   
    for item in device['lan']['vlans']: 
        mydict={}
        mydict['comment'] = f"fw_in_dhcp_netV4_{item['name']}" 
        mydict['order'] = 'top'
        mydict['resource'] = '/ip/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '67-68'
        mydict['protocol'] = 'udp'
        mydict['in_interface'] = item['name']
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        myconfig.append(mydict) 

    #ipv6 dhcp-server
    for item in device['lan']['vlans']:   
        mydict={}
        mydict['use_set'] = False
        mydict['resource'] = '/ipv6/dhcp-server'
        mydict['comment'] = f"dhcpV6_{item['name']}" 
        mydict['name'] = f"dhcpV6_{item['name']}" 
        mydict['address_pool'] = f"pool_{str(device['subnetsv6_list'][item['id']])}"
        mydict['interface'] = item['name']
        mydict['lease_time'] = device['lease-time']
        myconfig.append(mydict)

    #ipv4 dhcp-server network FW   
    for item in device['lan']['vlans']: 
        mydict={}
        mydict['comment'] = f"fw_in_dhcp_netV6_{item['name']}" 
        mydict['order'] = 'top'
        mydict['resource'] = '/ipv6/firewall/filter'
        mydict['chain'] = 'input'
        mydict['dst_port'] = '546'
        mydict['protocol'] = 'udp'
        mydict['in_interface'] = item['name']
        mydict['disabled'] = 'false'
        mydict['action'] = 'accept'
        myconfig.append(mydict) 


    #----------------
    #----------------VXLAN
    #----------------

    if device['role'] == 'core' or device['role'] == 'edge':
        if device['enable_vxlan']:

            #-----------------Create FW rules

            #--Collecting info from global inventory
            networks_to_allow = []
            vxlan_lo_remote = []
            remote_vlans = []

            for inventory_device in myinventory:
                if inventory_device['role'] == 'core' or inventory_device['role'] == 'edge':
                    #Collect all core transit subnets from routers participating
                    if inventory_device['enable_vxlan']:

                        #1) COLLECT SUBNETS TO ALLOW IN FW

                        # Define the initial network
                        network = ipaddress.ip_network(inventory_device['subnetv4'])
                        # Looking for core transit subnet:
                        subnet_index = 250
                        # Calculate the specific /24 subnet
                        subnet_prefix_length = 24
                        target_subnet = list(network.subnets(new_prefix=subnet_prefix_length))[subnet_index]
                        networks_to_allow.append(target_subnet)

                        #Check is not us
                        if inventory_device['name']!= device['name']:
                            #2) COLLECT LOOPBACK PARTICIPATING not us
                            vxlan_lo_remote.append(f"{LOOPBACK_IP_PREFIX}.{inventory_device['site_id']}")

                            #3) REMOTE VLANS
                            for vlan in inventory_device['lan']['vlans']:
                                remote_vlans.append({'inventory_device':inventory_device, 'vlan':vlan})

            #--Create address list
            for subnet in networks_to_allow:
                #--Create filter input rule
                mydict={}
                mydict['comment'] = f"fw_in_vxlan_{subnet}"
                mydict['order'] = 'top'
                mydict['resource'] = '/ip/firewall/filter'
                mydict['chain'] = 'input'
                mydict['disabled'] = 'false'
                mydict['protocol'] = 'udp'
                mydict['dst_port'] = f'{VXLAN_PORT}'
                mydict['src_address'] = f"{subnet}"
                mydict['action'] = 'accept'
                myconfig.append(mydict) 

            #--CREATE LOCAL VXLANS

            for vlan in device['lan']['vlans']:

                #VNI is a combination of site id digit and vlan id
                myvni = f"{device['site_id']}{vlan['id']}"

                mydict={}
                mydict['comment'] = f"vxlan_local_{device['name']}_{vlan['name']}_{myvni}"
                mydict['name'] = f"vxlan_local_{device['name']}_{vlan['name']}_{myvni}"
                #vxlan consume 50 bytes for IPv4 and 70 for ipv6 we just use our WG tunnel as reference
                mydict['mtu'] =  f"{int(device['wg_mtu']) - 50}"
                mydict['dont_fragment'] = VXLAN_DONT_FRAGMENT
                mydict['loop_protect'] = VXLAN_LOOP_PROTECT
                mydict['port'] =  f'{VXLAN_PORT}'
                mydict['vni'] =  f'{myvni}'
                mydict['resource'] = '/interface/vxlan'

                myconfig.append(mydict) 

                #--Create local vtep
                for mylo in vxlan_lo_remote:
                    mydict={}
                    mydict['comment'] = f"vtep_{mylo}__{device['name']}_{vlan['name']}_{myvni}"
                    mydict['interface'] = f"vxlan_local_{device['name']}_{vlan['name']}_{myvni}"
                    mydict['port'] =  f'{VXLAN_PORT}'
                    mydict['remote_ip'] =  f'{mylo}'
                    mydict['resource'] = '/interface/vxlan/vteps'
                    myconfig.append(mydict)

                #--Bridge local vxlan with pvid

                mydict={}
                mydict['resource'] = '/interface/bridge/port'
                mydict['comment'] = f"int_br_{myvni}_{device['name']}_{vlan['name']}"
                mydict['interface'] = f"vxlan_local_{device['name']}_{vlan['name']}_{myvni}"
                mydict['ingress_filtering'] = 'true'
                mydict['bridge'] = BRIDGE_VLAN_NAME 
                mydict['pvid'] = f"{vlan['id']}"
                mydict['edge'] = 'yes'
                mydict['use_set'] = False
                myconfig.append(mydict)


            #--CREATE REMOTE VXLANS

            for item in remote_vlans:
                #VNI is a combination of site id digit and vlan id
                myvni = f"{item['inventory_device']['site_id']}{item['vlan']['id']}"

                mydict={}
                mydict['comment'] = f"vxlan_remote_{item['inventory_device']['name']}_{item['vlan']['name']}_{myvni}"
                mydict['name'] = f"vxlan_remote_{item['inventory_device']['name']}_{item['vlan']['name']}_{myvni}"
                #vxlan consume 50 bytes for IPv4 and 70 for ipv6 we just use our WG tunnel as reference
                mydict['mtu'] =  f"{int(device['wg_mtu']) - 50}"
                mydict['dont_fragment'] = VXLAN_DONT_FRAGMENT
                mydict['loop_protect'] = VXLAN_LOOP_PROTECT
                mydict['port'] =  f'{VXLAN_PORT}'
                mydict['vni'] =  f'{myvni}'
                mydict['resource'] = '/interface/vxlan'
                
                myconfig.append(mydict) 

                #--CREATE VTEPS
                for mylo in vxlan_lo_remote:
                    mydict={}
                    mydict['comment'] = f"vtep_{mylo}_{item['inventory_device']['name']}_{item['vlan']['name']}_{myvni}"
                    mydict['interface'] = f"vxlan_remote_{item['inventory_device']['name']}_{item['vlan']['name']}_{myvni}"
                    mydict['port'] =  f'{VXLAN_PORT}'
                    mydict['remote_ip'] =  f'{mylo}'
                    mydict['resource'] = '/interface/vxlan/vteps'
                    myconfig.append(mydict) 

                #--CREATE LOCAL VLAN AND BRIDGE WITH REMOTE VXLANS if enabled on inventory
                if device['enable_vxlan_to_vlan']:
                    
                    #All exported vlans start with number 3 xxx  where xxx is the VNI
                    exportvlan_id = f"3{myvni}"

                    #--create vlan
                    mydict={}
                    mydict['comment'] = f"{exportvlan_id}_vx_{myvni}_{item['inventory_device']['name']}_{item['vlan']['name']}"
                    mydict['resource'] = '/interface/vlan'
                    mydict['name'] = f"{exportvlan_id}_vx_{myvni}_{item['inventory_device']['name']}_{item['vlan']['name']}"
                    mydict['vlan_id'] = f"{exportvlan_id}"
                    mydict['interface'] =  BRIDGE_VLAN_NAME
                    mydict['use_set'] = False
                    myconfig.append(mydict)

                    #--add vxlan to bridge port
                    mydict={}
                    mydict['resource'] = '/interface/bridge/port'
                    mydict['comment'] = f"int_br_{item['inventory_device']['name']}_{item['vlan']['name']}_{myvni}"
                    mydict['interface'] = f"vxlan_remote_{item['inventory_device']['name']}_{item['vlan']['name']}_{myvni}"
                    mydict['ingress_filtering'] = 'true'
                    mydict['bridge'] = BRIDGE_VLAN_NAME 
                    mydict['pvid'] = f"{exportvlan_id}"
                    mydict['edge'] = 'yes'
                    mydict['use_set'] = False
                    myconfig.append(mydict)


                    #Add to bridge trunks

                    mydict={}
                    mydict['resource'] = '/interface/bridge/vlan'
                    mydict['comment'] = f"int_br_vlan_{exportvlan_id}"
                    myinterfaces=""
                    if device['lan']['trunk_ports'] != None:
                        for name in device['lan']['trunk_ports']:
                            if (exportvlan_id == 1) and not (device['lan']['issolated_trunk']):
                                #this port is a mixed port safe will be untagged
                                pass
                            else:
                                myinterfaces = myinterfaces + "," + name

                        mydict['tagged'] = f"{BRIDGE_VLAN_NAME}{myinterfaces}"
                        mydict['vlan_ids'] = f"{exportvlan_id}"
                        mydict['use_set'] = False
                        mydict['bridge'] = BRIDGE_VLAN_NAME
                        myconfig.append(mydict)

    #----------------
    #----------------
    #----------------


    return myconfig








