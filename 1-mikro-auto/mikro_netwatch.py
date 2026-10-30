from dotenv import load_dotenv
import os
import logging

load_dotenv()

mqtt_user = os.environ.get("MQTT_USER")
mqtt_pass = os.environ.get("MQTT_PASSWORD")
#MQTT broker the routers publish the netwatch rtt to (devices with mqtt_netwatch_monitor: true)
MQTT_SERVER = os.environ.get("MQTT_SERVER")
MQTT_PORT = os.environ.get("MQTT_PORT") or "1883"


def load_config(device):

    my_config=[]

    #DNS

    #Create MQTT server
    if "mqtt_netwatch_monitor" in device.keys():
        if device['mqtt_netwatch_monitor'] and not MQTT_SERVER:
            logging.warning(f"{device['name']} -> mqtt_netwatch_monitor enabled but MQTT_SERVER not set, broker not created")
        elif device['mqtt_netwatch_monitor']:

            mydict={}
            mydict['resource'] = '/iot/mqtt/brokers'
            mydict['use_set'] = True
            mydict['name'] = "auto_mqtt_broker_1"
            mydict['client_id'] = f"{device['name']}"
            mydict['auto_connect'] = "true"
            mydict['username'] = mqtt_user
            mydict['password'] = mqtt_pass
            mydict['port'] = MQTT_PORT
            mydict['address'] = MQTT_SERVER
            my_config.append(mydict)

    #Create netwatch

    mydict={}
    mydict['comment'] = f"netwatch_dns1"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['dns1']
    mydict['interval'] = "10s"
    mydict['down_script'] = "/ip firewall nat enable [find comment=\"NAT_FALLBACK_DNS_1\"];"
    mydict['up_script'] = "/ip firewall nat disable [find comment=\"NAT_FALLBACK_DNS_1\"];"
    my_config.append(mydict)

    mydict={}
    mydict['comment'] = f"netwatch_dns2"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['dns2']
    mydict['interval'] = "10s"
    mydict['down_script'] = "/ip firewall nat enable [find comment=\"NAT_FALLBACK_DNS_2\"];"
    mydict['up_script'] = "/ip firewall nat disable [find comment=\"NAT_FALLBACK_DNS_2\"];"
    my_config.append(mydict) 

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

    my_config.append(mydict) 

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

    my_config.append(mydict) 

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
    my_config.append(mydict)

    mydict={}
    mydict['comment'] = f"netwatch_tcp_dns_2"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['dns2']
    mydict['interval'] = "30s"
    mydict['type'] = "tcp-conn"
    mydict['port'] = "53"
    my_config.append(mydict)

    mydict={}
    mydict['comment'] = f"netwatch_internet1"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['internet_icmp_check1']
    mydict['type'] = "icmp"
    if 'mqtt_netwatch_monitor' in device.keys():
        if device['mqtt_netwatch_monitor']:
            mydict['interval'] = "30s"
            mydict['test_script'] = f"\
/iot mqtt publish message=$\"rtt-avg\" broker=\"auto_mqtt_broker_1\" topic=\"mikrotik/rtt-avg/{device['name']}/internet1\"\r\
\n"
        else:
            mydict['interval'] = "30s"
            mydict['test_script'] = "# no test configure"
    else:
        mydict['interval'] = "30s"
        mydict['test_script'] = "# no test configure"
    my_config.append(mydict)

    mydict={}
    mydict['comment'] = f"netwatch_internet2"
    mydict['resource'] = '/tool/netwatch'
    mydict['host'] = device['internet_icmp_check2']
    mydict['type'] = "icmp"
    if 'mqtt_netwatch_monitor' in device.keys():
        if device['mqtt_netwatch_monitor']:
            mydict['interval'] = "30s"
            mydict['test_script'] = f"\
/iot mqtt publish message=$\"rtt-avg\" broker=\"auto_mqtt_broker_1\" topic=\"mikrotik/rtt-avg/{device['name']}/internet2\"\r\
\n"
        else:
            mydict['interval'] = "30s"
            mydict['test_script'] = "# no test configure"
    else:
        mydict['interval'] = "30s"
        mydict['test_script'] = "# no test configure"

    my_config.append(mydict)

    return my_config




