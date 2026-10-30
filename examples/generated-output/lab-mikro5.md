#DEVICE: lab-mikro5

## General Config  
  
### /interface/bridge  
comment|name|ingress_filtering|pvid|vlan_filtering|
|---------|---------|---------|---------|---------|
|bridge-vlans|bridge-vlans|false|999|true|

### /interface/bridge/port  
comment|interface|ingress_filtering|bridge|pvid|
|---------|---------|---------|---------|---------|
|int_br_TRUNK_ether3|ether3|true|bridge-vlans|999|
|int_br_1SAFE_access_ether2|ether2|true|bridge-vlans|1|

### /interface/bridge/vlan  
comment|tagged|vlan_ids|bridge|
|---------|---------|---------|---------|
|int_br_vlan_1|bridge-vlans,ether3|1|bridge-vlans|
|int_br_vlan_2|bridge-vlans,ether3|2|bridge-vlans|
|int_br_vlan_3|bridge-vlans,ether3|3|bridge-vlans|
|int_br_vlan_4|bridge-vlans,ether3|4|bridge-vlans|
|int_br_vlan_5|bridge-vlans,ether3|5|bridge-vlans|

### /interface/list  
comment|include|name|
|---------|---------|---------|
|int_list_inside|static|list_inside|
|int_list_wireguard_main|static|list_wireguard_main|
|int_list_external_wireguard_main|static|list_external_wireguard_main|
|list_internet|static|list_internet|

### /interface/list/member  
comment|interface|list|
|---------|---------|---------|
|list_item_int_v_1safe|1safe|list_inside|
|list_item_int_v_2dmz|2dmz|list_inside|
|list_item_int_v_3services|3services|list_inside|
|list_item_int_v_4guest|4guest|list_inside|
|list_item_int_v_5lab|5lab|list_inside|
|list_item_int_w_lab-mikro5_main_to_lab-mikro1_main|int_w_lab-mikro5_main_to_lab-mikro1_main|list_wireguard_main|
|list_item_int_w_lab-mikro5_main_to_lab-mikro2_main|int_w_lab-mikro5_main_to_lab-mikro2_main|list_wireguard_main|
|list_item_int_w_lab-mikro5_main_to_lab-mikro3_main|int_w_lab-mikro5_main_to_lab-mikro3_main|list_wireguard_main|
|list_internet_item_int_eth1|ether1|list_internet|

### /interface/vlan  
comment|name|vlan_id|interface|
|---------|---------|---------|---------|
|vlan_1safe|1safe|1|bridge-vlans|
|vlan_2dmz|2dmz|2|bridge-vlans|
|vlan_3services|3services|3|bridge-vlans|
|vlan_4guest|4guest|4|bridge-vlans|
|vlan_5lab|5lab|5|bridge-vlans|
|vlan_isolated|isolated|999|bridge-vlans|

### /interface/wireguard  
comment|mtu|name|listen_port|
|---------|---------|---------|---------|
|int_w_lab-mikro5_main_to_lab-mikro1_main|1280|int_w_lab-mikro5_main_to_lab-mikro1_main|51820|
|int_w_lab-mikro5_main_to_lab-mikro2_main|1280|int_w_lab-mikro5_main_to_lab-mikro2_main|51821|
|int_w_lab-mikro5_main_to_lab-mikro3_main|1280|int_w_lab-mikro5_main_to_lab-mikro3_main|51822|

### /interface/wireguard/peers  
name|comment|allowed_address|endpoint_address|endpoint_port|interface|persistent_keepalive|
|---------|---------|---------|---------|---------|---------|---------|
|int_wg_peer_lab-mikro5_main_to_lab-mikro1_main|int_wg_peer_lab-mikro5_main_to_lab-mikro1_main|0.0.0.0/0,::/0|192.168.88.11|51823|int_w_lab-mikro5_main_to_lab-mikro1_main|10s|
|int_wg_peer_lab-mikro5_main_to_lab-mikro2_main|int_wg_peer_lab-mikro5_main_to_lab-mikro2_main|0.0.0.0/0,::/0|lab-mikro2.example.int|51823|int_w_lab-mikro5_main_to_lab-mikro2_main|10s|
|int_wg_peer_lab-mikro5_main_to_lab-mikro3_main|int_wg_peer_lab-mikro5_main_to_lab-mikro3_main|0.0.0.0/0,::/0|lab-mikro3.example.int|51823|int_w_lab-mikro5_main_to_lab-mikro3_main|10s|

### /ip/address  
interface|comment|address|disabled|
|---------|---------|---------|---------|
|lo|ip_lo_10.0.0.5|10.0.0.5/32|true|
|1safe|ip_1safe_10.25.1.1|10.25.1.1/24| - |
|2dmz|ip_2dmz_10.25.2.1|10.25.2.1/24| - |
|3services|ip_3services_10.25.3.1|10.25.3.1/24| - |
|4guest|ip_4guest_10.25.4.1|10.25.4.1/24| - |
|5lab|ip_5lab_10.25.5.1|10.25.5.1/24| - |
|int_w_lab-mikro5_main_to_lab-mikro1_main|ip_wg_10.25.250.1_30|10.25.250.1/30| - |
|int_w_lab-mikro5_main_to_lab-mikro2_main|ip_wg_10.25.250.5_30|10.25.250.5/30| - |
|int_w_lab-mikro5_main_to_lab-mikro3_main|ip_wg_10.25.250.9_30|10.25.250.9/30| - |

### /ip/cloud  
ddns_enabled|ddns_update_interval|
|---------|---------|
|yes|10m|

### /ip/dhcp-server  
comment|name|address_pool|interface|lease_time|
|---------|---------|---------|---------|---------|
|dhcpV4_1safe|dhcpV4_1safe|pool_10.25.1.0/24|1safe|1d|
|dhcpV4_2dmz|dhcpV4_2dmz|pool_10.25.2.0/24|2dmz|1d|
|dhcpV4_3services|dhcpV4_3services|pool_10.25.3.0/24|3services|1d|
|dhcpV4_4guest|dhcpV4_4guest|pool_10.25.4.0/24|4guest|1d|
|dhcpV4_5lab|dhcpV4_5lab|pool_10.25.5.0/24|5lab|1d|

### /ip/dhcp-server/lease  
comment|address|mac-address|server|
|---------|---------|---------|---------|
|lease_example_1|10.25.1.5|02:00:00:00:00:01|dhcpV4_1safe|
|lease_example_2|10.25.1.2|02:00:00:00:00:02|dhcpV4_1safe|

### /ip/dhcp-server/network  
comment|address|dns_server|ntp_server|gateway|domain|
|---------|---------|---------|---------|---------|---------|
|dhcp_netV4_1safe|10.25.1.0/24|8.8.8.8,8.8.4.4|10.21.3.10|10.25.1.1|example.int|
|dhcp_netV4_2dmz|10.25.2.0/24|8.8.8.8,8.8.4.4|10.21.3.10|10.25.2.1|example.int|
|dhcp_netV4_3services|10.25.3.0/24|8.8.8.8,8.8.4.4|10.21.3.10|10.25.3.1|example.int|
|dhcp_netV4_4guest|10.25.4.0/24|8.8.8.8,8.8.4.4|10.21.3.10|10.25.4.1|example.int|
|dhcp_netV4_5lab|10.25.5.0/24|8.8.8.8,8.8.4.4|10.21.3.10|10.25.5.1|example.int|

### /ip/dns  
allow_remote_requests|
|---------|
|no|

### /ip/pool  
comment|name|ranges|
|---------|---------|---------|
|pool_10.25.1.0/24|pool_10.25.1.0/24|10.25.1.100-10.25.1.250|
|pool_10.25.2.0/24|pool_10.25.2.0/24|10.25.2.100-10.25.2.250|
|pool_10.25.3.0/24|pool_10.25.3.0/24|10.25.3.100-10.25.3.250|
|pool_10.25.4.0/24|pool_10.25.4.0/24|10.25.4.100-10.25.4.250|
|pool_10.25.5.0/24|pool_10.25.5.0/24|10.25.5.100-10.25.5.250|

