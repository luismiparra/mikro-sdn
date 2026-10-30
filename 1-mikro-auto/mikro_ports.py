#Objective: read only report of the wireguard wan mesh: listen ports and transit ips that
#the automation would push, without touching any device and without needing the secrets.
#The slot of every link comes from the wan_order pinned in the inventory, so this report is
#exact: it uses the same wan_pairs/conn_slot the generator uses.
#
#Usage:
#   CONFIG=config python3 1-mikro-auto/mikro_ports.py
#   CONFIG=config python3 1-mikro-auto/mikro_ports.py lab-mikro4
#
#Optional second argument 'csv' prints the same data as csv.

import os
import sys
import logging
from dotenv import load_dotenv

import mikro_shared
import mikro_wan

load_dotenv()

logging.basicConfig(level=logging.WARNING)

WG_PORT_BASE = 51820


def collect(inventory):

    #Objective: one row per end of every link of the mesh

    core_devices = []
    edge_devices = []

    for device in inventory:
        if device['enabled']:
            if device['role'] == "core":
                core_devices.append(device)
            if device['role'] == "edge" or device['role'] == "external_edge":
                edge_devices.append(device)

    #Transit subnets are derived from the device subnets, needed to show the transit ips
    for device in inventory:
        mikro_shared.prepare_sdn(device)

    rows = []

    for device1, device2 in mikro_wan.wan_pairs(core_devices, edge_devices):
        slot1 = mikro_wan.conn_slot(device1, device2)
        slot2 = mikro_wan.conn_slot(device2, device1)

        #The transit pair of a link always comes from device1, both ends share it
        transit = device1[mikro_wan.TRANSIT_NETWORK_V4][slot1]
        prefix = transit['subnet'].prefixlen

        rows.append({'device': device1['name'], 'peer': device2['name'],
                     'slot': slot1, 'listen_port': WG_PORT_BASE + slot1,
                     'peer_port': WG_PORT_BASE + slot2,
                     'transit_ip': f"{transit['ip1']}/{prefix}"})

        rows.append({'device': device2['name'], 'peer': device1['name'],
                     'slot': slot2, 'listen_port': WG_PORT_BASE + slot2,
                     'peer_port': WG_PORT_BASE + slot1,
                     'transit_ip': f"{transit['ip2']}/{prefix}"})

    return rows


def report(rows, inventory, only_device):

    order = {device['name']: device['wan_order'] for device in inventory}

    for name in sorted(order, key=lambda item: order[item]):
        if only_device and name != only_device:
            continue

        links = [row for row in rows if row['device'] == name]
        if not links:
            continue

        print(f"\n{name}  (wan_order {order[name]})")
        print(f"  {'peer':<16} {'slot':>4} {'listen':>7} {'peer port':>10}  transit v4")
        for link in sorted(links, key=lambda item: item['slot']):
            print(f"  {link['peer']:<16} {link['slot']:>4} {link['listen_port']:>7} "
                  f"{link['peer_port']:>10}  {link['transit_ip']}")

    if only_device and only_device not in order:
        print(f"Device not found in inventory -> {only_device}")


def report_csv(rows):

    print("device,peer,slot,listen_port,peer_port,transit_v4")
    for row in sorted(rows, key=lambda item: (item['device'], item['slot'])):
        print(f"{row['device']},{row['peer']},{row['slot']},"
              f"{row['listen_port']},{row['peer_port']},{row['transit_ip']}")


if __name__ == "__main__":

    only_device = None
    as_csv = False

    for arg in sys.argv[1:]:
        if arg == 'csv':
            as_csv = True
        else:
            only_device = arg

    if not os.environ.get("CONFIG"):
        sys.exit("CONFIG not set. Use e.g. CONFIG=config")

    inventory = mikro_shared.load_inventory()
    rows = collect(inventory)

    if as_csv:
        report_csv(rows)
    else:
        report(rows, inventory, only_device)
