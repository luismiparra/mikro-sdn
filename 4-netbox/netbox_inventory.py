
import netbox_external_api
from slugify import slugify
import netbox_get
import netbox_shared
import ipaddress
from concurrent.futures import ThreadPoolExecutor

SERIAL_WORKERS = 16




#-----------INVENTORY

def get_inventory_prefixes(nb, inventory):
    prefixes_list=[]
    for device in inventory:
        site_id = netbox_get.get_site_id_from_slug(nb, slugify(device.get('location')))
        tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_tag)
        #Get General Prefix v4
        prefix_data = {
            "prefix": device.get('subnetv4'),
            "site": site_id,
            "status": "active",
            "description": f"{device.get('location')} main ipv4 subnet",      # Optional: Add a description
            'tags': [tag.id],
        }
        prefixes_list.append(prefix_data)

        #Get General Prefix v6
        prefix_data = {
            "prefix": str(ipaddress.IPv6Network(device.get('subnetv6'),strict=False)),
            "site": site_id,
            "status": "active",
            "description": f"{device.get('location')} main ipv6 subnet",      # Optional: Add a description
            'tags': [tag.id],
        }
        prefixes_list.append(prefix_data)

        #Get VLANS
        vlans_list=[]
        lan = device.get('lan')
        if not lan:
            continue
        vlans_list = lan.get('vlans')
        if not vlans_list:
            continue

        for vlan in vlans_list:
            prefix_data = {
                "prefix": netbox_shared.calculate_ipv4_3octect(device.get('subnetv4'), vlan['id']),
                "site": site_id,
                "vlan": netbox_get.get_vlan_vid_from_name(nb,vlan['name']),
                "status": "active",
                "description": f"Subnet device {device.get('name')} vlan {vlan['name']}",
                'tags': [tag.id],
            }
            prefixes_list.append(prefix_data)

            if vlan.get('ipv6'):
                prefix_data = {
                    "prefix": str(ipaddress.IPv6Network(netbox_shared.calculate_ipv6_subnet_7hextet(device.get('subnetv6'), vlan['id']), strict=False)),
                    "site": site_id,
                    "vlan": netbox_get.get_vlan_vid_from_name(nb,vlan['name']),
                    "status": "active",
                    "description": f"Subnet device {device.get('name')} vlan {vlan['name']}",
                    'tags': [tag.id],
                }
            prefixes_list.append(prefix_data)

        #Get main fabrid wg static 250 subnet

            prefix_data = {
                "prefix": netbox_shared.calculate_ipv4_3octect(device.get('subnetv4'), 250),
                "site": site_id,
                "status": "active",
                "description": f"WG main fabric device {device.get('name')} ",
                'tags': [tag.id],
            }
            prefixes_list.append(prefix_data)

            prefix_data = {
                "prefix": str(ipaddress.IPv6Network(netbox_shared.calculate_ipv6_subnet_7hextet(device.get('subnetv6'), 250))),
                "site": site_id,
                "status": "active",
                "description": f"WG main fabric device {device.get('name')} ",
                'tags': [tag.id],
            }
            prefixes_list.append(prefix_data)

        #Get WG VPN
        vpns_list = device.get('wg-vpn')
        if not vpns_list:
            continue

        for wg_vpn in vpns_list:
            prefix_data = {
                "prefix": netbox_shared.calculate_ipv4_3octect(device.get('subnetv4'), wg_vpn['subnet']),
                "site": site_id,
                "status": "active",
                "description": f"Client WG VPN ipv4 - device {device.get('name')} name {wg_vpn['name']}",
                'tags': [tag.id],
            }
            prefixes_list.append(prefix_data)

            if vlan.get('ipv6'):
                prefix_data = {
                    "prefix": str(ipaddress.IPv6Network(netbox_shared.calculate_ipv6_subnet_7hextet(device.get('subnetv6'), wg_vpn['subnet']), strict=False)),
                    "site": site_id,
                    "status": "active",
                    "description": f"Client WG VPN ipv6 - device {device.get('name')} name {wg_vpn['name']}",
                    'tags': [tag.id],
                }
                prefixes_list.append(prefix_data)



    return prefixes_list


def get_inventory_vlans(nb, inventory):
    vlans_list=[]
    for device in inventory:
        lan = device.get('lan')
        if not lan:
            continue
        vlans = lan.get('vlans')
        if not vlans:
            continue
        for vlan in vlans:
            if not any(existing_vlan['id'] == vlan['id'] for existing_vlan in vlans_list):
                vlans_list.append(vlan)
    return vlans_list

def get_inventory_regions(nb, inventory):
    regions=[]
    for device in inventory:
        netbox = device.get('netbox')
        if not netbox:
            continue  # No 'netbox' block: skip the device

        organization = netbox.get('organization')
        if not organization:
            continue  # No 'organization' block: skip the device

        region = organization.get('region')
        if region:
            if region not in regions:
                regions.append(region)
    return regions

def get_inventory_device_roles(nb, inventory):
    roles=[]
    for device in inventory:

        role = device.get('role')
        if role:
            if role not in roles:
                roles.append(role)
    return roles

def get_device_serial(device):
    if device.get('role') == 'core' or device.get('role') == 'edge':
        match device.get("netbox", {}).get("device", {}).get("device_model"):
            case "mikrotik-chr":
                response = netbox_external_api.getMikrotikApiItem(device,"/system/license")
                if response:
                    return response.get('system-id')
            case _:
                response = netbox_external_api.getMikrotikApiItem(device,"/system/routerboard")
                if response:
                    return response.get('serial-number')
    return "none"

def get_inventory_devices(nb, inventory):
    #Serials are read from every router in parallel instead of one after the other
    with ThreadPoolExecutor(max_workers=SERIAL_WORKERS) as executor:
        serials = list(executor.map(get_device_serial, inventory))

    devices=[]
    for device, serial in zip(inventory, serials):
        device['serial'] = serial
        devices.append(device)


    return devices

def get_inventory_asns(nb, inventory):
    asns=[]
    for device in inventory:
        asn = device.get('as')
        if asn:
            if asn not in asns:
                if int(asn) > 64512 and int(asn) < 65512:
                    tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_tag)
                    asns.append({'asn':asn, 'rir':netbox_get.get_rir_id_from_slug(nb,'private'),  "tags": [tag.id] })
    return asns

def get_inventory_sites(nb, inventory):
    sites=[]
    for device in inventory:

        asns = []
        asns.append(netbox_get.get_asn_id_from_number(nb,device.get('as')))
        tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_tag)
        if device.get('enabled'):
            status = "active"
        else:
            status = "staging"
        region = netbox_get.get_region_id_from_name(nb, device.get("netbox", {}).get("organization", {}).get("region"))
        site_group = netbox_get.get_site_groups_id_from_slug(nb, device.get("netbox", {}).get("organization", {}).get("site_group"))

        
        sites.append({'name':device.get('location'), 'slug':slugify(device.get('location')), 'description':device.get('description'), 'status':status, 'region':region, 'asns':asns,  "tags": [tag.id], 'group':site_group})
    return sites