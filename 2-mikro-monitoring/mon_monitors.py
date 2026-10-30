from dotenv import load_dotenv
import os
import mon_shared
import logging
import pandas as pd 
from icmplib import ping

WIREGUARD_KEEPALIVE_LIMIT = 600
INTERNET_HOSTS_IPV4 = ['1.1.1.1','8.8.8.8']
INTERNET_HOSTS_IPV6 = ['2001:4860:4860::8888', '2606:4700:4700::1111']

LIST_INTERFACES_IPV6_INTERNET_PING = ['1safe','2dmz','3services','4guest','5dev']
LIST_INTERFACES_IPV4_VPNINTERNET_PING = ['4guest']

ICMP_TIMEOUT = '1'
ICMP_COUNT = 3

load_dotenv()
micro_user = os.environ.get("MIKRO_READ_USER")
micro_pass = os.environ.get("MIKRO_READ_PASSWORD")
debugmode = os.environ.get("DEBUGMODE")


def monitorDevice(device,global_metrics):

    #Check if device is alive.
    pingdevice = ping(device['mgmt_int'], count=1)

    if pingdevice.is_alive:
        logging.info (f"Monitoring device --> {device['name']}")
        global_metrics['sites_online']+=1
        my_measurements = []

        #------------MONITORS
        my_measurements.extend(wireguard_peer_status(device,global_metrics))
        my_measurements.extend(netwatch_status(device))
        my_measurements.extend(dhcp_status(device,global_metrics))
        my_measurements.extend(mikro_global_checks(device,global_metrics))
        #my_measurements.extend(wireguard_ping_bgp(device))
        #my_measurements.extend(internet_ping(device))

        #------------SEND TO INFLUX
        if my_measurements:
            mon_shared.sendToInflux(my_measurements)
            my_measurements = []
    
    else:
        logging.error (f"Monitoring ERROR TO DEVICE --> {device['name']}")
        global_metrics['site_offline']+=1

#------------MONITOR mikro global checks
def mikro_global_checks(device,global_metrics):
    list_monitors = []
    mysessions = mon_shared.getItem(device,"/user-manager/session")
    if mysessions:
        for item in mysessions:
            if 'active' in item.keys():
                if (item['active']=="true"):
                    global_metrics['authusers']+=1


    return list_monitors

#------------MONITOR leases
def dhcp_status(device,global_metrics):
    list_monitors = []
    myleases = mon_shared.getItem(device,"/ip/dhcp-server/lease")
    if myleases:
        for item in myleases:
            if 'status' in item.keys():
                match item['status']:
                    case 'bound':
                        global_metrics['ipv4_dhcp_leases']+=1

#CODE NOT WORKING just here waiting to implement via mongodb
#                        if 'active-client-id' in item.keys():
#                            myactiveclient = item['active-client-id']
#                        else:
#                            myactiveclient = 'none'
#                        if 'host-name' in item.keys():
#                            myhostname = item['host-name']
#                        else:
#                            myactiveclient = 'none'
#                        list_monitors.append(\
#f"mikro_dhcp_bound,host={device['name']},role={device['role']},mac=mac_{item['mac-address']},server={item['server']} active-address=ip_{item['active-address']},active-client-id=cid_{myactiveclient},host-name={myhostname},\
#last-seen={str(pd.Timedelta(item['last-seen']).total_seconds())},expires-after={str(pd.Timedelta(item['expires-after']).total_seconds())},dynamic={item['dynamic']}")
                    case _:
                        pass                        

    return list_monitors

