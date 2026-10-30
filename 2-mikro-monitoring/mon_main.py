from dotenv import load_dotenv
import os
import logging
import mon_shared
import mon_monitors

load_dotenv()
micro_user = os.environ.get("MIKRO_READ_USER")
micro_pass = os.environ.get("MIKRO_READ_PASSWORD")
debugmode = os.environ.get("DEBUGMODE")
inventory_path = os.environ.get("INVENTORY")


#CONFIG FOR TEST
if debugmode:
    logging.basicConfig(level=logging.INFO)
    prod=False
else:
    logging.basicConfig(level=logging.INFO)
    prod=False





if __name__ == '__main__':

    #Global metrics:
    global_metrics = {'vpn_infra_peers':0, 'vpn_infra_down_peers':0,'ipv4_dhcp_leases':0, 'sites_online':0, 'site_offline':0, 'authusers':0 , 'vpn_users_up':0 }

    #Get inventory
    my_inventory = mon_shared.load_inventory(inventory_path)
    for device in my_inventory:
        if ((device['role'] == "core" or device['role'] == "edge") and device['enabled'] and device['monitoring']):
            #Monitor wg
            
            #MANUAL
            mon_monitors.monitorDevice(device,global_metrics)

            #CREATE PROCESS
            #p = Process(target = mon_monitors.monitorDevice, args=(device,))
            #p.start()
    
    #Send global metrics
    mon_shared.sendToInflux([\
f"mikro_global vpn_infra_peers={global_metrics['vpn_infra_peers']},vpn_infra_down_peers={global_metrics['vpn_infra_down_peers']},ipv4_dhcp_leases={global_metrics['ipv4_dhcp_leases']},\
sites_online={global_metrics['sites_online']},site_offline={global_metrics['site_offline']},authusers={global_metrics['authusers']},vpn_users_up={global_metrics['vpn_users_up']}"])
    logging.info (f"Monitoring Global Data")
    logging.info (f"----DONE")

    #



