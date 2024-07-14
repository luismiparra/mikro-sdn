# Important information:
## This script is totally experimental, use it at your own risk.
## I'm still working on adding documentation, examples and other parts that may not work.


# Configuration Guide for mikro-sdn inventory Config.

This documentation provides guidelines for configuring CORE/EDGE devices using the given YAML configuration structure. 
CORE devices are designed to allow transit and are required to have a public IP that accepts connections from other peers to facilitate underlay WireGuard (WG) tunnels. A full mesh topology is expected between all CORE devices.
EDGE devices will connect to each core.


# How to install and run offline: (no push to devices yet)
1. Install python > 3.12
1. Install OS dependencies (wireguard-tools )
1. Install python dependencies
1. Create your .env file (you can copy from )
1. run 1-mikro-sdn/mikro_main.py

# How to install and push config to devices
(to be documented)


## YAML Configuration Structure of inventory.yaml


Each CORE/EDGE device configuration includes several parameters as described below:

- **name**: The name of the router. (e.g., `"lab-mikro1"`)
- **site_id**: A unique ID for each site, ranging between 1 and 200.
- **enable_vxlan**: Enable VXLAN feature. (`true` or `false`)
- **enable_vxlan_to_vlan**: Add VXLAN to VLAN in bridge. (`true` or `false`)
- **role**: The device role, either `core` or `edge`. (e.g., `"core"`)
- **enabled**: Include the device as part of the WAN when generating WG tunnels. (`True` or `False`)
- **push_config**: Push configuration to the device. (`True` or `False`)
- **push_clean**: Delete configuration not created by the automation or not matching the exclusion prefix. (`True` or `False`)
- **cleanconfig**: Wipe all configuration except those with the exclusion prefix. (`True` or `False`)
- **mgmt_ext**: External IP or hostname for API connection and secondary configuration. (e.g., `"lab-mikro1.yourdomain.int"`)
- **mgmt_int**: Internal IP or hostname for API connection and primary configuration. (e.g., `"10.5.5.11"`)
- **external_ddns**: Enable MikroTik cloud IP DDNS. (`true` or `false`)
- **external_endpoint**: Host used by the underlay WireGuard for external connection, also required for client VPN WG. (e.g., `"10.5.5.11"`)
- **as**: BGP AS number. (e.g., `'10'`)
- **rp_external**: Security setting for accepting forward traffic. (`true` or `false`)
- **core_priority**: Allows traffic engineering within the backbone of CORE devices. (`true` or `false`)
- **ipv6_advertise_static**: Send static IPv6 prefixes to neighbors. (`true` or `false`)
- **core_internet_transit**: Creates structures for routing internet output via another CORE. (`true` or `false`)
- **location**: Describes the location of the node. (e.g., `"rptest1"`)
- **gateway_number**: Defines the last octet number for each VLAN interface. (e.g., `1`)
- **dhcp_pool_start**: Start of DHCP pool for each VLAN. (e.g., `100`)
- **dhcp_pool_end**: End of DHCP pool for each VLAN. (e.g., `250`)
- **wg_mtu**: Defines the maximum MTU for WireGuard tunnels. (e.g., `'1280'`)
- **domain**: Search domain for DHCP server. (e.g., `"yourdomain.int"`)
- **dns1**: Primary DNS server. (e.g., `"8.8.8.8"`)
- **dns2**: Secondary DNS server. (e.g., `"8.8.4.4"`)
- **dns1_fallback**: Fallback primary DNS server. (e.g., `"7.7.7.7"`)
- **dns2_fallback**: Fallback secondary DNS server. (e.g., `"6.6.6.6"`)
- **internet_icmp_check1**: Netwatch monitor IP 1. (e.g., `"8.8.4.4"`)
- **internet_icmp_check2**: Netwatch monitor IP 2. (e.g., `"8.8.8.8"`)
- **ntp1**: NTP server. (e.g., `"10.151.2.2"`)
- **lease-time**: DHCP lease time. (e.g., `"1d"`)
- **disable-ipv6**: Disable all IPv6 configurations. (e.g., `"no"`)
- **subnetv4**: Main IPv4 /16 network for each site. (e.g., `"10.151.0.0/16"`)
- **subnetv6**: Main IPv6 /96 network for each site. (e.g., `"1:0:0:0:10:151:0:0/96"`)
- **subnetv6slaac**: Main IPv6 /53 network for SLAAC. (e.g., `"1:0:0:8800:0000:0000:0000:0000/53"`)

#### Configlet

A list of automations to execute. Custom automations should be added to the inventory list.
- `"general"`
- `"autoupdate"`
- `"internet"`
- `"wan"`
- `"fw"`
- `"netwatch"`
- `"wg_vpn"`
- `"lan"`
- `"dhcp"`

#### WireGuard VPN Configuration (wg-vpn)

Each WG VPN configuration includes several parameters as described below:

