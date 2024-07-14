import mikro_shared

def loadConfig(device):

    myconfig=[]

    #DNS

    #Create netwatch

    mydict={}
    mydict['comment'] = f"netwatch_dns1"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['dns1']
    mydict['interval'] = "10s"
    mydict['down_script'] = "/ip firewall nat enable [find comment=\"NAT_FALLBACK_DNS_1\"];"
    mydict['up_script'] = "/ip firewall nat disable [find comment=\"NAT_FALLBACK_DNS_1\"];"
    myconfig.append(mydict)

    mydict={}
    mydict['comment'] = f"netwatch_dns2"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['dns2']
    mydict['interval'] = "10s"
    mydict['down_script'] = "/ip firewall nat enable [find comment=\"NAT_FALLBACK_DNS_2\"];"
    mydict['up_script'] = "/ip firewall nat disable [find comment=\"NAT_FALLBACK_DNS_2\"];"
    myconfig.append(mydict) 

    #Create firewall rules   

    mydict={}
    mydict['comment'] = f"NAT_FALLBACK_DNS_1"
    mydict['resource'] = '/ip/firewall/nat'
    mydict['order'] = 'top'
    mydict['action'] = 'dst-nat'
    mydict['chain'] = 'dstnat'
#    mydict['disabled'] = 'true'
    mydict['dst_address'] = device['dns1']
    mydict['dst_port'] = '53'
    mydict['protocol'] = 'udp'
    mydict['src_address'] = '10.0.0.0/8'
    mydict['to_addresses'] = device['dns1_fallback']
    mydict['to_ports'] = '53'
    mydict['log'] = 'false'

    myconfig.append(mydict) 

    mydict={}
    mydict['comment'] = f"NAT_FALLBACK_DNS_2"
    mydict['resource'] = '/ip/firewall/nat'
    mydict['order'] = 'top'
    mydict['action'] = 'dst-nat'
    mydict['chain'] = 'dstnat'
#    mydict['disabled'] = 'true'
    mydict['dst_address'] = device['dns2']
    mydict['dst_port'] = '53'
    mydict['protocol'] = 'udp'
    mydict['src_address'] = '10.0.0.0/8'
    mydict['to_addresses'] = device['dns2_fallback']
    mydict['to_ports'] = '53'
    mydict['log'] = 'false'

    myconfig.append(mydict) 

#--------------work in progress
    #---Internet monitoring
    #--Local DNS check
    mydict={}
    mydict['comment'] = f"netwatch_tcp_dns_1"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['dns1']
    mydict['interval'] = "30s"
    mydict['type'] = "tcp-conn"
    mydict['port'] = "53"
    myconfig.append(mydict)

    mydict={}
    mydict['comment'] = f"netwatch_tcp_dns_2"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['dns2']
    mydict['interval'] = "30s"
    mydict['type'] = "tcp-conn"
    mydict['port'] = "53"
    myconfig.append(mydict)

    mydict={}
    mydict['comment'] = f"netwatch_internet1"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['internet_icmp_check1']
    mydict['interval'] = "30s"
    mydict['type'] = "icmp"
    myconfig.append(mydict)

    mydict={}
    mydict['comment'] = f"netwatch_internet2"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['internet_icmp_check2']
    mydict['interval'] = "30s"
    mydict['type'] = "icmp"
    myconfig.append(mydict)

    return myconfig




