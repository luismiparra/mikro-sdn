import pynetbox
from dotenv import load_dotenv
import os
import sys
import logging
import time
import netbox_shared
import netbox_inventory
import netbox_intended
import netbox_api
import netbox_get

#The CI log formatter is shared with the mikro automation
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "1-mikro-auto"))
import mikro_log

load_dotenv()


netbox_url = os.environ.get("NETBOX_URL")
netbox_token = os.environ.get("NETBOX_TOKEN")
my_config = os.environ.get("CONFIG")
path_secrets = os.environ.get("SECRETS")
debugmode = os.environ.get("DEBUGMODE")

#CONFIG FOR TEST
if debugmode:
    mikro_log.setup(level=logging.INFO)
    prod=False
else:
    mikro_log.setup(level=logging.INFO)
    prod=False





def build_netbox():
    logging.info("NETBOX -> ------------------------START")
    started = time.monotonic()
    #threading=True reads the pages of large endpoints in parallel
    nb = pynetbox.api(netbox_url, token=netbox_token, threading=True)
    netbox_get.clear_cache()
    netbox_api.sync_results.clear()
    my_inventory=netbox_shared.load_inventory()


    #----CREATE STATIC OBJECTS Global_TAG
    logging.info ("NETBOX -> Static Objects")
    netbox_api.create_or_update_tag(nb, netbox_shared.netbox_tag)
    netbox_api.create_or_update_tag(nb, netbox_shared.netbox_global_tag)
    netbox_api.create_private_rir(nb) 
    netbox_api.create_site_groups(nb)


    #----REGIONS
    logging.info ("NETBOX -> Regions")
    regions = netbox_inventory.get_inventory_regions(nb, my_inventory)
    netbox_api.sync_regions(nb, regions)

    #----ASN
    logging.info ("NETBOX -> ASNs")
    asns = netbox_inventory.get_inventory_asns(nb, my_inventory)
    netbox_api.sync_asns(nb, asns)

    #----SITES
    logging.info ("NETBOX -> Sites")
    sites = netbox_inventory.get_inventory_sites(nb, my_inventory)
    netbox_api.sync_sites(nb, sites)

    #----DEVICES ROLES Global_TAG
    logging.info ("NETBOX -> Device Roles")
    roles = netbox_inventory.get_inventory_device_roles(nb, my_inventory)
    netbox_api.sync_roles(nb, roles)
    
    #----DEVICES 
    logging.info ("NETBOX -> Devices")
    devices = netbox_inventory.get_inventory_devices(nb, my_inventory)
    netbox_api.sync_devices(nb, devices)

    #----VLANS   Global_TAG
    logging.info ("NETBOX -> VLANS")
    vlans = netbox_inventory.get_inventory_vlans(nb, my_inventory)
    netbox_api.sync_vlans(nb, vlans)

    #--------------------UNIVERAL API FUNCTIONS STARTING HERE
    #----Interfaces
    logging.info ("NETBOX -> Interfaces")
    interfaces = netbox_intended.get_intended_interfaces(nb, my_inventory)
    netbox_api.sync_resources(nb, 'dcim', 'interfaces', interfaces, 'name', netbox_shared.netbox_tag)

    #----site prefix
    logging.info ("NETBOX -> Prefixes")
    prefixes = netbox_inventory.get_inventory_prefixes(nb, my_inventory)
    netbox_api.sync_resources(nb, 'ipam', 'prefixes', prefixes, 'prefix', netbox_shared.netbox_tag)

    #----site interfaces ip
    logging.info ("NETBOX -> IPs")
    ip_addresses  = netbox_intended.get_intended_ip_addresses(nb, my_inventory)
    netbox_api.sync_resources(nb, 'ipam', 'ip_addresses', ip_addresses, 'address', netbox_shared.netbox_tag)

    #----IP Ranges pool
    logging.info ("NETBOX -> IP Ranges")
    ip_ranges  = netbox_intended.get_intended_ip_ranges(nb, my_inventory)
    netbox_api.sync_resources(nb, 'ipam', 'ip_ranges', ip_ranges, 'start_address', netbox_shared.netbox_tag)

    #----VPN Tunnels

    #----PRIMARY IP FOR DEVICES

    #----OOB IP FOR DEVICES

    sync_report()
    logging.info(f"NETBOX -> ------------------------DONE in {time.monotonic() - started:.1f}s")

def sync_report():
    """Table of what every endpoint sync did. A cell shows done/planned when some failed."""
    def cell(done, planned):
        return f"{done}" if done == planned else f"❌ {done}/{planned}"

    rows = []
    for name, result, (create, update, delete), dry_run in netbox_api.sync_results:
        if dry_run:
            rows.append([name, f"🧪 {create}", f"🧪 {update}", f"🧪 {delete}", result['unchanged']])
        else:
            rows.append([name, cell(result['created'], create), cell(result['updated'], update),
                         cell(result['deleted'], delete), result['unchanged']])
    mikro_log.report("NETBOX -> Sync result", ["Resource", "➕ Created", "🔄 Updated", "🗑️ Deleted", "💤 Unchanged"], rows)

if __name__ == "__main__":
    build_netbox()