### /ip/route  
comment|dst-address|gateway|routing-table|disabled|
|---------|---------|---------|---------|---------|
|ip_route_internet_vpn|0.0.0.0/0|10.25.250.10|internet_vpn|false|
|ip_route_core_transit_lab-mikro1|0.0.0.0/0|10.25.250.2|core_transit_lab-mikro1|false|
|ip_route_core_transit_lab-mikro2|0.0.0.0/0|10.25.250.6|core_transit_lab-mikro2|false|
|ip_route_core_transit_lab-mikro3|0.0.0.0/0|10.25.250.10|core_transit_lab-mikro3|false|

### /ip/service  
name|disabled|port|certificate|
|---------|---------|---------|---------|
|telnet|true| - | - |
|ftp|true|21| - |
|www|true|80| - |
|www-ssl|false|443|example.int.crt|
|api|true| - | - |
|api-ssl|false|8729| - |
|ssh|false|22| - |

### /ip/traffic-flow  
enabled|
|---------|
|yes|

### /ip/traffic-flow/target  
numbers|dst-address|port|version|vlan_src|
|---------|---------|---------|---------|---------|
|0|10.21.3.30|4739|ipfix|1|

### /ipv6/address  
interface|comment|address|
|---------|---------|---------|
|1safe|ip_1safe_2001:db8:10:0:10:25:1:1|2001:db8:10:0:10:25:1:1/112|
|2dmz|ip_2dmz_2001:db8:10:0:10:25:2:1|2001:db8:10:0:10:25:2:1/112|
|3services|ip_3services_2001:db8:10:0:10:25:3:1|2001:db8:10:0:10:25:3:1/112|
|4guest|ip_4guest_2001:db8:10:0:10:25:4:1|2001:db8:10:0:10:25:4:1/112|
|5lab|ip_5lab_2001:db8:10:0:10:25:5:1|2001:db8:10:0:10:25:5:1/112|
|1safe|ip_1safe_2001:db8:20:1001::1_slaac|2001:db8:20:1001::1/64|
|2dmz|ip_2dmz_2001:db8:20:1002::1_slaac|2001:db8:20:1002::1/64|
|3services|ip_3services_2001:db8:20:1003::1_slaac|2001:db8:20:1003::1/64|
|4guest|ip_4guest_2001:db8:20:1004::1_slaac|2001:db8:20:1004::1/64|
|5lab|ip_5lab_2001:db8:20:1005::1_slaac|2001:db8:20:1005::1/64|
|int_w_lab-mikro5_main_to_lab-mikro1_main|ip_wg_2001:db8:10:0:10:25:fa:0_127|2001:db8:10:0:10:25:fa:0/127|
|int_w_lab-mikro5_main_to_lab-mikro2_main|ip_wg_2001:db8:10:0:10:25:fa:2_127|2001:db8:10:0:10:25:fa:2/127|
|int_w_lab-mikro5_main_to_lab-mikro3_main|ip_wg_2001:db8:10:0:10:25:fa:4_127|2001:db8:10:0:10:25:fa:4/127|

### /ipv6/dhcp-server  
comment|name|address_pool|interface|lease_time|
|---------|---------|---------|---------|---------|
|dhcpV6_1safe|dhcpV6_1safe|pool_2001:db8:10:0:10:25:1:0/112|1safe|1d|
|dhcpV6_2dmz|dhcpV6_2dmz|pool_2001:db8:10:0:10:25:2:0/112|2dmz|1d|
|dhcpV6_3services|dhcpV6_3services|pool_2001:db8:10:0:10:25:3:0/112|3services|1d|
|dhcpV6_4guest|dhcpV6_4guest|pool_2001:db8:10:0:10:25:4:0/112|4guest|1d|
|dhcpV6_5lab|dhcpV6_5lab|pool_2001:db8:10:0:10:25:5:0/112|5lab|1d|

### /ipv6/pool  
comment|name|prefix|prefix_length|
|---------|---------|---------|---------|
|pool_2001:db8:10:0:10:25:1:0/112|pool_2001:db8:10:0:10:25:1:0/112|2001:db8:10:0:10:25:1:0/112|112|
|pool_2001:db8:10:0:10:25:2:0/112|pool_2001:db8:10:0:10:25:2:0/112|2001:db8:10:0:10:25:2:0/112|112|
|pool_2001:db8:10:0:10:25:3:0/112|pool_2001:db8:10:0:10:25:3:0/112|2001:db8:10:0:10:25:3:0/112|112|
|pool_2001:db8:10:0:10:25:4:0/112|pool_2001:db8:10:0:10:25:4:0/112|2001:db8:10:0:10:25:4:0/112|112|
|pool_2001:db8:10:0:10:25:5:0/112|pool_2001:db8:10:0:10:25:5:0/112|2001:db8:10:0:10:25:5:0/112|112|

### /routing/bfd/configuration  
comment|disabled|multiplier|interfaces|
|---------|---------|---------|---------|
|bfd_wan_links|false|25|list_wireguard_main|
|bfd_default|false|25| - |

### /routing/bgp/connection  
comment|name|as|disabled|local.role|output.redistribute|remote.address|remote.as|instance|routing_table|vrf|use-bfd|input.filter|output.filter_chain|afi|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|bgp_v4_lab-mikro1_main__lab-mikro5_main|bgp_v4_lab-mikro1_main__lab-mikro5_main|65150|false|ebgp|connected|10.25.250.2|65110|bgp_instance_main_lab-mikro5|main|main|true|filter_v4_any_priority|filter_v4_labsite5| - |
|bgp_v6_lab-mikro1_main__lab-mikro5_main|bgp_v6_lab-mikro1_main__lab-mikro5_main|65150|false|ebgp|connected|2001:db8:10:0:10:25:fa:1|65110|bgp_instance_main_lab-mikro5|main|main|true|filter_v6_any_priority|filter_v6_labsite5|ipv6|
|bgp_v4_lab-mikro2_main__lab-mikro5_main|bgp_v4_lab-mikro2_main__lab-mikro5_main|65150|false|ebgp|connected|10.25.250.6|65120|bgp_instance_main_lab-mikro5|main|main|true|filter_v4_any_priority|filter_v4_labsite5| - |
|bgp_v6_lab-mikro2_main__lab-mikro5_main|bgp_v6_lab-mikro2_main__lab-mikro5_main|65150|false|ebgp|connected|2001:db8:10:0:10:25:fa:3|65120|bgp_instance_main_lab-mikro5|main|main|true|filter_v6_any_priority|filter_v6_labsite5|ipv6|
|bgp_v4_lab-mikro3_main__lab-mikro5_main|bgp_v4_lab-mikro3_main__lab-mikro5_main|65150|false|ebgp|connected|10.25.250.10|65130|bgp_instance_main_lab-mikro5|main|main|true|filter_v4_any|filter_v4_labsite5| - |
|bgp_v6_lab-mikro3_main__lab-mikro5_main|bgp_v6_lab-mikro3_main__lab-mikro5_main|65150|false|ebgp|connected|2001:db8:10:0:10:25:fa:5|65130|bgp_instance_main_lab-mikro5|main|main|true|filter_v6_any|filter_v6_labsite5|ipv6|

### /routing/bgp/instance  
comment|name|as|router_id|
|---------|---------|---------|---------|
|bgp_instance_main_lab-mikro5|bgp_instance_main_lab-mikro5|65150|192.168.88.15|

