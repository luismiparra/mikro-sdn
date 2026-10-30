
import os
from dotenv import load_dotenv
import yaml
from yaml.loader import SafeLoader
import ipaddress




load_dotenv()

pathconfig = os.environ.get("CONFIG")
path_secrets = os.environ.get("SECRETS")
netbox_tag= os.environ.get("NETBOX_TAG")
netbox_global_tag= "MSDN-GLOBAL"
#NETBOX_DRYRUN=1 logs what would be created/updated/deleted without writing to NetBox
dry_run = os.environ.get("NETBOX_DRYRUN", "").lower() in ("1", "true", "yes")


def load_inventory():
    #Create list
    list=[]

    #Load all files config. Sorted to keep the order independent of the filesystem
    for filename in sorted(os.listdir(f"{pathconfig}/inventory")):
        #Skip non-inventory files (e.g. .DS_Store, editor temp files)
        if not filename.endswith((".yml", ".yaml")):
            continue
        #Open each file and load data
        with open(f"{pathconfig}/inventory/{filename}") as file:
            data = yaml.load(file, Loader=SafeLoader)
            #For each key in yml
            for key in data:
                for rule in data[key]:
                    rule['role']=key
                    list.append(rule)
    return list 

def calculate_ipv4_3octect(base_subnet, id_value):
    # Parse the base subnet
    base_network = ipaddress.IPv4Network(base_subnet)
    
    # Check if ID is valid (0 to 255 for the 3rd octet)
    if id_value < 0 or id_value > 255:
        raise ValueError("ID must be between 0 and 255")
    
    # Extract the base IP (10.21.0.0) and convert it to a list of octets
    base_ip = base_network.network_address
    octets = str(base_ip).split('.')
    
    # Replace the third octet with the given ID
    octets[2] = str(id_value)
    
    # Reconstruct the new subnet (e.g., 10.21.id.0/24)
    new_subnet = f"{'.'.join(octets)}/24"
    
    return new_subnet


def calculate_ipv6_subnet_7hextet(base_subnet, id_value):
    # Parse the base IPv6 network
    base_network = ipaddress.IPv6Network(base_subnet)
    
    # Check if the ID is valid (0 to 65535 for the 7th hextet in IPv6 /96 to /112 conversion)
    if id_value < 0 or id_value > 65535:
        raise ValueError("ID must be between 0 and 65535")
    
    # Extract the base network address
    base_ip = base_network.network_address
    
    # Convert the address to a list of hextets (parts of the IPv6 address)
    hextets = base_ip.exploded.split(':')
    
    # Modify the 7th hextet (6th index) with the given ID (convert ID to hexadecimal)
    hextets[6] = f"{id_value:x}"
    
    # Rebuild the new subnet in /112 format
    new_subnet = f"{':'.join(hextets)}/112"
    
    return new_subnet

def generate_ip_list(ip: str, start_ip: int, num_ips: int, mask):
    # Create a network object from the IP and mask
    network = ipaddress.ip_network(ip, strict=False)
    # Convert the network to a list of all available hosts
    all_hosts = list(network.hosts())
    # Ensure the start IP and number of IPs are within the network range
    if start_ip < 0 or start_ip + num_ips > len(all_hosts):
        raise ValueError("Start IP and number of IPs exceed the available range in the network.")
    # Generate the list of IPs starting from the given start_ip index
    selected_ips = all_hosts[start_ip:start_ip + num_ips]
    # Format the IPs with the subnet mask and return as a list of strings
    result = [f"{str(ip)}/{mask}" for ip in selected_ips]
    return result

