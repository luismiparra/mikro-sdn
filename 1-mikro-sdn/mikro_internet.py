def loadConfig(device):

    myconfig=[]

    #DHCP for interfaces 

    #for interface in device['internet-int-dhcp']:

    #    mydict={}
    #    mydict['comment'] = f"dhcp_c_internet1_{interface}"
    #    mydict['resource'] = '/ip/dhcp-client'
    #    mydict['interface'] = interface
    #    mydict['use_set'] = False
    #    myconfig.append(mydict)


    #Just create path to internet if router is not the path
    if (device ['role'] == 'core' and device['core_internet_transit'] == False) or ( device ['role'] == 'edge'):
        #Create routing table

            mydict={}
            mydict['comment'] = f"routing_table_internet_vpn"
            mydict['resource'] = '/routing/table'
            mydict['name'] = 'internet_vpn'
            mydict['fib'] = ""
            myconfig.append(mydict)

            #Create routing rules
            mydict={}
            mydict['comment'] = f"routing_rule_internet_vpn"
            mydict['resource'] = '/routing/rule'
            mydict['table'] = 'internet_vpn'
            mydict['action'] = "lookup-only-in-table"
            mydict['disabled'] = "false"
            mydict['routing-mark'] = "internet_vpn"
            myconfig.append(mydict)

            mydict={}
            mydict['comment'] = f"routing_rule_main"
            mydict['resource'] = '/routing/rule'
            mydict['table'] = 'main'
            mydict['action'] = "lookup"
            mydict['disabled'] = "false"
            mydict['routing-mark'] = "main"
            myconfig.append(mydict)

            #Create routing rules
            if 'internet_vpn_ip' in device.keys():
                mydict={}
                mydict['comment'] = f"ip_route_internet_vpn"
                mydict['resource'] = '/ip/route'
                mydict['dst-address'] = '0.0.0.0/0'
                mydict['gateway'] = device['internet_vpn_ip']
                mydict['routing-table'] = 'internet_vpn'
                mydict['disabled'] = "false"
                myconfig.append(mydict) 

            #Create FW rule to forward traffic 

            mydict={}
            mydict['comment'] = f"nordvpn_mark_forward"
            mydict['resource'] = '/ip/firewall/mangle'
            mydict['order'] = "top"
            mydict['chain'] = 'prerouting'
            mydict['src_address_list'] = 'SET_HOSTS4_ROUTEVIA_WG'
            mydict['dst_address_list'] = '!SET_NET4_PRIVATE'
            mydict['new_routing_mark'] = "internet_vpn"
            mydict['log'] = "false"
            mydict['log_prefix'] = "no"
            mydict['disabled'] = "false"
            mydict['action'] = "mark-routing"

            myconfig.append(mydict)

            #Create FW rule to output traffic to be able to simulate out

            mydict={}
            mydict['comment'] = f"nordvpn_mark_out"
            mydict['resource'] = '/ip/firewall/mangle'
            mydict['order'] = "top"
            mydict['chain'] = 'output'
            mydict['src_address_list'] = 'SET_HOSTS4_ROUTEVIA_WG'
            mydict['dst_address_list'] = '!SET_NET4_PRIVATE'
            mydict['new_routing_mark'] = "internet_vpn"
            mydict['log'] = "false"
            mydict['log_prefix'] = "no"
            mydict['disabled'] = "false"
            mydict['action'] = "mark-routing"

            myconfig.append(mydict)

            #Create FW rule to to forward traffic if mark via webapp

            mydict={}
            mydict['comment'] = f"webapp_mark_internetvpn_forward"
            mydict['resource'] = '/ip/firewall/mangle'
            mydict['order'] = "top"
            mydict['chain'] = 'prerouting'
            mydict['src_address_list'] = 'SET_HOSTS4_WEBAPP_VPN'
            mydict['dst_address_list'] = '!SET_NET4_PRIVATE'
            mydict['new_routing_mark'] = "internet_vpn"
            mydict['log'] = "false"
            mydict['log_prefix'] = "no"
            mydict['disabled'] = "false"
            mydict['action'] = "mark-routing"

            myconfig.append(mydict)

    #CREATE INT LIST WIREGUARD admins
    mydict={}
    mydict['comment'] = f"list_internet"
    mydict['resource'] = '/interface/list'
    mydict['include'] = 'static'
    mydict['name'] = f"list_internet"
    mydict['use_set'] = False
    myconfig.append(mydict)   

    #add to list
    mydict={}
    mydict['comment'] = f"list_internet_item_int_eth1"
    mydict['resource'] = '/interface/list/member'
    mydict['interface'] = f"ether1"
    mydict['list'] = f'list_internet'
    mydict['use_set'] = False
    myconfig.append(mydict)   

    #Create core transits 
    for my_core_transit in device['core_transits']:
        #Create routing table

            mydict={}
            mydict['comment'] = f"routing_table_core_transit_{my_core_transit['transit_device']}"
            mydict['resource'] = '/routing/table'
            mydict['name'] = f"core_transit_{my_core_transit['transit_device']}"
            mydict['fib'] = ""
            myconfig.append(mydict)

            #Create routing rules
            mydict={}
            mydict['comment'] = f"routing_rule_core_transit_{my_core_transit['transit_device']}"
            mydict['resource'] = '/routing/rule'
            mydict['table'] = f"core_transit_{my_core_transit['transit_device']}"
            mydict['action'] = "lookup-only-in-table"
            mydict['disabled'] = "false"
            mydict['routing-mark'] = f"core_transit_{my_core_transit['transit_device']}"
            myconfig.append(mydict)

            #Create routing rules
            mydict={}
            mydict['comment'] = f"ip_route_core_transit_{my_core_transit['transit_device']}"
            mydict['resource'] = '/ip/route'
            mydict['dst-address'] = '0.0.0.0/0'
            mydict['gateway'] = my_core_transit['ipv4']
            mydict['routing-table'] = f"core_transit_{my_core_transit['transit_device']}"
            mydict['disabled'] = "false"
            myconfig.append(mydict) 

            #Create FW mangle rule to use this route transit
            mydict={}
            mydict['comment'] = f"core_transit_{my_core_transit['transit_device']}_mark"
            mydict['resource'] = '/ip/firewall/mangle'
            mydict['order'] = "top"
            mydict['chain'] = 'prerouting'
            mydict['src_address_list'] = f"SET_HOSTS4_VIA_{my_core_transit['transit_device']}"
            mydict['dst_address_list'] = '!SET_NET4_PRIVATE'
            mydict['new_routing_mark'] = f"core_transit_{my_core_transit['transit_device']}"
            mydict['log'] = "false"
            mydict['log_prefix'] = "no"
            mydict['disabled'] = "false"
            mydict['action'] = "mark-routing"
            myconfig.append(mydict)

            #Create rule to disable core transit if not available

            mydict={}
            mydict['comment'] = f"netwatch_core_transit_{my_core_transit['transit_device']}"
            mydict['resource'] = '/tool/netwatch'
            mydict['host'] = my_core_transit['ipv4']
            mydict['interval'] = "10s"
            mydict['down_script'] = f"/ip firewall mangle disable [find comment=\"core_transit_{my_core_transit['transit_device']}_mark\"];"
            mydict['up_script'] = f"/ip firewall mangle enable [find comment=\"core_transit_{my_core_transit['transit_device']}_mark\"];"
            myconfig.append(mydict)
    return myconfig