### /routing/filter/rule  
comment|chain|disabled|rule|
|---------|---------|---------|---------|
|filter_v4_labsite1|filter_v4_labsite1|false|if (dst in 10.21.0.0/16 || dst in 10.0.0.1/32) {accept}|
|filter_v4_labsite5|filter_v4_labsite5|false|if (dst in 10.25.0.0/16 || dst in 10.0.0.5/32) {accept}|
|filter_v4_any|filter_v4_any|false|if (dst in 10.0.0.0/8) {set bgp-path-peer-prepend 2; accept}|
|filter_v4_any_priority|filter_v4_any_priority|false|if (dst in 10.0.0.0/8) {set bgp-path-peer-prepend 1; accept}|
|filter_v6_labsite1|filter_v6_labsite1|false|if (dst in 2001:db8:10:0:10:21:0:0/96 || dst in 2001:db8:10:8800:0000:0000:0000:0000/53) {accept}|
|filter_v6_labsite5|filter_v6_labsite5|false|if (dst in 2001:db8:10:0:10:25:0:0/96 || dst in 2001:db8:20:1000:0000:0000:0000:0000/53) {accept}|
|filter_v6_any|filter_v6_any|false|if (dst in ::/0) {set bgp-path-peer-prepend 2; accept}|
|filter_v6_any_priority|filter_v6_any_priority|false|if (dst in ::/0) {set bgp-path-peer-prepend 1; accept}|
|filter_v4_labsite2|filter_v4_labsite2|false|if (dst in 10.22.0.0/16 || dst in 10.0.0.2/32) {accept}|
|filter_v6_labsite2|filter_v6_labsite2|false|if (dst in 2001:db8:10:0:10:22:0:0/96 || dst in 2001:db8:10:9000:0000:0000:0000:0000/53) {accept}|
|filter_v4_labsite3|filter_v4_labsite3|false|if (dst in 10.23.0.0/16 || dst in 10.0.0.3/32) {accept}|
|filter_v6_labsite3|filter_v6_labsite3|false|if (dst in 2001:db8:10:0:10:23:0:0/96 || dst in 2001:db8:10:9800:0000:0000:0000:0000/53) {accept}|

### /routing/rule  
comment|table|action|disabled|routing-mark|
|---------|---------|---------|---------|---------|
|routing_rule_internet_vpn|internet_vpn|lookup-only-in-table|false|internet_vpn|
|routing_rule_main|main|lookup|false|main|
|routing_rule_core_transit_lab-mikro1|core_transit_lab-mikro1|lookup-only-in-table|false|core_transit_lab-mikro1|
|routing_rule_core_transit_lab-mikro2|core_transit_lab-mikro2|lookup-only-in-table|false|core_transit_lab-mikro2|
|routing_rule_core_transit_lab-mikro3|core_transit_lab-mikro3|lookup-only-in-table|false|core_transit_lab-mikro3|

### /routing/table  
comment|name|fib|
|---------|---------|---------|
|routing_table_internet_vpn|internet_vpn||
|routing_table_core_transit_lab-mikro1|core_transit_lab-mikro1||
|routing_table_core_transit_lab-mikro2|core_transit_lab-mikro2||
|routing_table_core_transit_lab-mikro3|core_transit_lab-mikro3||

### /snmp  
contact|enabled|
|---------|---------|
|admin@example.com|yes|

### /system/clock  
time_zone_name|
|---------|
|Etc/UTC|

### /system/identity  

|
|

### /system/logging  
numbers|action|topics|
|---------|---------|---------|
|4|remote|!debug|

### /system/logging/action  
numbers|remote|remote_port|vlan_src|
|---------|---------|---------|---------|
|3|10.21.3.10|514|1|

### /system/ntp/client  
enabled|
|---------|
|yes|

### /system/ntp/client/servers  
comment|address|
|---------|---------|
|ntp-pool|pool.ntp.org|

### /tool/netwatch  
comment|host|type|interval|test_script|down_script|up_script|port|
|---------|---------|---------|---------|---------|---------|---------|---------|
|netwatch_wg_lab-mikro5_main_to_lab-mikro1_main|10.25.250.2|icmp|30s|# no test configure| - | - | - |
|netwatch_wg_lab-mikro5_main_to_lab-mikro2_main|10.25.250.6|icmp|30s|# no test configure| - | - | - |
|netwatch_wg_lab-mikro5_main_to_lab-mikro3_main|10.25.250.10|icmp|30s|# no test configure| - | - | - |
|netwatch_core_transit_lab-mikro1|10.25.250.2| - |10s| - |/ip firewall mangle disable [find comment="core_transit_lab-mikro1_mark"];|/ip firewall mangle enable [find comment="core_transit_lab-mikro1_mark"];| - |
|netwatch_core_transit_lab-mikro2|10.25.250.6| - |10s| - |/ip firewall mangle disable [find comment="core_transit_lab-mikro2_mark"];|/ip firewall mangle enable [find comment="core_transit_lab-mikro2_mark"];| - |
|netwatch_core_transit_lab-mikro3|10.25.250.10| - |10s| - |/ip firewall mangle disable [find comment="core_transit_lab-mikro3_mark"];|/ip firewall mangle enable [find comment="core_transit_lab-mikro3_mark"];| - |
|netwatch_dns1|8.8.8.8| - |10s| - |/ip firewall nat enable [find comment="NAT_FALLBACK_DNS_1"];|/ip firewall nat disable [find comment="NAT_FALLBACK_DNS_1"];| - |
|netwatch_dns2|8.8.4.4| - |10s| - |/ip firewall nat enable [find comment="NAT_FALLBACK_DNS_2"];|/ip firewall nat disable [find comment="NAT_FALLBACK_DNS_2"];| - |
|netwatch_tcp_dns_1|8.8.8.8|tcp-conn|30s| - | - | - |53|
|netwatch_tcp_dns_2|8.8.4.4|tcp-conn|30s| - | - | - |53|
|netwatch_internet1|1.1.1.1|icmp|30s|# no test configure| - | - | - |
|netwatch_internet2|8.8.8.8|icmp|30s|# no test configure| - | - | - |

## Firewall Config  
  
### /ip/firewall/address-list  
comment|address|
|---------|---------|
|ACL4_HOSTS_VPN_EXIT|['10.21.4.0/24', '10.22.4.0/24', '10.23.4.0/24', '10.24.4.0/24', '10.25.4.0/24', '10.26.4.0/24']|
|ACL4_HOSTS_VPN_EXIT2|['10.21.5.50']|
|ACL4_HOSTS_VPN_USERS|['10.21.102.0/24']|
|ACL4_NETS_NOLOG|['224.0.0.0/4', '255.255.255.255']|
|ACL4_NETS_SITES|['10.21.0.0/16', '10.22.0.0/16', '10.23.0.0/16', '10.24.0.0/16', '10.25.0.0/16', '10.26.0.0/16']|
|ACL4_NETS_TRUSTED|['10.21.1.0/24', '10.22.1.0/24', '10.23.1.0/24', '10.24.1.0/24', '10.25.1.0/24', '10.26.1.0/24']|
|ACL4_NETS_PRIVATE|['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']|
|ACL4_HOSTS_MGMT|['127.0.0.1', '192.168.88.0/24', '10.21.100.0/24', '10.21.101.0/24', '10.21.250.0/24', '10.22.250.0/24', '10.23.250.0/24']|
|ACL4_HOSTS_MGMT_VPN|['10.21.100.0/24']|
|ACL4_NETS_INTERNET|['0.0.0.0/0']|
|ACL4_HOSTS_MONITORING|['10.21.3.30']|
|ACL4_NETS_DMZ|['10.21.2.0/24', '10.22.2.0/24', '10.23.2.0/24', '10.24.2.0/24', '10.25.2.0/24', '10.26.2.0/24']|
|ACL4_HOSTS_NTP|['10.21.3.10']|
|ACL4_HOSTS_SYSLOG|['10.21.3.10']|
|ACL4_HOSTS_DNS|['10.21.3.53', '10.22.3.53']|
|ACL4_HOSTS_WEB|['10.21.2.80']|
|ACL4_HOSTS_RADIUS_SERVERS|['10.21.1.1', '10.22.1.1', '10.23.1.1']|
|ACL4_HOSTS_RADIUS_CLIENTS|['10.24.1.1', '10.25.1.1', '10.26.1.1']|
|ACL4_HOSTS_NETFLOW|['10.21.1.1', '10.22.1.1', '10.23.1.1', '10.24.1.1', '10.25.1.1', '10.26.1.1']|
|ACL4_HOSTS_APPS_DMZ|['10.21.2.20', '10.21.2.21']|
|ACL4_HOSTS_APPS_TRUSTED|['10.21.1.20']|
|ACL4_HOSTS_STORAGE|['10.21.3.40']|
|ACL4_HOSTS_STORAGE_CLIENTS|['10.21.2.20', '10.21.2.21', '10.21.1.20']|