#------------MONITOR NETWATCH
def netwatch_status(device):
    list_monitors = []
    mynetwatch = mon_shared.getItem(device,"/tool/netwatch")

    if mynetwatch:
        for item in mynetwatch:
            if 'type' in item.keys():
                match item['type']:
                    case 'simple':
                        list_monitors.append(f"mikro_netwatch_simple,host={device['name']},role={device['role']},name={item['comment']},dst_ip={item['host']} done-tests={item['done-tests']},failed-tests={item['failed-tests']}")
                    case 'icmp':
                        if item['status'] == 'up':
                            list_monitors.append(\
f"mikro_netwatch_icmp,host={device['name']},role={device['role']},name={item['comment']},dst_ip={item['host']} done-tests={item['done-tests']},failed-tests={item['failed-tests']},\
loss-count={item['loss-count']},loss-percent={item['loss-percent']},rtt-avg={str(pd.Timedelta(item['rtt-avg']).total_seconds())},rtt-jitter={str(pd.Timedelta(item['rtt-jitter']).total_seconds())},\
rtt-max={str(pd.Timedelta(item['rtt-max']).total_seconds())},rtt-min={str(pd.Timedelta(item['rtt-min']).total_seconds())},rtt-stdev={str(pd.Timedelta(item['rtt-stdev']).total_seconds())}")
                        else:
                            list_monitors.append(\
f"mikro_netwatch_icmp,host={device['name']},role={device['role']},name={item['comment']},dst_ip={item['host']} done-tests={item['done-tests']},failed-tests={item['failed-tests']},\
loss-count={item['loss-count']},loss-percent={item['loss-percent']}")                            
                    case 'tcp-conn':
                        list_monitors.append(f"mikro_netwatch_tcp,host={device['name']},role={device['role']},name={item['comment']},dst_ip={item['host']} done-tests={item['done-tests']},failed-tests={item['failed-tests']},tcp-connect-time={str(pd.Timedelta(item['tcp-connect-time']).total_seconds())}")
                    case _:
                        pass    

    return list_monitors


#------------MONITOR WIREGUARD PEERS
def wireguard_peer_status(device,global_metrics):
    #We get wireguard peers list
    list_monitors = []
    mypeers = mon_shared.getItem(device,"/interface/wireguard/peers")

    #Just monitor main peers
    if mypeers:
        for item in mypeers:

            #Checks for VPN INFRA
            if "main" in item['interface']:
                #valid peer then evaluate it
                global_metrics['vpn_infra_peers']+=1
                if 'last-handshake' in item.keys():
                    logging.debug (f"Checking peers for device {device['name']}")
                    if mon_shared.convert_to_seconds(item['last-handshake']) < WIREGUARD_KEEPALIVE_LIMIT:
                        
                        list_monitors.append(f"mikro_wg_peer_status,host={device['name']},role={device['role']},name={item['interface']} healthy={True},last-handshake={str(pd.Timedelta(item['last-handshake']).total_seconds())}")
                    else:
                        list_monitors.append(f"mikro_wg_peer_status,host={device['name']},role={device['role']},name={item['interface']} healthy={False},last-handshake={str(pd.Timedelta(item['last-handshake']).total_seconds())}")
                        global_metrics['vpn_infra_down_peers']+=1
                else:
                    list_monitors.append(f"mikro_wg_peer_status,host={device['name']},role={device['role']},name={item['interface']} healthy={False},last-handshake=-1")
                    global_metrics['vpn_infra_down_peers']+=1

            #Checks for VPN users
            elif "vpn_admin" in item['interface'] or "vpn_user" in item['interface']:
                if 'last-handshake' in item.keys():
                    logging.debug (f"Checking peers vpn users for device {device['name']}")
                    if mon_shared.convert_to_seconds(item['last-handshake']) < WIREGUARD_KEEPALIVE_LIMIT:
                        global_metrics['vpn_users_up']+=1

    return list_monitors