- **id**: Identifies the subnet for WG.
- **name**: Name of the VPN. (e.g., `"mgmt_vpn"`)
- **admin**: Full firewall access for users on this subnet. (`true` or `false`)
- **persistent_keepalive_enable**: Enable persistent keepalive. (`true` or `false`)
- **persistent_keepalive_seconds**: Keepalive interval in seconds. (e.g., `'25'`)
- **mgmt_vpn**: Designates this VPN as an OOB network. (`true` or `false`)
- **allowed_ips**: Allowed IP ranges. (e.g., `'0.0.0.0/0, ::/0'`)
- **disabled_peers**: List of disabled peers by last octet. (e.g., `[2,3]`)
- **subnet**: WG base subnet. (e.g., `100`)
- **number_client**: Number of clients to generate. (e.g., `10`)
- **port**: Listening port. (e.g., `30001`)

#### LAN Configuration (lan)

- **safe_ports**: List of safe ports in VLAN 1.
- **trunk_ports**: List of ports in trunk mode. (e.g., `['ether3']`)
- **access_ports**: List of access ports with associated VLANs. (e.g., `[{port: 'ether2', vlan: '1'}]`)
- **issolated_trunk**: Define if port trunk uses native VLAN 999. (`true` or `false`)

##### VLAN Configuration (vlans)

Each VLAN configuration includes several parameters as described below:

- **id**: VLAN ID number. (e.g., `1`)
- **name**: VLAN name. (e.g., `"1safe"`)
- **ipv6**: Configure IPv6 on this VLAN. (`true` or `false`)
- **ipv6slaac**: Enable SLAAC for IPv6. (`true` or `false`)
- **ipv4_vip_pool**: Pool of IPv4 VIPs for NAT. (e.g., `['10.151.91.0/29']`)
- **ipv6_vip_pool**: Pool of IPv6 VIPs for NAT.

### Example Configuration for one core device (full example at inventory.yml)

```yaml
core:
  - name: "lab-mikro1"
    site_id: 1
    enable_vxlan: true
    enable_vxlan_to_vlan: true
    role: "core"
    enabled: True
    push_config: True
    push_clean: True
    cleanconfig: False
    mgmt_ext: "lab-mikro1.yourdomain.int"
    mgmt_int: "10.5.5.11"
    external_ddns: false
    external_endpoint: "10.5.5.11"
    as: '10'
    rp_external: false
    core_priority: true
    ipv6_advertise_static: false
    core_internet_transit: false
    location: "rptest1"
    gateway_number: 1
    dhcp_pool_start: 100
    dhcp_pool_end: 250
    wg_mtu: '1280'
    domain: "yourdomain.int"
    dns1: "8.8.8.8"
    dns2: "8.8.4.4"
    dns1_fallback: "7.7.7.7"
    dns2_fallback: "6.6.6.6"
    internet_icmp_check1: "8.8.4.4"
    internet_icmp_check2: "8.8.8.8"
    ntp1: "10.151.2.2"
    lease-time: "1d"
    disable-ipv6: "no"
    subnetv4: "10.151.0.0/16"
    subnetv6: "1:0:0:0:10:151:0:0/96"
    subnetv6slaac: "1:0:0:8800:0000:0000:0000:0000/53"
    configlet:
      - "general"
      - "autoupdate"
      - "internet"
      - "wan"
      - "fw"
      - "netwatch"
      - "wg_vpn"
      - "lan"
      - "dhcp"
    save_wg_files: false
    wg-vpn:
      - id: 1
        name: mgmt_vpn
        admin: true
        persistent_keepalive_enable: true
        persistent_keepalive_seconds: '25'
        mgmt_vpn: true
        allowed_ips: '0.0.0.0/0, ::/0'
        disabled_peers: [2,3]
        subnet: 100
        number_client: 10
        port: 30001
      - id: 2
        name: admin_vpn1
        admin: true
        persistent_keepalive_enable: true
        persistent_keepalive_seconds: '25'
        mgmt_vpn: false
        allowed_ips: '0.0.0.0/0, ::/0'
        disabled_peers: []
        subnet: 101
        number_client: 10
        port: 30002
      - id: 3
        name: user_vpn2
        admin: false
        persistent_keepalive_enable: true
        persistent_keepalive_seconds: '25'
        mgmt_vpn: false
        allowed_ips: '0.0.0.0/0, ::/0'
        disabled_peers: []
        subnet: 102
        number_client: 10
        port: 30003
    lan:
      safe_ports: []
      trunk_ports:
        - 'ether3'
      access_ports:
        - port: 'ether2'
          vlan: '1'
      issolated_trunk: true
      vlans:
        - id: 1
          name: 1safe
          ipv6: true
          ipv6slaac: false
          ipv4_vip_pool:
            - '10.151.91.0/29'
          ipv6_vip_pool: []
        - id: 2
          name: 2dmz
          ipv6: true
          ipv6slaac: true
          ipv4_vip_pool: []
          ipv6_vip_pool: []
        - id: 3
          name: 3services
          ipv6: true
          ipv6slaac: false
          ipv4_vip_pool: []
          ipv6_vip_pool: []
        - id: 4
          name: 4guest
          ipv6: true
          ipv6slaac: true
          ipv4_vip_pool: []
          ipv6_vip_pool: []
        - id: 5
          name: 5lab
          ipv6: true
          ipv6slaac: true
          ipv4_vip_pool: []
          ipv6_vip_pool: []