### /ip/firewall/filter  
comment|order|posi|chain|connection_state|action|src_address_list|dst_address_list|log|log_prefix|disabled|protocol|icmp_options|dst_port|reject_with|in_interface|src_address|dst_address|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|v4_forward_fasttrackconnection|posi|6|forward|established,related|fasttrack-connection| - | - | - | - | - | - | - | - | - | - | - | - |
|v4_forward_accept|posi|6|forward|established,related,untracked|accept| - | - | - | - | - | - | - | - | - | - | - | - |
|v4_input_accept|posi|7|input|established,related,untracked|accept| - | - | - | - | - | - | - | - | - | - | - | - |
|v4_input_log_banned|posi|1|input| - |log|ACL4_NETS_PRIVATE|ACL4_BANNED|true|FW=ban_log T=to_banned S=PRIV|false| - | - | - | - | - | - | - |
|v4_forward_log_banned|posi|2|forward| - |log|ACL4_NETS_PRIVATE|ACL4_BANNED|true|FW=ban_log T=to_banned S=PRIV|false| - | - | - | - | - | - | - |
|v4_input_drop_banned|posi|3|input| - |drop|ACL4_BANNED| - |true|FW=ban_drop S=PUB|false| - | - | - | - | - | - | - |
|v4_forward_drop_banned|posi|4|forward| - |drop|ACL4_BANNED| - |true|FW=ban_drop S=PUB|false| - | - | - | - | - | - | - |
|v4_input_accept_icmp_t0|top| - |input| - |accept| - | - | - | - |false|icmp|0:0-255| - | - | - | - | - |
|v4_input_accept_icmp_t3|top| - |input| - |accept| - | - | - | - |false|icmp|3:0-255| - | - | - | - | - |
|v4_input_accept_icmp_t8|top| - |input| - |accept| - | - | - | - |false|icmp|8:0-255| - | - | - | - | - |
|v4_input_accept_icmp_t11|top| - |input| - |accept| - | - | - | - |false|icmp|11:0-255| - | - | - | - | - |
|v4_forward_accept_icmp_t0|top| - |forward| - |accept| - | - | - | - |false|icmp|0:0-255| - | - | - | - | - |
|v4_forward_accept_icmp_t3|top| - |forward| - |accept| - | - | - | - |false|icmp|3:0-255| - | - | - | - | - |
|v4_forward_accept_icmp_t8|top| - |forward| - |accept| - | - | - | - |false|icmp|8:0-255| - | - | - | - | - |
|v4_forward_accept_icmp_t11|top| - |forward| - |accept| - | - | - | - |false|icmp|11:0-255| - | - | - | - | - |
|v4_input_accept_tcp_mgmt|top| - |input| - |accept|ACL4_HOSTS_MGMT| - |false|no|false|tcp| - |21,22,23,80,443,8291,8728,8729,2000| - | - | - | - |
|v4_input_accept_udp_mgmt|top| - |input| - |accept|ACL4_HOSTS_MGMT| - |false|no|false|udp| - |161,1812,1813,5678| - | - | - | - |
|v4_input_accept_mgmt_vpn|top| - |input| - |accept|ACL4_HOSTS_MGMT_VPN|ACL4_HOSTS_MGMT_VPN|false|no|false| - | - | - | - | - | - | - |
|v4_input_accept_udp_monitoring|top| - |input| - |accept|ACL4_HOSTS_MONITORING| - |false|no|false|udp| - |161| - | - | - | - |
|v4_input_accept_udp_radius_clients|top| - |input| - |accept|ACL4_HOSTS_RADIUS_CLIENTS| - |false|no|false|udp| - |1812-1813| - | - | - | - |
|v4_forward_accept_tcp_storage|top| - |forward| - |accept|ACL4_HOSTS_VPN_USERS|ACL4_HOSTS_STORAGE|false|no|false|tcp| - |80,139,443,445,5000,5001| - | - | - | - |
|v4_forward_accept_not_private|top| - |forward| - |accept|ACL4_NETS_PRIVATE|!ACL4_NETS_PRIVATE|false|no|false| - | - | - | - | - | - | - |
|v4_forward_accept_trusted|top| - |forward| - |accept|ACL4_NETS_TRUSTED| - |false|no|false| - | - | - | - | - | - | - |
|v4_input_accept_trusted|top| - |input| - |accept|ACL4_NETS_TRUSTED| - |false|no|false| - | - | - | - | - | - | - |
|v4_forward_accept_dmz|top| - |forward| - |accept|ACL4_NETS_DMZ|ACL4_NETS_DMZ|false|no|false| - | - | - | - | - | - | - |
|v4_forward_accept_udp_ntp|top| - |forward| - |accept|ACL4_NETS_PRIVATE|ACL4_HOSTS_NTP|false|no|false|udp| - |123| - | - | - | - |
|v4_forward_accept_udp_syslog|top| - |forward| - |accept|ACL4_NETS_PRIVATE|ACL4_HOSTS_SYSLOG|false|no|false|udp| - |514| - | - | - | - |
|v4_forward_accept_udp_dns|top| - |forward| - |accept|ACL4_NETS_PRIVATE|ACL4_HOSTS_DNS|false|no|false|udp| - |53| - | - | - | - |
|v4_forward_accept_tcp_dns|top| - |forward| - |accept|ACL4_NETS_PRIVATE|ACL4_HOSTS_DNS|false|no|false|tcp| - |53| - | - | - | - |
|v4_forward_accept_tcp_web|top| - |forward| - |accept|ACL4_NETS_PRIVATE|ACL4_HOSTS_WEB|false|no|false|tcp| - |80,443| - | - | - | - |
|v4_forward_accept_udp_radius_servers|top| - |forward| - |accept|ACL4_HOSTS_RADIUS_CLIENTS|ACL4_HOSTS_RADIUS_SERVERS|false|no|false|udp| - |1812-1813| - | - | - | - |
|v4_forward_accept_udp_apps_dmz|top| - |forward| - |accept|ACL4_HOSTS_NETFLOW|ACL4_HOSTS_APPS_DMZ|false|no|false|udp| - |4739| - | - | - | - |
|v4_forward_accept_tcp_monitoring|top| - |forward| - |accept|ACL4_NETS_PRIVATE|ACL4_HOSTS_MONITORING|false|no|false|tcp| - |8086| - | - | - | - |
|v4_forward_accept_udp_private|top| - |forward| - |accept|ACL4_HOSTS_MONITORING|ACL4_NETS_PRIVATE|false|no|false|udp| - |161| - | - | - | - |
|v4_forward_accept_tcp_private|top| - |forward| - |accept|ACL4_HOSTS_MONITORING|ACL4_NETS_PRIVATE|false|no|false|tcp| - |3000,8053,443,80,3306| - | - | - | - |
|v4_forward_accept_udp_apps_trusted|top| - |forward| - |accept|ACL4_HOSTS_SYSLOG|ACL4_HOSTS_APPS_TRUSTED|false|no|false|udp| - |514| - | - | - | - |
|v4_forward_accept_tcp_apps_dmz|top| - |forward| - |accept|ACL4_HOSTS_APPS_DMZ|ACL4_HOSTS_APPS_DMZ|false|no|false|tcp| - |2376,2377,7946| - | - | - | - |
|v4_forward_accept_udp_apps_dmz_2|top| - |forward| - |accept|ACL4_HOSTS_APPS_DMZ|ACL4_HOSTS_APPS_DMZ|false|no|false|udp| - |4789,7946| - | - | - | - |
|v4_forward_accept_tcp_apps_trusted|top| - |forward| - |accept|ACL4_HOSTS_APPS_TRUSTED|ACL4_HOSTS_APPS_TRUSTED|false|no|false|tcp| - |2376,2377,7946| - | - | - | - |
|v4_forward_accept_udp_apps_trusted_2|top| - |forward| - |accept|ACL4_HOSTS_APPS_TRUSTED|ACL4_HOSTS_APPS_TRUSTED|false|no|false|udp| - |4789,7946| - | - | - | - |
|v4_forward_accept_tcp_storage_2|top| - |forward| - |accept|ACL4_HOSTS_STORAGE_CLIENTS|ACL4_HOSTS_STORAGE|false|no|false|tcp| - |111,892,2049| - | - | - | - |
|v4_forward_accept_udp_storage|top| - |forward| - |accept|ACL4_HOSTS_STORAGE_CLIENTS|ACL4_HOSTS_STORAGE|false|no|false|udp| - |111,892,2049| - | - | - | - |
|v4_forward_accept_tcp_apps_dmz_2|top| - |forward| - |accept|ACL4_NETS_SITES|ACL4_HOSTS_APPS_DMZ|false|no|false|tcp| - |1883| - | - | - | - |
|v4_input_reject_icmp_private|bot| - |input| - |reject|ACL4_NETS_PRIVATE| - |true|FW=in_reject T=icmp S=PRIV|false|icmp| - | - |icmp-admin-prohibited| - | - | - |
|v4_forward_reject_icmp_private|bot| - |forward| - |reject|ACL4_NETS_PRIVATE| - |true|FW=fw_reject T=icmp S=PRIV|false|icmp| - | - |icmp-admin-prohibited| - | - | - |
|v4_input_drop_icmp|bot| - |input| - |drop| - | - |true|FW=in_reject T=icmp S=PUB|false|icmp| - | - | - | - | - | - |
|v4_forward_drop_icmp|bot| - |forward| - |drop| - | - |true|FW=fw_reject T=icmp S=PUB|false|icmp| - | - | - | - | - | - |
|v4_input_reject_tcp_private|bot| - |input| - |reject|ACL4_NETS_PRIVATE| - |true|FW=in_reject T=SSH S=PRIV|false|tcp| - |22|icmp-admin-prohibited| - | - | - |
|v4_forward_reject_tcp_private|bot| - |forward| - |reject|ACL4_NETS_PRIVATE| - |true|FW=fw_reject T=SSH S=PRIV|false|tcp| - |22|icmp-admin-prohibited| - | - | - |
|v4_input_drop_tcp_internet|bot| - |input| - |drop|ACL4_NETS_INTERNET| - |true|FW=in_drop T=SSH S=PUB|false|tcp| - |22| - | - | - | - |
|v4_forward_drop_tcp_internet|bot| - |forward| - |drop|ACL4_NETS_INTERNET| - |true|FW=fw_drop T=SSH S=PUB|false|tcp| - |22| - | - | - | - |
|v4_input_drop_nolog|bot| - |input| - |drop|ACL4_NETS_NOLOG| - |false|no|false| - | - | - | - | - | - | - |
|v4_forward_drop_nolog|bot| - |forward| - |drop|ACL4_NETS_NOLOG| - |false|no|false| - | - | - | - | - | - | - |
|v4_input_drop_nolog_2|bot| - |input| - |drop| - |ACL4_NETS_NOLOG|false|no|false| - | - | - | - | - | - | - |
|v4_forward_drop_nolog_2|bot| - |forward| - |drop| - |ACL4_NETS_NOLOG|false|no|false| - | - | - | - | - | - | - |
|v4_input_drop_internet|bot| - |input|invalid|drop|ACL4_NETS_INTERNET| - |false|no|false| - | - | - | - | - | - | - |
|v4_forward_drop_internet|bot| - |forward|invalid|drop|ACL4_NETS_INTERNET| - |false|no|false| - | - | - | - | - | - | - |
|v4_input_reject_private|bot| - |input| - |reject|ACL4_NETS_PRIVATE| - |true|FW=in_reject S=PRIV|false| - | - | - |icmp-admin-prohibited| - | - | - |
|v4_forward_reject_private|bot| - |forward| - |reject|ACL4_NETS_PRIVATE| - |true|FW=fw_reject S=PRIV|false| - | - | - |icmp-admin-prohibited| - | - | - |
|v4_input_drop_internet_2|bot| - |input| - |drop|ACL4_NETS_INTERNET| - |true|FW=in_drop S=PUB|false| - | - | - | - | - | - | - |
|v4_forward_drop_internet_2|bot| - |forward| - |drop|ACL4_NETS_INTERNET| - |true|FW=fw_drop S=PUB|false| - | - | - | - | - | - | - |
|fw_in_dhcp_netV4_1safe|top| - |input| - |accept| - | - | - | - |false|udp| - |67-68| - |1safe| - | - |
|fw_in_dhcp_netV4_2dmz|top| - |input| - |accept| - | - | - | - |false|udp| - |67-68| - |2dmz| - | - |
|fw_in_dhcp_netV4_3services|top| - |input| - |accept| - | - | - | - |false|udp| - |67-68| - |3services| - | - |
|fw_in_dhcp_netV4_4guest|top| - |input| - |accept| - | - | - | - |false|udp| - |67-68| - |4guest| - | - |
|fw_in_dhcp_netV4_5lab|top| - |input| - |accept| - | - | - | - |false|udp| - |67-68| - |5lab| - | - |
|fw_v4_forward_wgmain_in_lab-mikro5_main_to_lab-mikro1_main|top| - |forward| - |accept| - | - | - | - |false| - | - | - | - |int_w_lab-mikro5_main_to_lab-mikro1_main| - | - |
|fw_in_wireguard_lab-mikro5_main_to_lab-mikro1_main|top| - |input| - |accept| - | - | - | - |false|udp| - |51820| - | - | - | - |
|fw_in_bgp_lab-mikro5_main_to_lab-mikro1_main|top| - |input| - |accept| - | - | - | - |false|tcp| - |179| - | - |10.25.250.0/30|10.25.250.0/30|
|fw_in_bfd_lab-mikro5_main_to_lab-mikro1_main|top| - |input| - |accept| - | - | - | - |false|udp| - |3784| - | - |10.25.250.0/30|10.25.250.0/30|
|fw_v4_forward_wgmain_in_lab-mikro5_main_to_lab-mikro2_main|top| - |forward| - |accept| - | - | - | - |false| - | - | - | - |int_w_lab-mikro5_main_to_lab-mikro2_main| - | - |
|fw_in_wireguard_lab-mikro5_main_to_lab-mikro2_main|top| - |input| - |accept| - | - | - | - |false|udp| - |51821| - | - | - | - |
|fw_in_bgp_lab-mikro5_main_to_lab-mikro2_main|top| - |input| - |accept| - | - | - | - |false|tcp| - |179| - | - |10.25.250.4/30|10.25.250.4/30|
|fw_in_bfd_lab-mikro5_main_to_lab-mikro2_main|top| - |input| - |accept| - | - | - | - |false|udp| - |3784| - | - |10.25.250.4/30|10.25.250.4/30|
|fw_v4_forward_wgmain_in_lab-mikro5_main_to_lab-mikro3_main|top| - |forward| - |accept| - | - | - | - |false| - | - | - | - |int_w_lab-mikro5_main_to_lab-mikro3_main| - | - |
|fw_in_wireguard_lab-mikro5_main_to_lab-mikro3_main|top| - |input| - |accept| - | - | - | - |false|udp| - |51822| - | - | - | - |
|fw_in_bgp_lab-mikro5_main_to_lab-mikro3_main|top| - |input| - |accept| - | - | - | - |false|tcp| - |179| - | - |10.25.250.8/30|10.25.250.8/30|
|fw_in_bfd_lab-mikro5_main_to_lab-mikro3_main|top| - |input| - |accept| - | - | - | - |false|udp| - |3784| - | - |10.25.250.8/30|10.25.250.8/30|