#------------PING WG PEERS
def wireguard_ping_bgp(device):
    list_monitors = []
    mybgppeers = mon_shared.getItem(device,"/routing/bgp/connection")
    if mybgppeers:
        for item in mybgppeers:
            myrequest = {'address':item['remote.address'],'ttl':'1','count':ICMP_COUNT,'interval':ICMP_TIMEOUT}
            result = mon_shared.postItem(device,"/ping",myrequest)
            result = result[ICMP_COUNT-1]
            if 'time' in result.keys():
                list_monitors.append(f"mikro_bgp_icmp,host={device['name']},role={device['role']},name={item['comment']} healthy={True},response={float(pd.Timedelta(result['time']).total_seconds())},packet_lost={result['packet-loss']}")
            else:
                list_monitors.append(f"mikro_bgp_icmp,host={device['name']},role={device['role']},name={item['comment']} healthy={False},packet_lost={result['packet-loss']}")
        
        return list_monitors


#------------PING INTERNET
def internet_ping(device):
    list_monitors = []
    ipv4list = mon_shared.getItem(device,"/ip/address")
    ipv6list = mon_shared.getItem(device,"/ipv6/address")
    if ipv4list and ipv6list:

        #CHECK DIRECT INTERNET IPV4
        for destination_ip in INTERNET_HOSTS_IPV4:
            myrequest = {'address':destination_ip,'ttl':'64','count':ICMP_COUNT,'interval':ICMP_TIMEOUT}
            result = mon_shared.postItem(device,"/ping",myrequest)
            result = result[ICMP_COUNT-1]
            if 'time' in result.keys():
                list_monitors.append(f"mikro_internet_ipv4_icmp,host={device['name']},role={device['role']},name=default,dst={destination_ip} healthy={True},response={float(pd.Timedelta(result['time']).total_seconds())},packet_lost={result['packet-loss']}")
            else:
                list_monitors.append(f"mikro_internet_ipv4_icmp,host={device['name']},role={device['role']},name=default,dst={destination_ip} healthy={False},packet_lost={result['packet-loss']}")

        #CHECK DIRECT INTERNET IPV6
        for interface_ip in ipv6list:
            if interface_ip['interface'] in LIST_INTERFACES_IPV6_INTERNET_PING and 'comment' in interface_ip.keys():
                for destination_ip in INTERNET_HOSTS_IPV6:
                    myrequest = {'address':destination_ip,'ttl':'64','count':ICMP_COUNT,'src-address':interface_ip['address'].split('/')[0],'interval':ICMP_TIMEOUT}
                    result = mon_shared.postItem(device,"/ping",myrequest)
                    result = result[ICMP_COUNT-1]
                    if 'time' in result.keys():
                        list_monitors.append(f"mikro_internet_ipv6_icmp,host={device['name']},role={device['role']},name={interface_ip['interface']},dst={destination_ip} healthy={True},response={float(pd.Timedelta(result['time']).total_seconds())},packet_lost={result['packet-loss']}")
                    else:
                        list_monitors.append(f"mikro_internet_ipv6_icmp,host={device['name']},role={device['role']},name={interface_ip['interface']},dst={destination_ip} healthy={False},packet_lost={result['packet-loss']}")

        #CHECK DIRECT VPNINTERNET IPV4 
        for interface_ip in ipv4list:
            if interface_ip['interface'] in LIST_INTERFACES_IPV4_VPNINTERNET_PING and 'comment' in interface_ip.keys():
                for destination_ip in INTERNET_HOSTS_IPV4:
                    myrequest = {'address':destination_ip,'ttl':'64','count':ICMP_COUNT,'src-address':interface_ip['address'].split('/')[0],'interval':ICMP_TIMEOUT}
                    result = mon_shared.postItem(device,"/ping",myrequest)
                    result = result[ICMP_COUNT-1]
                    if 'time' in result.keys():
                        list_monitors.append(f"mikro_vpninternet_ipv4_icmp,host={device['name']},role={device['role']},name={interface_ip['interface']},dst={destination_ip} healthy={True},response={float(pd.Timedelta(result['time']).total_seconds())},packet_lost={result['packet-loss']}")
                    else:
                        list_monitors.append(f"mikro_vpninternet_ipv4_icmp,host={device['name']},role={device['role']},name={interface_ip['interface']},dst={destination_ip} healthy={False},packet_lost={result['packet-loss']}")            


        return list_monitors

    


