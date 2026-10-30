
from slugify import slugify
from dotenv import load_dotenv
import json
import os
import netbox_get
import netbox_shared

load_dotenv()

pathconfig = os.environ.get("CONFIG")
path_secrets = os.environ.get("SECRETS")


#-----------INTENDED


def get_intended_interfaces(nb, my_inventory):
    interfaces_list = []
    for device in my_inventory:
        if os.path.exists(f"{path_secrets}/proposed/{device.get('name')}_global.json"):
            with open(f"{path_secrets}/proposed/{device.get('name')}_global.json") as file1:
                deviceconfig = json.load(file1)
                file1.close()
                device_id = netbox_get.get_device_from_name(nb,slugify(device.get('name')))
                tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_tag)
                for item in deviceconfig:
                    if item['resource'] == '/interface/vlan' or item['resource'] == '/interface/vxlan' or item['resource'] == '/interface/wireguard':
                        
                        if 'mgmt' in item.get('name'):
                            mgmt_only = True
                        else:
                            mgmt_only = False

                        interface_data = {
                            'device': device_id,
                            'name': f"{device.get('name')}_{item.get('name')}",
                            'type':'virtual','description': f"{item['resource']} -- {item.get('comment')}",
                            'tags': [tag.id],
                            'mgmt_only': mgmt_only
                        }
                        interfaces_list.append(interface_data)
    return interfaces_list


def get_intended_ip_addresses(nb, my_inventory):
    ip_addreses_list = []
    for device in my_inventory:
        if os.path.exists(f"{path_secrets}/proposed/{device.get('name')}_global.json"):
            with open(f"{path_secrets}/proposed/{device.get('name')}_global.json") as file1:
                deviceconfig = json.load(file1)
                file1.close()
                tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_tag)

                #Address at interfaces
                for item in deviceconfig:
                    if item['resource'] == '/ip/address' or item['resource'] == '/ipv6/address':
                        ip_address_data = {
                            'address': item.get('address'),
                            'tags': [tag.id], 
                            'status':'active',
                            'dns_name':f"{slugify(item['interface'])}-{device.get('name')}.{device.get('domain')}.", 
                            'description': f"IP -- {device.get('name')} -- {item.get('comment')}",
                        }
                        interface_id = netbox_get.get_interface_id_from_name(nb,f"{device.get('name')}_{item.get('interface')}")
                        if interface_id:
                            ip_address_data['assigned_object_id'] = interface_id
                            ip_address_data['assigned_object_type'] = 'dcim.interface'

                        ip_addreses_list.append(ip_address_data)

                #Address at WG Client VPN
                vpns_list = device.get('wg-vpn')
                if not vpns_list:
                    continue
                for wg_vpn in vpns_list:
                    ip_vpn_list = netbox_shared.generate_ip_list( netbox_shared.calculate_ipv4_3octect(device.get('subnetv4'), wg_vpn['subnet']),1, wg_vpn.get('number_client'),24 )
                    for ip_vpn in ip_vpn_list:
                        ip_address_data = {
                            'address': ip_vpn,
                            'tags': [tag.id], 
                            'status':'active',
                            'description': f"IP WG Client {device.get('name')} -- {wg_vpn.get('name')}",
                        }
                        ip_addreses_list.append(ip_address_data)
                    ip_vpn_list = netbox_shared.generate_ip_list( netbox_shared.calculate_ipv6_subnet_7hextet(device.get('subnetv6'), wg_vpn['subnet']),1, wg_vpn.get('number_client'),112 )
                    for ip_vpn in ip_vpn_list:
                        ip_address_data = {
                            'address': ip_vpn,
                            'tags': [tag.id], 
                            'status':'active',
                            'description': f"IP WG Client {device.get('name')} -- {wg_vpn.get('name')}",
                        }
                        ip_addreses_list.append(ip_address_data)


    return ip_addreses_list

def get_intended_ip_ranges(nb, my_inventory):
    ip_ranges_list = []

    for device in my_inventory:
        if os.path.exists(f"{path_secrets}/proposed/{device.get('name')}_global.json"):
            with open(f"{path_secrets}/proposed/{device.get('name')}_global.json") as file1:
                deviceconfig = json.load(file1)
                file1.close()
                tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_tag)

                #Address at interfaces
                for item in deviceconfig:
                    if item['resource'] == '/ip/pool':
                        ip_range_data = {
                            'start_address': f"{item.get('ranges').split('-',-1)[0]}/{item.get('name').split('/',-1)[1]}",
                            'end_address':  f"{item.get('ranges').split('-',-1)[1]}/{item.get('name').split('/',-1)[1]}",
                            'tags': [tag.id], 
                            'mark_utilized': True,
                            'status':'active',
                        }
                        ip_ranges_list.append(ip_range_data)

    return ip_ranges_list