### /ip/firewall/mangle  
comment|order|chain|dst_port|protocol|log|disabled|passthrough|action|new_packet_mark|tcp_flags|new_mss|src_address_list|dst_address_list|new_routing_mark|log_prefix|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|v4_mangle_prerouting_markpacket_tcp|top|prerouting|22,53,179,1194-1200,1883,3389,5201|tcp|false|false|true|mark-packet|p1| - | - | - | - | - | - |
|v4_mangle_prerouting_markpacket_udp|top|prerouting|53,179,119,500,1194-1200,3724,3478-3479,3000-4000|udp|false|false|true|mark-packet|p1| - | - | - | - | - | - |
|v4_mangle_prerouting_markpacket_udp_2|top|prerouting|4500,4784,5000-5030,6000-6030,6060,6113,6250,7000-7030,9000-10000|udp|false|false|true|mark-packet|p1| - | - | - | - | - | - |
|v4_mangle_prerouting_markpacket_udp_3|top|prerouting|50000-65535|udp|false|false|true|mark-packet|p1| - | - | - | - | - | - |
|v4_mangle_prerouting_markpacket_tcp_2|top|prerouting|80|tcp|false|false|true|mark-packet|p3| - | - | - | - | - | - |
|v4_mangle_prerouting_markpacket_udp_4|top|prerouting|6881-6889|udp|false|false|true|mark-packet|p3| - | - | - | - | - | - |
|v4_mangle_forward_changemss_tcp|top|forward| - |tcp| - | - |true|change-mss| - |syn|clamp-to-pmtu| - | - | - | - |
|vpnexit_mark_forward|top|prerouting| - | - |false|false| - |mark-routing| - | - | - |ACL4_HOSTS_VPN_EXIT|!ACL4_NETS_PRIVATE|internet_vpn|no|
|vpnexit_mark_out|top|output| - | - |false|false| - |mark-routing| - | - | - |ACL4_HOSTS_VPN_EXIT|!ACL4_NETS_PRIVATE|internet_vpn|no|
|webapp_mark_internetvpn_forward|top|prerouting| - | - |false|false| - |mark-routing| - | - | - |ACL4_PORTAL_VPN|!ACL4_NETS_PRIVATE|internet_vpn|no|
|core_transit_lab-mikro1_mark|top|prerouting| - | - |false|false| - |mark-routing| - | - | - |ACL4_EXIT_VIA_lab-mikro1|!ACL4_NETS_PRIVATE|core_transit_lab-mikro1|no|
|core_transit_lab-mikro2_mark|top|prerouting| - | - |false|false| - |mark-routing| - | - | - |ACL4_EXIT_VIA_lab-mikro2|!ACL4_NETS_PRIVATE|core_transit_lab-mikro2|no|
|core_transit_lab-mikro3_mark|top|prerouting| - | - |false|false| - |mark-routing| - | - | - |ACL4_EXIT_VIA_lab-mikro3|!ACL4_NETS_PRIVATE|core_transit_lab-mikro3|no|

### /ip/firewall/nat  
comment|order|chain|src_address_list|dst_address|dst_port|to_addresses|to-ports|protocol|log|log_prefix|disabled|action|src_address|to_ports|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|v4_nat_dstnat_udp_portal_dns|top|dstnat|ACL4_PORTAL_DNS|10.21.3.53|53|10.21.3.54|53|udp|false|no|false|dst-nat| - | - |
|v4_nat_dstnat_udp_portal_dns_2|top|dstnat|ACL4_PORTAL_DNS|10.22.3.53|53|10.21.3.54|53|udp|false|no|false|dst-nat| - | - |
|NAT_FALLBACK_DNS_1|top|dstnat| - |8.8.8.8|53|7.7.7.7| - |udp|false| - | - |dst-nat|10.0.0.0/8|53|
|NAT_FALLBACK_DNS_2|top|dstnat| - |8.8.4.4|53|6.6.6.6| - |udp|false| - | - |dst-nat|10.0.0.0/8|53|

### /ipv6/firewall/address-list  
comment|address|
|---------|---------|
|ACL6_NETS_NOLOG|['::1/128', 'ff02::1/128', 'ff02::1:2/128', 'ff00::/8']|
|ACL6_NETS_BLOCKED|['2001:db8:ffff:1::/64']|
|ACL6_HOSTS_WG_ENDPOINTS|['2001:db8:10:0:10:21:fa:2/128']|
|ACL6_NETS_SITES|['2001:db8:10:0:10:21::/96', '2001:db8:10:0:10:22::/96', '2001:db8:10:0:10:23::/96', '2001:db8:10:0:10:24::/96', '2001:db8:10:0:10:25::/96', '2001:db8:10:0:10:26::/96', '2001:db8:10:8000::/49']|
|ACL6_NETS_TRUSTED|['2001:db8:10:0:10:21:1:0/112', '2001:db8:10:9801::/64', '2001:db8:10:0:10:22:1:0/112', '2001:db8:10:9001::/64', '2001:db8:10:0:10:23:1:0/112', '2001:db8:10:b001::/64']|
|ACL6_NETS_PRIVATE|['2001:db8:10::/48', 'fc00::/7', 'ff00::/8']|
|ACL6_HOSTS_MGMT|['2001:db8:10:0:10:21:1:0/112', '2001:db8:10:0:10:21:64:0/112']|
|ACL6_NETS_INTERNET|['::/0', '2000::/3']|
|ACL6_HOSTS_MONITORING|['2001:db8:10:0:10:21:3:30/128']|
|ACL6_NETS_DMZ|['2001:db8:10:0:10:21:2:0/112', '2001:db8:10:0:10:22:2:0/112']|
|ACL6_HOSTS_NTP|['2001:db8:10:0:10:21:3:10/128']|
|ACL6_HOSTS_SYSLOG|['2001:db8:10:0:10:21:3:10/128']|
|ACL6_HOSTS_DNS|['2001:db8:10:0:10:21:3:53/128', '2001:db8:10:0:10:22:3:53/128']|
|ACL6_HOSTS_WEB|['2001:db8:10:0:10:21:2:80/128']|
|ACL6_HOSTS_RADIUS_SERVERS|['2001:db8:10:0:10:21:1:1/128']|
|ACL6_HOSTS_RADIUS_CLIENTS|['2001:db8:10:0:10:24:1:1/128']|
|ACL6_HOSTS_NETFLOW|['2001:db8:10:0:10:21:1:1/128', '2001:db8:10:0:10:22:1:1/128', '2001:db8:10:0:10:23:1:1/128']|
|ACL6_HOSTS_APPS_DMZ|['2001:db8:10:0:10:21:2:20/128']|
|ACL6_HOSTS_APPS_TRUSTED|['2001:db8:10:0:10:21:1:20/128']|
|ACL6_HOSTS_STORAGE|['2001:db8:10:0:10:21:3:40/128']|
|ACL6_HOSTS_STORAGE_CLIENTS|['2001:db8:10:0:10:21:2:20/128', '2001:db8:10:0:10:21:1:20/128']|

### /ipv6/firewall/filter  
comment|order|posi|chain|connection_state|action|src_address_list|dst_address_list|log|log_prefix|disabled|protocol|icmp_options|dst_port|dst_address|reject_with|in_interface|src_address|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|v6_input_accept|posi|5|input|established,related,untracked|accept| - | - | - | - | - | - | - | - | - | - | - | - |
|v6_forward_accept|posi|6|forward|established,related,untracked|accept| - | - | - | - | - | - | - | - | - | - | - | - |
|v6_input_log_banned|posi|1|input| - |log|ACL4_NETS_PRIVATE|ACL6_BANNED|true|FW=ban_log T=to_banned S=PRIV|false| - | - | - | - | - | - | - |
|v6_forward_log_banned|posi|2|forward| - |log|ACL4_NETS_PRIVATE|ACL6_BANNED|true|FW=ban_log T=to_banned S=PRIV|false| - | - | - | - | - | - | - |
|v6_input_drop_banned|posi|3|input| - |drop|ACL6_BANNED| - |true|FW=ban_drop S=PUB|false| - | - | - | - | - | - | - |
|v6_forward_drop_banned|posi|4|forward| - |drop|ACL6_BANNED| - |true|FW=ban_drop S=PUB|false| - | - | - | - | - | - | - |
|v6_input_accept_icmpv6_t1|top| - |input| - |accept| - | - | - | - |false|icmpv6|1| - | - | - | - | - |
|v6_input_accept_icmpv6_t2|top| - |input| - |accept| - | - | - | - |false|icmpv6|2| - | - | - | - | - |
|v6_input_accept_icmpv6_t3|top| - |input| - |accept| - | - | - | - |false|icmpv6|3| - | - | - | - | - |
|v6_input_accept_icmpv6_t4|top| - |input| - |accept| - | - | - | - |false|icmpv6|4| - | - | - | - | - |
|v6_input_accept_icmpv6_t128|top| - |input| - |accept| - | - | - | - |false|icmpv6|128| - | - | - | - | - |
|v6_input_accept_icmpv6_t129|top| - |input| - |accept| - | - | - | - |false|icmpv6|129| - | - | - | - | - |
|v6_input_accept_icmpv6_t133|top| - |input| - |accept| - | - | - | - |false|icmpv6|133| - | - | - | - | - |
|v6_input_accept_icmpv6_t134|top| - |input| - |accept| - | - | - | - |false|icmpv6|134| - | - | - | - | - |
|v6_input_accept_icmpv6_t135|top| - |input| - |accept| - | - | - | - |false|icmpv6|135| - | - | - | - | - |
|v6_input_accept_icmpv6_t136|top| - |input| - |accept| - | - | - | - |false|icmpv6|136| - | - | - | - | - |
|v6_input_accept_icmpv6_t137|top| - |input| - |accept| - | - | - | - |false|icmpv6|137| - | - | - | - | - |
|v6_forward_accept_icmpv6_t1|top| - |forward| - |accept| - | - | - | - |false|icmpv6|1| - | - | - | - | - |
|v6_forward_accept_icmpv6_t2|top| - |forward| - |accept| - | - | - | - |false|icmpv6|2| - | - | - | - | - |
|v6_forward_accept_icmpv6_t3|top| - |forward| - |accept| - | - | - | - |false|icmpv6|3| - | - | - | - | - |
|v6_forward_accept_icmpv6_t4|top| - |forward| - |accept| - | - | - | - |false|icmpv6|4| - | - | - | - | - |
|v6_forward_accept_icmpv6_t128|top| - |forward| - |accept| - | - | - | - |false|icmpv6|128| - | - | - | - | - |
|v6_forward_accept_icmpv6_t129|top| - |forward| - |accept| - | - | - | - |false|icmpv6|129| - | - | - | - | - |
|v6_forward_accept_icmpv6_t133|top| - |forward| - |accept| - | - | - | - |false|icmpv6|133| - | - | - | - | - |
|v6_forward_accept_icmpv6_t134|top| - |forward| - |accept| - | - | - | - |false|icmpv6|134| - | - | - | - | - |
|v6_forward_accept_icmpv6_t135|top| - |forward| - |accept| - | - | - | - |false|icmpv6|135| - | - | - | - | - |
|v6_forward_accept_icmpv6_t136|top| - |forward| - |accept| - | - | - | - |false|icmpv6|136| - | - | - | - | - |
|v6_forward_accept_icmpv6_t137|top| - |forward| - |accept| - | - | - | - |false|icmpv6|137| - | - | - | - | - |
|v6_input_accept_tcp_mgmt|top| - |input| - |accept|ACL6_HOSTS_MGMT| - |false|no|false|tcp| - |22,8291,8729| - | - | - | - |
|v6_input_accept_udp_monitoring|top| - |input| - |accept|ACL6_HOSTS_MONITORING| - |false|no|false|udp| - |161| - | - | - | - |
|v6_input_accept_udp_radius_clients|top| - |input| - |accept|ACL6_HOSTS_RADIUS_CLIENTS| - |false|no|false|udp| - |1812-1813| - | - | - | - |
|v6_forward_accept_tcp|top| - |forward| - |accept| - | - |false|no|false|tcp| - |80,443|2001:db8:10:0:10:1:2:4/128| - | - | - |
|v6_forward_accept_tcp_2|top| - |forward| - |accept| - | - |false|no|false|tcp| - |80,443|2001:db8:10:0:10:5:2:4/128| - | - | - |
|v6_forward_accept_udp_wg_endpoints|top| - |forward| - |accept| - |ACL6_HOSTS_WG_ENDPOINTS|false|no|false|udp| - |3000-3010,51820-51900| - | - | - | - |
|v6_forward_accept_not_private|posi|5|forward| - |accept|ACL6_NETS_PRIVATE|!ACL6_NETS_PRIVATE|false|no|false| - | - | - | - | - | - | - |
|v6_forward_reject_blocked|posi|4|forward| - |reject|ACL6_NETS_PRIVATE|ACL6_NETS_BLOCKED|false|no|false| - | - | - | - | - | - | - |
|v6_forward_accept_trusted|top| - |forward| - |accept|ACL6_NETS_TRUSTED| - |false|no|false| - | - | - | - | - | - | - |
|v6_input_accept_trusted|top| - |input| - |accept|ACL6_NETS_TRUSTED| - |false|no|false| - | - | - | - | - | - | - |
|v6_forward_accept_dmz|top| - |forward| - |accept|ACL6_NETS_DMZ|ACL6_NETS_DMZ|false|no|false| - | - | - | - | - | - | - |
|v6_forward_accept_udp_ntp|top| - |forward| - |accept|ACL6_NETS_PRIVATE|ACL6_HOSTS_NTP|false|no|false|udp| - |123| - | - | - | - |
|v6_forward_accept_udp_syslog|top| - |forward| - |accept|ACL6_NETS_PRIVATE|ACL6_HOSTS_SYSLOG|false|no|false|udp| - |514| - | - | - | - |
|v6_forward_accept_udp_dns|top| - |forward| - |accept|ACL6_NETS_PRIVATE|ACL6_HOSTS_DNS|false|no|false|udp| - |53| - | - | - | - |
|v6_forward_accept_udp_dns_2|top| - |forward| - |accept|ACL6_NETS_PRIVATE|ACL6_HOSTS_DNS|false|no|false|udp| - |53| - | - | - | - |
|v6_forward_accept_tcp_web|top| - |forward| - |accept|ACL6_NETS_PRIVATE|ACL6_HOSTS_WEB|false|no|false|tcp| - |80,443| - | - | - | - |
|v6_forward_accept_udp_radius_servers|top| - |forward| - |accept|ACL6_HOSTS_RADIUS_CLIENTS|ACL6_HOSTS_RADIUS_SERVERS|false|no|false|udp| - |1812-1813| - | - | - | - |
|v6_forward_accept_udp_apps_dmz|top| - |forward| - |accept|ACL6_HOSTS_NETFLOW|ACL6_HOSTS_APPS_DMZ|false|no|false|udp| - |4739| - | - | - | - |
|v6_forward_accept_tcp_monitoring|top| - |forward| - |accept|ACL6_NETS_PRIVATE|ACL6_HOSTS_MONITORING|false|no|false|tcp| - |8086| - | - | - | - |
|v6_forward_accept_udp_private|top| - |forward| - |accept|ACL6_HOSTS_MONITORING|ACL6_NETS_PRIVATE|false|no|false|udp| - |161| - | - | - | - |
|v6_forward_accept_tcp_private|top| - |forward| - |accept|ACL6_HOSTS_MONITORING|ACL6_NETS_PRIVATE|false|no|false|tcp| - |3000,8053,443,80,3306| - | - | - | - |
|v6_forward_accept_udp_apps_trusted|top| - |forward| - |accept|ACL6_HOSTS_SYSLOG|ACL6_HOSTS_APPS_TRUSTED|false|no|false|udp| - |514| - | - | - | - |
|v6_forward_accept_tcp_apps_dmz|top| - |forward| - |accept|ACL6_HOSTS_APPS_DMZ|ACL6_HOSTS_APPS_DMZ|false|no|false|tcp| - |2376,2377,7946| - | - | - | - |
|v6_forward_accept_udp_apps_dmz_2|top| - |forward| - |accept|ACL6_HOSTS_APPS_DMZ|ACL6_HOSTS_APPS_DMZ|false|no|false|udp| - |4789,7946| - | - | - | - |
|v6_forward_accept_tcp_apps_trusted|top| - |forward| - |accept|ACL6_HOSTS_APPS_TRUSTED|ACL6_HOSTS_APPS_TRUSTED|false|no|false|tcp| - |2376,2377,7946| - | - | - | - |
|v6_forward_accept_udp_apps_trusted_2|top| - |forward| - |accept|ACL6_HOSTS_APPS_TRUSTED|ACL6_HOSTS_APPS_TRUSTED|false|no|false|udp| - |4789,7946| - | - | - | - |
|v6_forward_accept_tcp_storage|top| - |forward| - |accept|ACL6_HOSTS_STORAGE_CLIENTS|ACL6_HOSTS_STORAGE|false|no|false|tcp| - |111,892,2049| - | - | - | - |
|v6_forward_accept_udp_storage|top| - |forward| - |accept|ACL6_HOSTS_STORAGE_CLIENTS|ACL6_HOSTS_STORAGE|false|no|false|udp| - |111,892,2049| - | - | - | - |
|v6_input_reject_icmpv6_private|bot| - |input| - |reject|ACL6_NETS_PRIVATE| - |true|FW=in_reject T=icmp S=PRIV|false|icmpv6| - | - | - |icmp-admin-prohibited| - | - |
|v6_forward_reject_icmpv6_private|bot| - |forward| - |reject|ACL6_NETS_PRIVATE| - |true|FW=fw_reject T=icmp S=PRIV|false|icmpv6| - | - | - |icmp-admin-prohibited| - | - |
|v6_input_drop_icmpv6|bot| - |input| - |drop| - | - |true|FW=in_reject T=icmp S=PUB|false|icmpv6| - | - | - | - | - | - |
|v6_forward_drop_icmpv6|bot| - |forward| - |drop| - | - |true|FW=fw_reject T=icmp S=PUB|false|icmpv6| - | - | - | - | - | - |
|v6_input_reject_tcp_private|bot| - |input| - |reject|ACL6_NETS_PRIVATE| - |true|FW=in_reject T=SSH S=PRIV|false|tcp| - |22| - |icmp-admin-prohibited| - | - |
|v6_forward_reject_tcp_private|bot| - |forward| - |reject|ACL6_NETS_PRIVATE| - |true|FW=fw_reject T=SSH S=PRIV|false|tcp| - |22| - |icmp-admin-prohibited| - | - |
|v6_input_drop_tcp_internet|bot| - |input| - |drop|ACL6_NETS_INTERNET| - |true|FW=in_drop T=SSH S=PUB|false|tcp| - |22| - | - | - | - |
|v6_forward_drop_tcp_internet|bot| - |forward| - |drop|ACL6_NETS_INTERNET| - |true|FW=fw_drop T=SSH S=PUB|false|tcp| - |22| - | - | - | - |
|v6_input_drop_nolog|bot| - |input| - |drop|ACL6_NETS_NOLOG| - |false|no|false| - | - | - | - | - | - | - |
|v6_forward_drop_nolog|bot| - |forward| - |drop|ACL6_NETS_NOLOG| - |false|no|false| - | - | - | - | - | - | - |
|v6_input_drop_nolog_2|bot| - |input| - |drop| - |ACL6_NETS_NOLOG|false|no|false| - | - | - | - | - | - | - |
|v6_forward_drop_nolog_2|bot| - |forward| - |drop| - |ACL6_NETS_NOLOG|false|no|false| - | - | - | - | - | - | - |
|v6_input_drop_internet|bot| - |input|invalid|drop|ACL6_NETS_INTERNET| - |false|no|false| - | - | - | - | - | - | - |
|v6_forward_drop_internet|bot| - |forward|invalid|drop|ACL6_NETS_INTERNET| - |false|no|false| - | - | - | - | - | - | - |
|v6_input_reject_private|bot| - |input| - |reject|ACL6_NETS_PRIVATE| - |true|FW=in_reject S=PRIV|false| - | - | - | - |icmp-admin-prohibited| - | - |
|v6_forward_reject_private|bot| - |forward| - |reject|ACL6_NETS_PRIVATE| - |true|FW=fw_reject S=PRIV|false| - | - | - | - |icmp-admin-prohibited| - | - |
|v6_input_drop_internet_2|bot| - |input| - |drop|ACL6_NETS_INTERNET| - |true|FW=in_drop S=PUB|false| - | - | - | - | - | - | - |
|v6_forward_drop_internet_2|bot| - |forward| - |drop|ACL6_NETS_INTERNET| - |true|FW=fw_drop S=PUB|false| - | - | - | - | - | - | - |
|fw_in_dhcp_netV6_1safe|top| - |input| - |accept| - | - | - | - |false|udp| - |546| - | - |1safe| - |
|fw_in_dhcp_netV6_2dmz|top| - |input| - |accept| - | - | - | - |false|udp| - |546| - | - |2dmz| - |
|fw_in_dhcp_netV6_3services|top| - |input| - |accept| - | - | - | - |false|udp| - |546| - | - |3services| - |
|fw_in_dhcp_netV6_4guest|top| - |input| - |accept| - | - | - | - |false|udp| - |546| - | - |4guest| - |
|fw_in_dhcp_netV6_5lab|top| - |input| - |accept| - | - | - | - |false|udp| - |546| - | - |5lab| - |
|fw_v6_forward_wgmain_in_lab-mikro5_main_to_lab-mikro1_main|top| - |forward| - |accept| - | - | - | - |false| - | - | - | - | - |int_w_lab-mikro5_main_to_lab-mikro1_main| - |
|fwv6_in_wireguard_lab-mikro5_main_to_lab-mikro1_main|top| - |input| - |accept| - | - | - | - |false|udp| - |51820| - | - | - | - |
|fw_in_bgpv6_lab-mikro5_main_to_lab-mikro1_main|top| - |input| - |accept| - | - | - | - |false|tcp| - |179|2001:db8:10:0:10:25:fa:0/127| - | - |2001:db8:10:0:10:25:fa:0/127|
|fw_in_bfdv6_lab-mikro5_main_to_lab-mikro1_main|top| - |input| - |accept| - | - | - | - |false|udp| - |3784|2001:db8:10:0:10:25:fa:0/127| - | - |2001:db8:10:0:10:25:fa:0/127|
|fw_v6_forward_wgmain_in_lab-mikro5_main_to_lab-mikro2_main|top| - |forward| - |accept| - | - | - | - |false| - | - | - | - | - |int_w_lab-mikro5_main_to_lab-mikro2_main| - |
|fwv6_in_wireguard_lab-mikro5_main_to_lab-mikro2_main|top| - |input| - |accept| - | - | - | - |false|udp| - |51821| - | - | - | - |
|fw_in_bgpv6_lab-mikro5_main_to_lab-mikro2_main|top| - |input| - |accept| - | - | - | - |false|tcp| - |179|2001:db8:10:0:10:25:fa:2/127| - | - |2001:db8:10:0:10:25:fa:2/127|
|fw_in_bfdv6_lab-mikro5_main_to_lab-mikro2_main|top| - |input| - |accept| - | - | - | - |false|udp| - |3784|2001:db8:10:0:10:25:fa:2/127| - | - |2001:db8:10:0:10:25:fa:2/127|
|fw_v6_forward_wgmain_in_lab-mikro5_main_to_lab-mikro3_main|top| - |forward| - |accept| - | - | - | - |false| - | - | - | - | - |int_w_lab-mikro5_main_to_lab-mikro3_main| - |
|fwv6_in_wireguard_lab-mikro5_main_to_lab-mikro3_main|top| - |input| - |accept| - | - | - | - |false|udp| - |51822| - | - | - | - |
|fw_in_bgpv6_lab-mikro5_main_to_lab-mikro3_main|top| - |input| - |accept| - | - | - | - |false|tcp| - |179|2001:db8:10:0:10:25:fa:4/127| - | - |2001:db8:10:0:10:25:fa:4/127|
|fw_in_bfdv6_lab-mikro5_main_to_lab-mikro3_main|top| - |input| - |accept| - | - | - | - |false|udp| - |3784|2001:db8:10:0:10:25:fa:4/127| - | - |2001:db8:10:0:10:25:fa:4/127|

### /ipv6/firewall/mangle  
comment|order|chain|dst_port|protocol|log|disabled|passthrough|action|new_packet_mark|tcp_flags|new_mss|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|v6_mangle_prerouting_markpacket_tcp|top|prerouting|22,53,179,1194-1200,1883,3389,5201|tcp|false|false|true|mark-packet|p1| - | - |
|v6_mangle_prerouting_markpacket_udp|top|prerouting|53,179,119,500,1194-1200,3724,3478-3479,3000-4000|udp|false|false|true|mark-packet|p1| - | - |
|v6_mangle_prerouting_markpacket_udp_2|top|prerouting|4500,4784,5000-5030,6000-6030,6060,6113,6250,7000-7030,9000-10000|udp|false|false|true|mark-packet|p1| - | - |
|v6_mangle_prerouting_markpacket_udp_3|top|prerouting|50000-65535|udp|false|false|true|mark-packet|p1| - | - |
|v6_mangle_prerouting_markpacket_tcp_2|top|prerouting|80|tcp|false|false|true|mark-packet|p3| - | - |
|v6_mangle_prerouting_markpacket_udp_4|top|prerouting|6881-6889|udp|false|false|true|mark-packet|p3| - | - |
|v6_mangle_forward_changemss_tcp|top|forward| - |tcp| - | - |true|change-mss| - |syn|clamp-to-pmtu|

