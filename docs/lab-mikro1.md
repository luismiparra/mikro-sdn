#DEVICE: lab-mikro1

## General Config  
  
### /interface/bridge  
comment|name|ingress_filtering|pvid|vlan_filtering|
|---------|---------|---------|---------|---------|
|bridge-vlans|bridge-vlans|false|999|true|

### /interface/bridge/port  
comment|interface|ingress_filtering|bridge|pvid|edge|
|---------|---------|---------|---------|---------|---------|
|int_br_TRUNK_ether3|ether3|true|bridge-vlans|999| - |
|int_br_vlan_1_access_ether2|ether2|true|bridge-vlans|1| - |
|int_br_11_lab-mikro1_1safe|vxlan_local_lab-mikro1_1safe_11|true|bridge-vlans|1|yes|
|int_br_12_lab-mikro1_2dmz|vxlan_local_lab-mikro1_2dmz_12|true|bridge-vlans|2|yes|
|int_br_13_lab-mikro1_3services|vxlan_local_lab-mikro1_3services_13|true|bridge-vlans|3|yes|
|int_br_14_lab-mikro1_4guest|vxlan_local_lab-mikro1_4guest_14|true|bridge-vlans|4|yes|
|int_br_15_lab-mikro1_5lab|vxlan_local_lab-mikro1_5lab_15|true|bridge-vlans|5|yes|
|int_br_lab-mikro2_1safe_21|vxlan_remote_lab-mikro2_1safe_21|true|bridge-vlans|321|yes|
|int_br_lab-mikro2_2dmz_22|vxlan_remote_lab-mikro2_2dmz_22|true|bridge-vlans|322|yes|
|int_br_lab-mikro2_3services_23|vxlan_remote_lab-mikro2_3services_23|true|bridge-vlans|323|yes|
|int_br_lab-mikro2_4guest_24|vxlan_remote_lab-mikro2_4guest_24|true|bridge-vlans|324|yes|
|int_br_lab-mikro2_5lab_25|vxlan_remote_lab-mikro2_5lab_25|true|bridge-vlans|325|yes|
|int_br_lab-mikro3_1safe_31|vxlan_remote_lab-mikro3_1safe_31|true|bridge-vlans|331|yes|
|int_br_lab-mikro3_2dmz_32|vxlan_remote_lab-mikro3_2dmz_32|true|bridge-vlans|332|yes|
|int_br_lab-mikro3_3services_33|vxlan_remote_lab-mikro3_3services_33|true|bridge-vlans|333|yes|
|int_br_lab-mikro3_4guest_34|vxlan_remote_lab-mikro3_4guest_34|true|bridge-vlans|334|yes|
|int_br_lab-mikro3_5lab_35|vxlan_remote_lab-mikro3_5lab_35|true|bridge-vlans|335|yes|
|int_br_lab-mikro4_1safe_41|vxlan_remote_lab-mikro4_1safe_41|true|bridge-vlans|341|yes|
|int_br_lab-mikro4_2dmz_42|vxlan_remote_lab-mikro4_2dmz_42|true|bridge-vlans|342|yes|
|int_br_lab-mikro4_3services_43|vxlan_remote_lab-mikro4_3services_43|true|bridge-vlans|343|yes|
|int_br_lab-mikro4_4guest_44|vxlan_remote_lab-mikro4_4guest_44|true|bridge-vlans|344|yes|
|int_br_lab-mikro4_5lab_45|vxlan_remote_lab-mikro4_5lab_45|true|bridge-vlans|345|yes|
|int_br_lab-mikro6_1safe_61|vxlan_remote_lab-mikro6_1safe_61|true|bridge-vlans|361|yes|
|int_br_lab-mikro6_2dmz_62|vxlan_remote_lab-mikro6_2dmz_62|true|bridge-vlans|362|yes|
|int_br_lab-mikro6_3services_63|vxlan_remote_lab-mikro6_3services_63|true|bridge-vlans|363|yes|
|int_br_lab-mikro6_4guest_64|vxlan_remote_lab-mikro6_4guest_64|true|bridge-vlans|364|yes|
|int_br_lab-mikro6_5lab_65|vxlan_remote_lab-mikro6_5lab_65|true|bridge-vlans|365|yes|

### /interface/bridge/vlan  
comment|tagged|vlan_ids|bridge|
|---------|---------|---------|---------|
|int_br_vlan_1|bridge-vlans,ether3|1|bridge-vlans|
|int_br_vlan_2|bridge-vlans,ether3|2|bridge-vlans|
|int_br_vlan_3|bridge-vlans,ether3|3|bridge-vlans|
|int_br_vlan_4|bridge-vlans,ether3|4|bridge-vlans|
|int_br_vlan_5|bridge-vlans,ether3|5|bridge-vlans|
|int_br_vlan_321|bridge-vlans,ether3|321|bridge-vlans|
|int_br_vlan_322|bridge-vlans,ether3|322|bridge-vlans|
|int_br_vlan_323|bridge-vlans,ether3|323|bridge-vlans|
|int_br_vlan_324|bridge-vlans,ether3|324|bridge-vlans|
|int_br_vlan_325|bridge-vlans,ether3|325|bridge-vlans|
|int_br_vlan_331|bridge-vlans,ether3|331|bridge-vlans|
|int_br_vlan_332|bridge-vlans,ether3|332|bridge-vlans|
|int_br_vlan_333|bridge-vlans,ether3|333|bridge-vlans|
|int_br_vlan_334|bridge-vlans,ether3|334|bridge-vlans|
|int_br_vlan_335|bridge-vlans,ether3|335|bridge-vlans|
|int_br_vlan_341|bridge-vlans,ether3|341|bridge-vlans|
|int_br_vlan_342|bridge-vlans,ether3|342|bridge-vlans|
|int_br_vlan_343|bridge-vlans,ether3|343|bridge-vlans|
|int_br_vlan_344|bridge-vlans,ether3|344|bridge-vlans|
|int_br_vlan_345|bridge-vlans,ether3|345|bridge-vlans|
|int_br_vlan_361|bridge-vlans,ether3|361|bridge-vlans|
|int_br_vlan_362|bridge-vlans,ether3|362|bridge-vlans|
|int_br_vlan_363|bridge-vlans,ether3|363|bridge-vlans|
|int_br_vlan_364|bridge-vlans,ether3|364|bridge-vlans|
|int_br_vlan_365|bridge-vlans,ether3|365|bridge-vlans|

### /interface/list  
comment|include|name|
|---------|---------|---------|
|int_list_inside|static|list_inside|
|int_list_wireguard_main|static|list_wireguard_main|
|int_list_external_wireguard_main|static|list_external_wireguard_main|
|list_internet|static|list_internet|
|list_wg_vpn_admins|static|list_wg_vpn_admins|
|list_wg_vpn_default|static|list_wg_vpn_default|

### /interface/list/member  
comment|interface|list|
|---------|---------|---------|
|list_item_int_v_1safe|1safe|list_inside|
|list_item_int_v_2dmz|2dmz|list_inside|
|list_item_int_v_3services|3services|list_inside|
|list_item_int_v_4guest|4guest|list_inside|
|list_item_int_v_5lab|5lab|list_inside|
|list_item_int_w_lab-mikro1_main_to_lab-mikro2_main|int_w_lab-mikro1_main_to_lab-mikro2_main|list_wireguard_main|
|list_item_int_w_lab-mikro1_main_to_lab-mikro3_main|int_w_lab-mikro1_main_to_lab-mikro3_main|list_wireguard_main|
|list_item_int_w_lab-mikro1_main_to_lab-mikro4_main|int_w_lab-mikro1_main_to_lab-mikro4_main|list_wireguard_main|
|list_external_item_int_w_lab-mikro1_main_to_lab-mikro5_main|int_w_lab-mikro1_main_to_lab-mikro5_main|list_external_wireguard_main|
|list_external_item_int_w_lab-mikro1_main_to_lab-mikro6_main|int_w_lab-mikro1_main_to_lab-mikro6_main|list_external_wireguard_main|
|list_item_int_w_lab-mikro1_main_to_externalhost1_main|int_w_lab-mikro1_main_to_externalhost1_main|list_wireguard_main|
|list_external_item_int_w_lab-mikro1_main_to_externalhost2_main|int_w_lab-mikro1_main_to_externalhost2_main|list_external_wireguard_main|
|list_internet_item_int_eth1|ether1|list_internet|
|local_auto__list_item_int_w_vpn_mgmt_vpn|int_w_vpn_mgmt_vpn|list_wg_vpn_admins|
|list_item_int_w_vpn_admin_vpn1|int_w_vpn_admin_vpn1|list_wg_vpn_admins|
|list_item_int_w_vpn_user_vpn2|int_w_vpn_user_vpn2|list_wg_vpn_default|

### /interface/vlan  
comment|name|vlan_id|interface|
|---------|---------|---------|---------|
|vlan_1safe|1safe|1|bridge-vlans|
|vlan_2dmz|2dmz|2|bridge-vlans|
|vlan_3services|3services|3|bridge-vlans|
|vlan_4guest|4guest|4|bridge-vlans|
|vlan_5lab|5lab|5|bridge-vlans|
|vlan_isolated|isolated|999|bridge-vlans|
|321_vx_21_lab-mikro2_1safe|321_vx_21_lab-mikro2_1safe|321|bridge-vlans|
|322_vx_22_lab-mikro2_2dmz|322_vx_22_lab-mikro2_2dmz|322|bridge-vlans|
|323_vx_23_lab-mikro2_3services|323_vx_23_lab-mikro2_3services|323|bridge-vlans|
|324_vx_24_lab-mikro2_4guest|324_vx_24_lab-mikro2_4guest|324|bridge-vlans|
|325_vx_25_lab-mikro2_5lab|325_vx_25_lab-mikro2_5lab|325|bridge-vlans|
|331_vx_31_lab-mikro3_1safe|331_vx_31_lab-mikro3_1safe|331|bridge-vlans|
|332_vx_32_lab-mikro3_2dmz|332_vx_32_lab-mikro3_2dmz|332|bridge-vlans|
|333_vx_33_lab-mikro3_3services|333_vx_33_lab-mikro3_3services|333|bridge-vlans|
|334_vx_34_lab-mikro3_4guest|334_vx_34_lab-mikro3_4guest|334|bridge-vlans|
|335_vx_35_lab-mikro3_5lab|335_vx_35_lab-mikro3_5lab|335|bridge-vlans|
|341_vx_41_lab-mikro4_1safe|341_vx_41_lab-mikro4_1safe|341|bridge-vlans|
|342_vx_42_lab-mikro4_2dmz|342_vx_42_lab-mikro4_2dmz|342|bridge-vlans|
|343_vx_43_lab-mikro4_3services|343_vx_43_lab-mikro4_3services|343|bridge-vlans|
|344_vx_44_lab-mikro4_4guest|344_vx_44_lab-mikro4_4guest|344|bridge-vlans|
|345_vx_45_lab-mikro4_5lab|345_vx_45_lab-mikro4_5lab|345|bridge-vlans|
|361_vx_61_lab-mikro6_1safe|361_vx_61_lab-mikro6_1safe|361|bridge-vlans|
|362_vx_62_lab-mikro6_2dmz|362_vx_62_lab-mikro6_2dmz|362|bridge-vlans|
|363_vx_63_lab-mikro6_3services|363_vx_63_lab-mikro6_3services|363|bridge-vlans|
|364_vx_64_lab-mikro6_4guest|364_vx_64_lab-mikro6_4guest|364|bridge-vlans|
|365_vx_65_lab-mikro6_5lab|365_vx_65_lab-mikro6_5lab|365|bridge-vlans|

### /interface/vxlan  
comment|name|mtu|dont_fragment|loop_protect|port|vni|
|---------|---------|---------|---------|---------|---------|---------|
|vxlan_local_lab-mikro1_1safe_11|vxlan_local_lab-mikro1_1safe_11|1230|inherit|on|8472|11|
|vxlan_local_lab-mikro1_2dmz_12|vxlan_local_lab-mikro1_2dmz_12|1230|inherit|on|8472|12|
|vxlan_local_lab-mikro1_3services_13|vxlan_local_lab-mikro1_3services_13|1230|inherit|on|8472|13|
|vxlan_local_lab-mikro1_4guest_14|vxlan_local_lab-mikro1_4guest_14|1230|inherit|on|8472|14|
|vxlan_local_lab-mikro1_5lab_15|vxlan_local_lab-mikro1_5lab_15|1230|inherit|on|8472|15|
|vxlan_remote_lab-mikro2_1safe_21|vxlan_remote_lab-mikro2_1safe_21|1230|inherit|on|8472|21|
|vxlan_remote_lab-mikro2_2dmz_22|vxlan_remote_lab-mikro2_2dmz_22|1230|inherit|on|8472|22|
|vxlan_remote_lab-mikro2_3services_23|vxlan_remote_lab-mikro2_3services_23|1230|inherit|on|8472|23|
|vxlan_remote_lab-mikro2_4guest_24|vxlan_remote_lab-mikro2_4guest_24|1230|inherit|on|8472|24|
|vxlan_remote_lab-mikro2_5lab_25|vxlan_remote_lab-mikro2_5lab_25|1230|inherit|on|8472|25|
|vxlan_remote_lab-mikro3_1safe_31|vxlan_remote_lab-mikro3_1safe_31|1230|inherit|on|8472|31|
|vxlan_remote_lab-mikro3_2dmz_32|vxlan_remote_lab-mikro3_2dmz_32|1230|inherit|on|8472|32|
|vxlan_remote_lab-mikro3_3services_33|vxlan_remote_lab-mikro3_3services_33|1230|inherit|on|8472|33|
|vxlan_remote_lab-mikro3_4guest_34|vxlan_remote_lab-mikro3_4guest_34|1230|inherit|on|8472|34|
|vxlan_remote_lab-mikro3_5lab_35|vxlan_remote_lab-mikro3_5lab_35|1230|inherit|on|8472|35|
|vxlan_remote_lab-mikro4_1safe_41|vxlan_remote_lab-mikro4_1safe_41|1230|inherit|on|8472|41|
|vxlan_remote_lab-mikro4_2dmz_42|vxlan_remote_lab-mikro4_2dmz_42|1230|inherit|on|8472|42|
|vxlan_remote_lab-mikro4_3services_43|vxlan_remote_lab-mikro4_3services_43|1230|inherit|on|8472|43|
|vxlan_remote_lab-mikro4_4guest_44|vxlan_remote_lab-mikro4_4guest_44|1230|inherit|on|8472|44|
|vxlan_remote_lab-mikro4_5lab_45|vxlan_remote_lab-mikro4_5lab_45|1230|inherit|on|8472|45|
|vxlan_remote_lab-mikro6_1safe_61|vxlan_remote_lab-mikro6_1safe_61|1230|inherit|on|8472|61|
|vxlan_remote_lab-mikro6_2dmz_62|vxlan_remote_lab-mikro6_2dmz_62|1230|inherit|on|8472|62|
|vxlan_remote_lab-mikro6_3services_63|vxlan_remote_lab-mikro6_3services_63|1230|inherit|on|8472|63|
|vxlan_remote_lab-mikro6_4guest_64|vxlan_remote_lab-mikro6_4guest_64|1230|inherit|on|8472|64|
|vxlan_remote_lab-mikro6_5lab_65|vxlan_remote_lab-mikro6_5lab_65|1230|inherit|on|8472|65|

### /interface/vxlan/vteps  
comment|interface|port|remote_ip|
|---------|---------|---------|---------|
|vtep_10.0.0.2__lab-mikro1_1safe_11|vxlan_local_lab-mikro1_1safe_11|8472|10.0.0.2|
|vtep_10.0.0.3__lab-mikro1_1safe_11|vxlan_local_lab-mikro1_1safe_11|8472|10.0.0.3|
|vtep_10.0.0.4__lab-mikro1_1safe_11|vxlan_local_lab-mikro1_1safe_11|8472|10.0.0.4|
|vtep_10.0.0.6__lab-mikro1_1safe_11|vxlan_local_lab-mikro1_1safe_11|8472|10.0.0.6|
|vtep_10.0.0.2__lab-mikro1_2dmz_12|vxlan_local_lab-mikro1_2dmz_12|8472|10.0.0.2|
|vtep_10.0.0.3__lab-mikro1_2dmz_12|vxlan_local_lab-mikro1_2dmz_12|8472|10.0.0.3|
|vtep_10.0.0.4__lab-mikro1_2dmz_12|vxlan_local_lab-mikro1_2dmz_12|8472|10.0.0.4|
|vtep_10.0.0.6__lab-mikro1_2dmz_12|vxlan_local_lab-mikro1_2dmz_12|8472|10.0.0.6|
|vtep_10.0.0.2__lab-mikro1_3services_13|vxlan_local_lab-mikro1_3services_13|8472|10.0.0.2|
|vtep_10.0.0.3__lab-mikro1_3services_13|vxlan_local_lab-mikro1_3services_13|8472|10.0.0.3|
|vtep_10.0.0.4__lab-mikro1_3services_13|vxlan_local_lab-mikro1_3services_13|8472|10.0.0.4|
|vtep_10.0.0.6__lab-mikro1_3services_13|vxlan_local_lab-mikro1_3services_13|8472|10.0.0.6|
|vtep_10.0.0.2__lab-mikro1_4guest_14|vxlan_local_lab-mikro1_4guest_14|8472|10.0.0.2|
|vtep_10.0.0.3__lab-mikro1_4guest_14|vxlan_local_lab-mikro1_4guest_14|8472|10.0.0.3|
|vtep_10.0.0.4__lab-mikro1_4guest_14|vxlan_local_lab-mikro1_4guest_14|8472|10.0.0.4|
|vtep_10.0.0.6__lab-mikro1_4guest_14|vxlan_local_lab-mikro1_4guest_14|8472|10.0.0.6|
|vtep_10.0.0.2__lab-mikro1_5lab_15|vxlan_local_lab-mikro1_5lab_15|8472|10.0.0.2|
|vtep_10.0.0.3__lab-mikro1_5lab_15|vxlan_local_lab-mikro1_5lab_15|8472|10.0.0.3|
|vtep_10.0.0.4__lab-mikro1_5lab_15|vxlan_local_lab-mikro1_5lab_15|8472|10.0.0.4|
|vtep_10.0.0.6__lab-mikro1_5lab_15|vxlan_local_lab-mikro1_5lab_15|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro2_1safe_21|vxlan_remote_lab-mikro2_1safe_21|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro2_1safe_21|vxlan_remote_lab-mikro2_1safe_21|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro2_1safe_21|vxlan_remote_lab-mikro2_1safe_21|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro2_1safe_21|vxlan_remote_lab-mikro2_1safe_21|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro2_2dmz_22|vxlan_remote_lab-mikro2_2dmz_22|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro2_2dmz_22|vxlan_remote_lab-mikro2_2dmz_22|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro2_2dmz_22|vxlan_remote_lab-mikro2_2dmz_22|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro2_2dmz_22|vxlan_remote_lab-mikro2_2dmz_22|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro2_3services_23|vxlan_remote_lab-mikro2_3services_23|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro2_3services_23|vxlan_remote_lab-mikro2_3services_23|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro2_3services_23|vxlan_remote_lab-mikro2_3services_23|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro2_3services_23|vxlan_remote_lab-mikro2_3services_23|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro2_4guest_24|vxlan_remote_lab-mikro2_4guest_24|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro2_4guest_24|vxlan_remote_lab-mikro2_4guest_24|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro2_4guest_24|vxlan_remote_lab-mikro2_4guest_24|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro2_4guest_24|vxlan_remote_lab-mikro2_4guest_24|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro2_5lab_25|vxlan_remote_lab-mikro2_5lab_25|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro2_5lab_25|vxlan_remote_lab-mikro2_5lab_25|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro2_5lab_25|vxlan_remote_lab-mikro2_5lab_25|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro2_5lab_25|vxlan_remote_lab-mikro2_5lab_25|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro3_1safe_31|vxlan_remote_lab-mikro3_1safe_31|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro3_1safe_31|vxlan_remote_lab-mikro3_1safe_31|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro3_1safe_31|vxlan_remote_lab-mikro3_1safe_31|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro3_1safe_31|vxlan_remote_lab-mikro3_1safe_31|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro3_2dmz_32|vxlan_remote_lab-mikro3_2dmz_32|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro3_2dmz_32|vxlan_remote_lab-mikro3_2dmz_32|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro3_2dmz_32|vxlan_remote_lab-mikro3_2dmz_32|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro3_2dmz_32|vxlan_remote_lab-mikro3_2dmz_32|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro3_3services_33|vxlan_remote_lab-mikro3_3services_33|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro3_3services_33|vxlan_remote_lab-mikro3_3services_33|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro3_3services_33|vxlan_remote_lab-mikro3_3services_33|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro3_3services_33|vxlan_remote_lab-mikro3_3services_33|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro3_4guest_34|vxlan_remote_lab-mikro3_4guest_34|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro3_4guest_34|vxlan_remote_lab-mikro3_4guest_34|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro3_4guest_34|vxlan_remote_lab-mikro3_4guest_34|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro3_4guest_34|vxlan_remote_lab-mikro3_4guest_34|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro3_5lab_35|vxlan_remote_lab-mikro3_5lab_35|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro3_5lab_35|vxlan_remote_lab-mikro3_5lab_35|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro3_5lab_35|vxlan_remote_lab-mikro3_5lab_35|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro3_5lab_35|vxlan_remote_lab-mikro3_5lab_35|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro4_1safe_41|vxlan_remote_lab-mikro4_1safe_41|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro4_1safe_41|vxlan_remote_lab-mikro4_1safe_41|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro4_1safe_41|vxlan_remote_lab-mikro4_1safe_41|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro4_1safe_41|vxlan_remote_lab-mikro4_1safe_41|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro4_2dmz_42|vxlan_remote_lab-mikro4_2dmz_42|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro4_2dmz_42|vxlan_remote_lab-mikro4_2dmz_42|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro4_2dmz_42|vxlan_remote_lab-mikro4_2dmz_42|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro4_2dmz_42|vxlan_remote_lab-mikro4_2dmz_42|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro4_3services_43|vxlan_remote_lab-mikro4_3services_43|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro4_3services_43|vxlan_remote_lab-mikro4_3services_43|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro4_3services_43|vxlan_remote_lab-mikro4_3services_43|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro4_3services_43|vxlan_remote_lab-mikro4_3services_43|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro4_4guest_44|vxlan_remote_lab-mikro4_4guest_44|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro4_4guest_44|vxlan_remote_lab-mikro4_4guest_44|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro4_4guest_44|vxlan_remote_lab-mikro4_4guest_44|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro4_4guest_44|vxlan_remote_lab-mikro4_4guest_44|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro4_5lab_45|vxlan_remote_lab-mikro4_5lab_45|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro4_5lab_45|vxlan_remote_lab-mikro4_5lab_45|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro4_5lab_45|vxlan_remote_lab-mikro4_5lab_45|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro4_5lab_45|vxlan_remote_lab-mikro4_5lab_45|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro6_1safe_61|vxlan_remote_lab-mikro6_1safe_61|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro6_1safe_61|vxlan_remote_lab-mikro6_1safe_61|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro6_1safe_61|vxlan_remote_lab-mikro6_1safe_61|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro6_1safe_61|vxlan_remote_lab-mikro6_1safe_61|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro6_2dmz_62|vxlan_remote_lab-mikro6_2dmz_62|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro6_2dmz_62|vxlan_remote_lab-mikro6_2dmz_62|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro6_2dmz_62|vxlan_remote_lab-mikro6_2dmz_62|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro6_2dmz_62|vxlan_remote_lab-mikro6_2dmz_62|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro6_3services_63|vxlan_remote_lab-mikro6_3services_63|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro6_3services_63|vxlan_remote_lab-mikro6_3services_63|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro6_3services_63|vxlan_remote_lab-mikro6_3services_63|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro6_3services_63|vxlan_remote_lab-mikro6_3services_63|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro6_4guest_64|vxlan_remote_lab-mikro6_4guest_64|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro6_4guest_64|vxlan_remote_lab-mikro6_4guest_64|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro6_4guest_64|vxlan_remote_lab-mikro6_4guest_64|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro6_4guest_64|vxlan_remote_lab-mikro6_4guest_64|8472|10.0.0.6|
|vtep_10.0.0.2_lab-mikro6_5lab_65|vxlan_remote_lab-mikro6_5lab_65|8472|10.0.0.2|
|vtep_10.0.0.3_lab-mikro6_5lab_65|vxlan_remote_lab-mikro6_5lab_65|8472|10.0.0.3|
|vtep_10.0.0.4_lab-mikro6_5lab_65|vxlan_remote_lab-mikro6_5lab_65|8472|10.0.0.4|
|vtep_10.0.0.6_lab-mikro6_5lab_65|vxlan_remote_lab-mikro6_5lab_65|8472|10.0.0.6|

### /interface/wireguard  
comment|mtu|name|listen_port|
|---------|---------|---------|---------|
|int_w_lab-mikro1_main_to_lab-mikro2_main|1280|int_w_lab-mikro1_main_to_lab-mikro2_main|51820|
|int_w_lab-mikro1_main_to_lab-mikro3_main|1280|int_w_lab-mikro1_main_to_lab-mikro3_main|51821|
|int_w_lab-mikro1_main_to_lab-mikro4_main|1280|int_w_lab-mikro1_main_to_lab-mikro4_main|51822|
|int_w_lab-mikro1_main_to_lab-mikro5_main|1280|int_w_lab-mikro1_main_to_lab-mikro5_main|51823|
|int_w_lab-mikro1_main_to_lab-mikro6_main|1280|int_w_lab-mikro1_main_to_lab-mikro6_main|51824|
|int_w_lab-mikro1_main_to_externalhost1_main|1280|int_w_lab-mikro1_main_to_externalhost1_main|61200|
|int_w_lab-mikro1_main_to_externalhost2_main|1280|int_w_lab-mikro1_main_to_externalhost2_main|61202|
|local_auto__int_w_vpn_mgmt_vpn|1280|int_w_vpn_mgmt_vpn|30001|
|int_w_vpn_admin_vpn1|1280|int_w_vpn_admin_vpn1|30002|
|int_w_vpn_user_vpn2|1280|int_w_vpn_user_vpn2|30003|

### /interface/wireguard/peers  
name|comment|allowed_address|endpoint_address|endpoint_port|interface|persistent_keepalive|is_responder|disabled|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|int_wg_peer_lab-mikro1_main_to_lab-mikro2_main|int_wg_peer_lab-mikro1_main_to_lab-mikro2_main|0.0.0.0/0,::/0|lab-mikro2.yourdomain.int|51820|int_w_lab-mikro1_main_to_lab-mikro2_main|10s| - | - |
|int_wg_peer_lab-mikro1_main_to_lab-mikro3_main|int_wg_peer_lab-mikro1_main_to_lab-mikro3_main|0.0.0.0/0,::/0|lab-mikro3.yourdomain.int|51820|int_w_lab-mikro1_main_to_lab-mikro3_main|10s| - | - |
|int_wg_peer_lab-mikro1_main_to_lab-mikro4_main|int_wg_peer_lab-mikro1_main_to_lab-mikro4_main|0.0.0.0/0,::/0| - |51820|int_w_lab-mikro1_main_to_lab-mikro4_main|10s|true| - |
|int_wg_peer_lab-mikro1_main_to_lab-mikro5_main|int_wg_peer_lab-mikro1_main_to_lab-mikro5_main|0.0.0.0/0,::/0| - |51820|int_w_lab-mikro1_main_to_lab-mikro5_main|10s|true| - |
|int_wg_peer_lab-mikro1_main_to_lab-mikro6_main|int_wg_peer_lab-mikro1_main_to_lab-mikro6_main|0.0.0.0/0,::/0| - |51820|int_w_lab-mikro1_main_to_lab-mikro6_main|10s|true| - |
|int_wg_peer_lab-mikro1_main_to_externalhost1_main|int_wg_peer_lab-mikro1_main_to_externalhost1_main|0.0.0.0/0,::/0| - |51820|int_w_lab-mikro1_main_to_externalhost1_main|10s|true| - |
|int_wg_peer_lab-mikro1_main_to_externalhost2_main|int_wg_peer_lab-mikro1_main_to_externalhost2_main|0.0.0.0/0,::/0| - |51820|int_w_lab-mikro1_main_to_externalhost2_main|10s|true| - |
|local_auto__peer_wgvpn_mgmt_vpn_2|local_auto__peer_wgvpn_mgmt_vpn_2|10.151.100.2/32,1::10:151:64:2/128| - | - |int_w_vpn_mgmt_vpn|25s|true|true|
|local_auto__peer_wgvpn_mgmt_vpn_3|local_auto__peer_wgvpn_mgmt_vpn_3|10.151.100.3/32,1::10:151:64:3/128| - | - |int_w_vpn_mgmt_vpn|25s|true|true|
|local_auto__peer_wgvpn_mgmt_vpn_4|local_auto__peer_wgvpn_mgmt_vpn_4|10.151.100.4/32,1::10:151:64:4/128| - | - |int_w_vpn_mgmt_vpn|25s|true|false|
|local_auto__peer_wgvpn_mgmt_vpn_5|local_auto__peer_wgvpn_mgmt_vpn_5|10.151.100.5/32,1::10:151:64:5/128| - | - |int_w_vpn_mgmt_vpn|25s|true|false|
|local_auto__peer_wgvpn_mgmt_vpn_6|local_auto__peer_wgvpn_mgmt_vpn_6|10.151.100.6/32,1::10:151:64:6/128| - | - |int_w_vpn_mgmt_vpn|25s|true|false|
|local_auto__peer_wgvpn_mgmt_vpn_7|local_auto__peer_wgvpn_mgmt_vpn_7|10.151.100.7/32,1::10:151:64:7/128| - | - |int_w_vpn_mgmt_vpn|25s|true|false|
|local_auto__peer_wgvpn_mgmt_vpn_8|local_auto__peer_wgvpn_mgmt_vpn_8|10.151.100.8/32,1::10:151:64:8/128| - | - |int_w_vpn_mgmt_vpn|25s|true|false|
|local_auto__peer_wgvpn_mgmt_vpn_9|local_auto__peer_wgvpn_mgmt_vpn_9|10.151.100.9/32,1::10:151:64:9/128| - | - |int_w_vpn_mgmt_vpn|25s|true|false|
|peer_wgvpn_admin_vpn1_2|peer_wgvpn_admin_vpn1_2|10.151.101.2/32,1::10:151:65:2/128| - | - |int_w_vpn_admin_vpn1|25s|true|false|
|peer_wgvpn_admin_vpn1_3|peer_wgvpn_admin_vpn1_3|10.151.101.3/32,1::10:151:65:3/128| - | - |int_w_vpn_admin_vpn1|25s|true|false|
|peer_wgvpn_admin_vpn1_4|peer_wgvpn_admin_vpn1_4|10.151.101.4/32,1::10:151:65:4/128| - | - |int_w_vpn_admin_vpn1|25s|true|false|
|peer_wgvpn_admin_vpn1_5|peer_wgvpn_admin_vpn1_5|10.151.101.5/32,1::10:151:65:5/128| - | - |int_w_vpn_admin_vpn1|25s|true|false|
|peer_wgvpn_admin_vpn1_6|peer_wgvpn_admin_vpn1_6|10.151.101.6/32,1::10:151:65:6/128| - | - |int_w_vpn_admin_vpn1|25s|true|false|
|peer_wgvpn_admin_vpn1_7|peer_wgvpn_admin_vpn1_7|10.151.101.7/32,1::10:151:65:7/128| - | - |int_w_vpn_admin_vpn1|25s|true|false|
|peer_wgvpn_admin_vpn1_8|peer_wgvpn_admin_vpn1_8|10.151.101.8/32,1::10:151:65:8/128| - | - |int_w_vpn_admin_vpn1|25s|true|false|
|peer_wgvpn_admin_vpn1_9|peer_wgvpn_admin_vpn1_9|10.151.101.9/32,1::10:151:65:9/128| - | - |int_w_vpn_admin_vpn1|25s|true|false|
|peer_wgvpn_user_vpn2_2|peer_wgvpn_user_vpn2_2|10.151.102.2/32,1::10:151:66:2/128| - | - |int_w_vpn_user_vpn2|25s|true|false|
|peer_wgvpn_user_vpn2_3|peer_wgvpn_user_vpn2_3|10.151.102.3/32,1::10:151:66:3/128| - | - |int_w_vpn_user_vpn2|25s|true|false|
|peer_wgvpn_user_vpn2_4|peer_wgvpn_user_vpn2_4|10.151.102.4/32,1::10:151:66:4/128| - | - |int_w_vpn_user_vpn2|25s|true|false|
|peer_wgvpn_user_vpn2_5|peer_wgvpn_user_vpn2_5|10.151.102.5/32,1::10:151:66:5/128| - | - |int_w_vpn_user_vpn2|25s|true|false|
|peer_wgvpn_user_vpn2_6|peer_wgvpn_user_vpn2_6|10.151.102.6/32,1::10:151:66:6/128| - | - |int_w_vpn_user_vpn2|25s|true|false|
|peer_wgvpn_user_vpn2_7|peer_wgvpn_user_vpn2_7|10.151.102.7/32,1::10:151:66:7/128| - | - |int_w_vpn_user_vpn2|25s|true|false|
|peer_wgvpn_user_vpn2_8|peer_wgvpn_user_vpn2_8|10.151.102.8/32,1::10:151:66:8/128| - | - |int_w_vpn_user_vpn2|25s|true|false|
|peer_wgvpn_user_vpn2_9|peer_wgvpn_user_vpn2_9|10.151.102.9/32,1::10:151:66:9/128| - | - |int_w_vpn_user_vpn2|25s|true|false|

### /ip/address  
interface|comment|address|disabled|
|---------|---------|---------|---------|
|lo|ip_lo_10.0.0.1|10.0.0.1/32|false|
|1safe|ip_1safe_10.151.1.1|10.151.1.1/24| - |
|2dmz|ip_2dmz_10.151.2.1|10.151.2.1/24| - |
|3services|ip_3services_10.151.3.1|10.151.3.1/24| - |
|4guest|ip_4guest_10.151.4.1|10.151.4.1/24| - |
|5lab|ip_5lab_10.151.5.1|10.151.5.1/24| - |
|1safe|ip_VIP_1safe_10.151.91.1|10.151.91.1/29| - |
|1safe|ip_VIP_1safe_10.151.91.2|10.151.91.2/29| - |
|1safe|ip_VIP_1safe_10.151.91.3|10.151.91.3/29| - |
|1safe|ip_VIP_1safe_10.151.91.4|10.151.91.4/29| - |
|1safe|ip_VIP_1safe_10.151.91.5|10.151.91.5/29| - |
|1safe|ip_VIP_1safe_10.151.91.6|10.151.91.6/29| - |
|int_w_lab-mikro1_main_to_lab-mikro2_main|ip_wg_10.151.250.1_30|10.151.250.1/30| - |
|int_w_lab-mikro1_main_to_lab-mikro3_main|ip_wg_10.151.250.5_30|10.151.250.5/30| - |
|int_w_lab-mikro1_main_to_lab-mikro4_main|ip_wg_10.154.250.2_30|10.154.250.2/30| - |
|int_w_lab-mikro1_main_to_lab-mikro5_main|ip_wg_10.155.250.2_30|10.155.250.2/30| - |
|int_w_lab-mikro1_main_to_lab-mikro6_main|ip_wg_10.156.250.2_30|10.156.250.2/30| - |
|int_w_lab-mikro1_main_to_externalhost1_main|ip_wg_10.222.250.2_30|10.222.250.2/30| - |
|int_w_lab-mikro1_main_to_externalhost2_main|ip_wg_10.223.250.2_30|10.223.250.2/30| - |
|int_w_vpn_mgmt_vpn|local_auto__ip_wgvpn_mgmt_vpn_10.151.100.1|10.151.100.1/24| - |
|int_w_vpn_admin_vpn1|ip_wgvpn_admin_vpn1_10.151.101.1|10.151.101.1/24| - |
|int_w_vpn_user_vpn2|ip_wgvpn_user_vpn2_10.151.102.1|10.151.102.1/24| - |

### /ip/cloud  
ddns_enabled|ddns_update_interval|
|---------|---------|
|yes|10m|

### /ip/dhcp-server  
comment|name|address_pool|interface|lease_time|
|---------|---------|---------|---------|---------|
|dhcpV4_1safe|dhcpV4_1safe|pool_10.151.1.0/24|1safe|1d|
|dhcpV4_2dmz|dhcpV4_2dmz|pool_10.151.2.0/24|2dmz|1d|
|dhcpV4_3services|dhcpV4_3services|pool_10.151.3.0/24|3services|1d|
|dhcpV4_4guest|dhcpV4_4guest|pool_10.151.4.0/24|4guest|1d|
|dhcpV4_5lab|dhcpV4_5lab|pool_10.151.5.0/24|5lab|1d|

### /ip/dhcp-server/lease  
comment|address|mac-address|server|
|---------|---------|---------|---------|
|example_vlan1|10.1.1.2|AA:BB:CC:DD:EE:11|dhcpV4_1safe|
|example_vlan2|10.1.2.2|AA:BB:CC:DD:EE:22|dhcpV4_2dmz|

### /ip/dhcp-server/network  
comment|address|dns_server|ntp_server|gateway|domain|
|---------|---------|---------|---------|---------|---------|
|dhcp_netV4_1safe|10.151.1.0/24|8.8.8.8,8.8.4.4|10.151.2.2|10.151.1.1|yourdomain.int|
|dhcp_netV4_2dmz|10.151.2.0/24|8.8.8.8,8.8.4.4|10.151.2.2|10.151.2.1|yourdomain.int|
|dhcp_netV4_3services|10.151.3.0/24|8.8.8.8,8.8.4.4|10.151.2.2|10.151.3.1|yourdomain.int|
|dhcp_netV4_4guest|10.151.4.0/24|8.8.8.8,8.8.4.4|10.151.2.2|10.151.4.1|yourdomain.int|
|dhcp_netV4_5lab|10.151.5.0/24|8.8.8.8,8.8.4.4|10.151.2.2|10.151.5.1|yourdomain.int|

### /ip/dns  
allow_remote_requests|
|---------|
|no|

### /ip/pool  
comment|name|ranges|
|---------|---------|---------|
|pool_10.151.1.0/24|pool_10.151.1.0/24|10.151.1.100-10.151.1.250|
|pool_10.151.2.0/24|pool_10.151.2.0/24|10.151.2.100-10.151.2.250|
|pool_10.151.3.0/24|pool_10.151.3.0/24|10.151.3.100-10.151.3.250|
|pool_10.151.4.0/24|pool_10.151.4.0/24|10.151.4.100-10.151.4.250|
|pool_10.151.5.0/24|pool_10.151.5.0/24|10.151.5.100-10.151.5.250|

### /ip/route  
comment|dst-address|gateway|routing-table|disabled|
|---------|---------|---------|---------|---------|
|ip_route_internet_vpn|0.0.0.0/0|10.151.250.6|internet_vpn|false|
|ip_route_core_transit_lab-mikro2|0.0.0.0/0|10.151.250.2|core_transit_lab-mikro2|false|
|ip_route_core_transit_lab-mikro3|0.0.0.0/0|10.151.250.6|core_transit_lab-mikro3|false|

### /ip/service  
name|disabled|port|certificate|
|---------|---------|---------|---------|
|telnet|true| - | - |
|ftp|true|21| - |
|www|false|80| - |
|www-ssl|false|443|mycert.int.crt|
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
|0|10.155.2.2|4739|ipfix|1|

### /ipv6/address  
interface|comment|address|
|---------|---------|---------|
|1safe|ip_1safe_1::10:151:1:1|1::10:151:1:1/112|
|2dmz|ip_2dmz_1::10:151:2:1|1::10:151:2:1/112|
|3services|ip_3services_1::10:151:3:1|1::10:151:3:1/112|
|4guest|ip_4guest_1::10:151:4:1|1::10:151:4:1/112|
|5lab|ip_5lab_1::10:151:5:1|1::10:151:5:1/112|
|2dmz|ip_2dmz_1:0:0:8802::1_slaac|1:0:0:8802::1/64|
|4guest|ip_4guest_1:0:0:8804::1_slaac|1:0:0:8804::1/64|
|5lab|ip_5lab_1:0:0:8805::1_slaac|1:0:0:8805::1/64|
|int_w_lab-mikro1_main_to_lab-mikro2_main|ip_wg_1::10:151:fa:0_127|1::10:151:fa:0/127|
|int_w_lab-mikro1_main_to_lab-mikro3_main|ip_wg_1::10:151:fa:2_127|1::10:151:fa:2/127|
|int_w_lab-mikro1_main_to_lab-mikro4_main|ip_wg_1::10:154:fa:1_127|1::10:154:fa:1/127|
|int_w_lab-mikro1_main_to_lab-mikro5_main|ip_wg_1::10:155:fa:1_127|1::10:155:fa:1/127|
|int_w_lab-mikro1_main_to_lab-mikro6_main|ip_wg_1::10:156:fa:1_127|1::10:156:fa:1/127|
|int_w_lab-mikro1_main_to_externalhost1_main|ip_wg_1::10:222:fa:1_127|1::10:222:fa:1/127|
|int_w_lab-mikro1_main_to_externalhost2_main|ip_wg_1::10:223:fa:1_127|1::10:223:fa:1/127|
|int_w_vpn_mgmt_vpn|local_auto__ipv6_wgvpn_mgmt_vpn_1::10:151:64:1|1::10:151:64:1/112|
|int_w_vpn_admin_vpn1|ipv6_wgvpn_admin_vpn1_1::10:151:65:1|1::10:151:65:1/112|
|int_w_vpn_user_vpn2|ipv6_wgvpn_user_vpn2_1::10:151:66:1|1::10:151:66:1/112|

### /ipv6/dhcp-server  
comment|name|address_pool|interface|lease_time|
|---------|---------|---------|---------|---------|
|dhcpV6_1safe|dhcpV6_1safe|pool_1::10:151:1:0/112|1safe|1d|
|dhcpV6_2dmz|dhcpV6_2dmz|pool_1::10:151:2:0/112|2dmz|1d|
|dhcpV6_3services|dhcpV6_3services|pool_1::10:151:3:0/112|3services|1d|
|dhcpV6_4guest|dhcpV6_4guest|pool_1::10:151:4:0/112|4guest|1d|
|dhcpV6_5lab|dhcpV6_5lab|pool_1::10:151:5:0/112|5lab|1d|

### /ipv6/pool  
comment|name|prefix|prefix_length|
|---------|---------|---------|---------|
|pool_1::10:151:1:0/112|pool_1::10:151:1:0/112|1::10:151:1:0/112|112|
|pool_1::10:151:2:0/112|pool_1::10:151:2:0/112|1::10:151:2:0/112|112|
|pool_1::10:151:3:0/112|pool_1::10:151:3:0/112|1::10:151:3:0/112|112|
|pool_1::10:151:4:0/112|pool_1::10:151:4:0/112|1::10:151:4:0/112|112|
|pool_1::10:151:5:0/112|pool_1::10:151:5:0/112|1::10:151:5:0/112|112|

### /routing/bfd/configuration  
comment|disabled|multiplier|interfaces|
|---------|---------|---------|---------|
|bfd_wireguard_interfaces|false|25|list_wireguard_main|
|bfd_any|false|25| - |

### /routing/bgp/connection  
comment|name|as|disabled|local.role|output.redistribute|remote.address|remote.as|router-id|routing_table|vrf|use-bfd|input.filter|output.filter_chain|address_families|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|bgp_v4_lab-mikro1_main__lab-mikro2_main|bgp_v4_lab-mikro1_main__lab-mikro2_main|10|false|ebgp|connected|10.151.250.2|20|10.5.5.11|main|main|true|filter_v4_any_priority|filter_v4_any| - |
|bgp_v6_lab-mikro1_main__lab-mikro2_main|bgp_v6_lab-mikro1_main__lab-mikro2_main|10|false|ebgp|connected|1::10:151:fa:1|20|10.5.5.11|main|main|true|filter_v6_any_priority|filter_v6_any|ipv6|
|bgp_v4_lab-mikro1_main__lab-mikro3_main|bgp_v4_lab-mikro1_main__lab-mikro3_main|10|false|ebgp|connected|10.151.250.6|30|10.5.5.11|main|main|true|filter_v4_any|filter_v4_any| - |
|bgp_v6_lab-mikro1_main__lab-mikro3_main|bgp_v6_lab-mikro1_main__lab-mikro3_main|10|false|ebgp|connected|1::10:151:fa:3|30|10.5.5.11|main|main|true|filter_v6_any|filter_v6_any|ipv6|
|bgp_v4_lab-mikro1_main__lab-mikro4_main|bgp_v4_lab-mikro1_main__lab-mikro4_main|10|false|ebgp|connected|10.154.250.1|40|10.5.5.11|main|main|true|filter_v4_rptest4|filter_v4_any| - |
|bgp_v6_lab-mikro1_main__lab-mikro4_main|bgp_v6_lab-mikro1_main__lab-mikro4_main|10|false|ebgp|connected|1::10:154:fa:0|40|10.5.5.11|main|main|true|filter_v6_rptest4|filter_v6_any|ipv6|
|bgp_v4_lab-mikro1_main__lab-mikro5_main|bgp_v4_lab-mikro1_main__lab-mikro5_main|10|false|ebgp|connected|10.155.250.1|50|10.5.5.11|main|main|true|filter_v4_rptest5|filter_v4_any| - |
|bgp_v6_lab-mikro1_main__lab-mikro5_main|bgp_v6_lab-mikro1_main__lab-mikro5_main|10|false|ebgp|connected|1::10:155:fa:0|50|10.5.5.11|main|main|true|filter_v6_rptest5|filter_v6_any|ipv6|
|bgp_v4_lab-mikro1_main__lab-mikro6_main|bgp_v4_lab-mikro1_main__lab-mikro6_main|10|false|ebgp|connected|10.156.250.1|60|10.5.5.11|main|main|true|filter_v4_rptest6|filter_v4_any| - |
|bgp_v6_lab-mikro1_main__lab-mikro6_main|bgp_v6_lab-mikro1_main__lab-mikro6_main|10|false|ebgp|connected|1::10:156:fa:0|60|10.5.5.11|main|main|true|filter_v6_rptest6|filter_v6_any|ipv6|
|bgp_v4_externalhost1_main__lab-mikro1_main|bgp_v4_externalhost1_main__lab-mikro1_main|10|false|ebgp|connected|10.222.250.1|200|10.5.5.11|main|main|true|filter_external_v4_rptest200|filter_v4_any| - |
|bgp_v6_externalhost1_main__lab-mikro1_main|bgp_v6_externalhost1_main__lab-mikro1_main|10|false|ebgp|connected|1::10:222:fa:0|200|10.5.5.11|main|main|true|filter_external_v6_rptest200|filter_v6_any|ipv6|
|bgp_v4_externalhost2_main__lab-mikro1_main|bgp_v4_externalhost2_main__lab-mikro1_main|10|false|ebgp|connected|10.223.250.1|202|10.5.5.11|main|main|true|filter_external_v4_rptest202|filter_v4_any| - |
|bgp_v6_externalhost2_main__lab-mikro1_main|bgp_v6_externalhost2_main__lab-mikro1_main|10|false|ebgp|connected|1::10:223:fa:0|202|10.5.5.11|main|main|true|filter_external_v6_rptest202|filter_v6_any|ipv6|

### /routing/filter/rule  
comment|chain|disabled|rule|
|---------|---------|---------|---------|
|filter_v4_rptest2|filter_v4_rptest2|false|if (dst in 10.152.0.0/16 || dst in 10.0.0.2/32) {accept}|
|filter_v4_rptest1|filter_v4_rptest1|false|if (dst in 10.151.0.0/16 || dst in 10.0.0.1/32) {accept}|
|filter_v4_any|filter_v4_any|false|if (dst in 10.0.0.0/8) {set bgp-path-peer-prepend 2; accept}|
|filter_v4_any_priority|filter_v4_any_priority|false|if (dst in 10.0.0.0/8) {set bgp-path-peer-prepend 1; accept}|
|filter_v6_rptest2|filter_v6_rptest2|false|if (dst in 1:0:0:0:10:152:0:0/96 || dst in 1:0:0:9000:0000:0000:0000:0000/53) {accept}|
|filter_v6_rptest1|filter_v6_rptest1|false|if (dst in 1:0:0:0:10:151:0:0/96 || dst in 1:0:0:8800:0000:0000:0000:0000/53) {accept}|
|filter_v6_any|filter_v6_any|false|if (dst in ::/0) {set bgp-path-peer-prepend 2; accept}|
|filter_v6_any_priority|filter_v6_any_priority|false|if (dst in ::/0) {set bgp-path-peer-prepend 1; accept}|
|filter_v4_rptest3|filter_v4_rptest3|false|if (dst in 10.153.0.0/16 || dst in 10.0.0.3/32) {accept}|
|filter_v6_rptest3|filter_v6_rptest3|false|if (dst in 1:0:0:0:10:153:0:0/96 || dst in 1:0:0:9800:0000:0000:0000:0000/53) {accept}|
|filter_v4_rptest4|filter_v4_rptest4|false|if (dst in 10.154.0.0/16 || dst in 10.0.0.4/32) {accept}|
|filter_v6_rptest4|filter_v6_rptest4|false|if (dst in 1:0:0:0:10:154:0:0/96 || dst in 1:0:0:b000:0000:0000:0000:0000/53) {accept}|
|filter_v4_rptest5|filter_v4_rptest5|false|if (dst in 10.155.0.0/16 || dst in 10.0.0.5/32) {accept}|
|filter_v6_rptest5|filter_v6_rptest5|false|if (dst in 1:0:0:0:10:155:0:0/96 || dst in 2600:70ff:f082:1000:0000:0000:0000:0000/53) {accept}|
|filter_v4_rptest6|filter_v4_rptest6|false|if (dst in 10.156.0.0/16 || dst in 10.0.0.6/32) {accept}|
|filter_v6_rptest6|filter_v6_rptest6|false|if (dst in 1:0:0:0:10:156:0:0/96 || dst in 1:0:0:a800:0000:0000:0000:0000/53) {accept}|
|filter_external_v4_rptest200|filter_external_v4_rptest200|false|if (dst in 10.222.222.200/32 || dst in 10.0.0.7/32 ) {accept}|
|filter_external_v6_rptest200|filter_external_v6_rptest200|false|if (dst in 1:0:0:0:10:222:0:0/96) {accept}|
|filter_v4_rptest200|filter_v4_rptest200|false|if (dst in 10.222.0.0/16 || dst in 10.0.0.7/32) {accept}|
|filter_v6_rptest200|filter_v6_rptest200|false|if (dst in 1:0:0:0:10:222:0:0/96 || dst in 1:0:0:a000:0000:0000:0000:0000/53) {accept}|
|filter_external_v4_rptest202|filter_external_v4_rptest202|false|if (dst in 10.222.222.202/32 || dst in 10.0.0.8/32 ) {accept}|
|filter_external_v6_rptest202|filter_external_v6_rptest202|false|if (dst in 1:0:0:0:10:223:0:0/96) {accept}|
|filter_v4_rptest202|filter_v4_rptest202|false|if (dst in 10.223.0.0/16 || dst in 10.0.0.8/32) {accept}|
|filter_v6_rptest202|filter_v6_rptest202|false|if (dst in 1:0:0:0:10:223:0:0/96 || dst in 2001:470:c8b6:8000:0000:0000:0000:0000/53) {accept}|

### /routing/rule  
comment|table|action|disabled|routing-mark|
|---------|---------|---------|---------|---------|
|routing_rule_internet_vpn|internet_vpn|lookup-only-in-table|false|internet_vpn|
|routing_rule_main|main|lookup|false|main|
|routing_rule_core_transit_lab-mikro2|core_transit_lab-mikro2|lookup-only-in-table|false|core_transit_lab-mikro2|
|routing_rule_core_transit_lab-mikro3|core_transit_lab-mikro3|lookup-only-in-table|false|core_transit_lab-mikro3|

### /routing/table  
comment|name|fib|
|---------|---------|---------|
|routing_table_internet_vpn|internet_vpn||
|routing_table_core_transit_lab-mikro2|core_transit_lab-mikro2||
|routing_table_core_transit_lab-mikro3|core_transit_lab-mikro3||

### /snmp  
contact|enabled|
|---------|---------|
|admin@yourdomain.com|yes|

### /system/clock  
time_zone_name|
|---------|
|Europe/Madrid|

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
|3|10.1.2.2|514|1|

### /system/ntp/client  
enabled|
|---------|
|yes|

### /system/ntp/client/servers  
comment|address|
|---------|---------|
|rp-ntp|0.es.pool.ntp.org|

### /tool/netwatch  
comment|host|interval|type|down_script|up_script|port|
|---------|---------|---------|---------|---------|---------|---------|
|netwatch_wg_lab-mikro1_main_to_lab-mikro2_main|10.151.250.2|30s|icmp| - | - | - |
|netwatch_wg_lab-mikro1_main_to_lab-mikro3_main|10.151.250.6|30s|icmp| - | - | - |
|netwatch_wg_lab-mikro1_main_to_lab-mikro4_main|10.154.250.1|30s|icmp| - | - | - |
|netwatch_wg_lab-mikro1_main_to_lab-mikro5_main|10.155.250.1|30s|icmp| - | - | - |
|netwatch_wg_lab-mikro1_main_to_lab-mikro6_main|10.156.250.1|30s|icmp| - | - | - |
|netwatch_wg_lab-mikro1_main_to_externalhost1_main|10.222.250.1|30s|icmp| - | - | - |
|netwatch_wg_lab-mikro1_main_to_externalhost2_main|10.223.250.1|30s|icmp| - | - | - |
|netwatch_core_transit_lab-mikro2|10.151.250.2|10s| - |/ip firewall mangle disable [find comment="core_transit_lab-mikro2_mark"];|/ip firewall mangle enable [find comment="core_transit_lab-mikro2_mark"];| - |
|netwatch_core_transit_lab-mikro3|10.151.250.6|10s| - |/ip firewall mangle disable [find comment="core_transit_lab-mikro3_mark"];|/ip firewall mangle enable [find comment="core_transit_lab-mikro3_mark"];| - |
|netwatch_dns1|8.8.8.8|10s| - |/ip firewall nat enable [find comment="NAT_FALLBACK_DNS_1"];|/ip firewall nat disable [find comment="NAT_FALLBACK_DNS_1"];| - |
|netwatch_dns2|8.8.4.4|10s| - |/ip firewall nat enable [find comment="NAT_FALLBACK_DNS_2"];|/ip firewall nat disable [find comment="NAT_FALLBACK_DNS_2"];| - |
|netwatch_tcp_dns_1|8.8.8.8|30s|tcp-conn| - | - |53|
|netwatch_tcp_dns_2|8.8.4.4|30s|tcp-conn| - | - |53|
|netwatch_internet1|8.8.4.4|30s|icmp| - | - | - |
|netwatch_internet2|8.8.8.8|30s|icmp| - | - | - |

## Firewall Config  
  
### /ip/firewall/address-list  
comment|address|
|---------|---------|
|SET_NET4_SAFE|['10.151.1.0/24', '10.152.1.0/24', '10.153.1.0/24', '10.154.1.0/24', '10.155.1.0/24']|
|SET_HOSTS4_ROUTEVIA_WG|['10.151.4.0/24', '10.152.4.0/24', '10.153.4.0/24', '10.154.4.0/24', '10.155.4.0/24']|
|SET_NET4_NOLOG|['127.0.0.1', '224.0.0.1', '255.255.255.255']|
|SET_NET4_PRIVATE|['10.0.0.0/8', '172.16.0.0/12']|
|SET_HOSTS4_ALLOW_MGMT|['127.0.0.1', '10.151.250.0/24', '10.152.250.0/24', '10.153.250.0/24', '10.154.250.0/24', '10.155.250.0/24', '10.156.250.0/24']|
|SET_NET4_INTERNET|['0.0.0.0/0']|
|SET_NET4_RP_DMZ|['10.151.2.0/24', '10.152.2.0/24', '10.153.2.0/24', '10.154.2.0/24', '10.155.2.0/24', '10.156.2.0/24']|
|SET_HOSTS4_NTP|['10.151.2.2']|
|SET_HOSTS4_LOG|['10.151.2.2']|
|SET_HOSTS4_DNS|['10.151.2.88', '10.152.2.88']|

### /ip/firewall/filter  
comment|order|chain|protocol|icmp_options|disabled|action|posi|connection_state|src_address_list|dst_port|log|log_prefix|dst_address_list|reject_with|in_interface|src_address|dst_address|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|icmp_local-0|top|input|icmp|0:0-255|false|accept| - | - | - | - | - | - | - | - | - | - | - |
|icmp_local-3|top|input|icmp|3:0-255|false|accept| - | - | - | - | - | - | - | - | - | - | - |
|icmp_local-8|top|input|icmp|8:0-255|false|accept| - | - | - | - | - | - | - | - | - | - | - |
|icmp_local-11|top|input|icmp|11:0-255|false|accept| - | - | - | - | - | - | - | - | - | - | - |
|icmp_forward-0|top|forward|icmp|0:0-255|false|accept| - | - | - | - | - | - | - | - | - | - | - |
|icmp_forward-3|top|forward|icmp|3:0-255|false|accept| - | - | - | - | - | - | - | - | - | - | - |
|icmp_forward-8|top|forward|icmp|8:0-255|false|accept| - | - | - | - | - | - | - | - | - | - | - |
|icmp_forward-11|top|forward|icmp|11:0-255|false|accept| - | - | - | - | - | - | - | - | - | - | - |
|forward_fasttrack|posi|forward| - | - | - |fasttrack-connection|6|established,related| - | - | - | - | - | - | - | - | - |
|FORWARD stablished|posi|forward| - | - | - |accept|6|established,related,untracked| - | - | - | - | - | - | - | - | - |
|INPUT stablished|posi|input| - | - | - |accept|7|established,related,untracked| - | - | - | - | - | - | - | - | - |
|local_mgmt|top|input|tcp| - |false|accept| - | - |SET_HOSTS4_ALLOW_MGMT|21,22,23,80,443,8291,8728,8729,2000|false|no| - | - | - | - | - |
|local_mgmt_udp|top|input|udp| - |false|accept| - | - |SET_HOSTS4_ALLOW_MGMT|161,1812,1813,5678|false|no| - | - | - | - | - |
|vpnmgmt_allow_all|top|input| - | - |false|accept| - | - |SET_HOSTS4_MGMTVPN| - |false|no|SET_HOSTS4_MGMTVPN| - | - | - | - |
|input_monitoring|top|input|udp| - |false|accept| - | - |SET_HOSTS4_MONITORING|161|false|no| - | - | - | - | - |
|internal_to_internetv4|top|forward| - | - |false|accept| - | - |SET_NET4_PRIVATE| - |false|no|!SET_NET4_PRIVATE| - | - | - | - |
|input_internal_icmp_deny|bot|input|icmp| - |false|reject| - | - |SET_NET4_PRIVATE| - |true|FW=in_reject T=icmp S=PRIV IPV=4 | - |icmp-admin-prohibited| - | - | - |
|forward_internal_icmp_deny|bot|forward|icmp| - |false|reject| - | - |SET_NET4_PRIVATE| - |true|FW=fw_reject T=icmp S=PRIV IPV=4 | - |icmp-admin-prohibited| - | - | - |
|input_public_icmp_deny|bot|input|icmp| - |false|drop| - | - | - | - |true|FW=in_reject T=icmp S=PUB IPV=4 | - | - | - | - | - |
|forward_public_icmp_deny|bot|forward|icmp| - |false|drop| - | - | - | - |true|FW=fw_reject T=icmp S=PUB IPV=4 | - | - | - | - | - |
|input_internal_ssh_deny|bot|input|tcp| - |false|reject| - | - |SET_NET4_PRIVATE|22|true|FW=in_reject T=SSH S=PRIV IPV=4 | - |icmp-admin-prohibited| - | - | - |
|forward_internal_ssh_deny|bot|forward|tcp| - |false|reject| - | - |SET_NET4_PRIVATE|22|true|FW=fw_reject T=SSH S=PRIV IPV=4 | - |icmp-admin-prohibited| - | - | - |
|intput_public_ssh_deny|bot|input|tcp| - |false|drop| - | - |SET_NET4_INTERNET|22|true|FW=in_drop T=SSH S=PUB IPV=4 | - | - | - | - | - |
|forward_public_ssh_deny|bot|forward|tcp| - |false|drop| - | - |SET_NET4_INTERNET|22|true|FW=fw_drop T=SSH S=PUB IPV=4 | - | - | - | - | - |
|input_src_nolog_deny|bot|input| - | - |false|drop| - | - |SET_NET4_NOLOG| - |false|no| - | - | - | - | - |
|forward_src_nolog_deny|bot|forward| - | - |false|drop| - | - |SET_NET4_NOLOG| - |false|no| - | - | - | - | - |
|input_dst_nolog_deny|bot|input| - | - |false|drop| - | - | - | - |false|no|SET_NET4_NOLOG| - | - | - | - |
|forward_dst_nolog_deny|bot|forward| - | - |false|drop| - | - | - | - |false|no|SET_NET4_NOLOG| - | - | - | - |
|intput_invalid_public_deny|bot|input| - | - |false|drop| - |invalid|SET_NET4_INTERNET| - |false|no| - | - | - | - | - |
|forward_invalid_public_deny|bot|forward| - | - |false|drop| - |invalid|SET_NET4_INTERNET| - |false|no| - | - | - | - | - |
|input_internal_deny|bot|input| - | - |false|reject| - | - |SET_NET4_PRIVATE| - |true|FW=in_reject S=PRIV IPV=4 | - |icmp-admin-prohibited| - | - | - |
|forward_internal_deny|bot|forward| - | - |false|reject| - | - |SET_NET4_PRIVATE| - |true|FW=fw_reject S=PRIV IPV=4 | - |icmp-admin-prohibited| - | - | - |
|intput_public_deny|bot|input| - | - |false|drop| - | - |SET_NET4_INTERNET| - |true|FW=in_drop S=PUB IPV=4 | - | - | - | - | - |
|forward_public_deny|bot|forward| - | - |false|drop| - | - |SET_NET4_INTERNET| - |true|FW=fw_drop S=PUB IPV=4 | - | - | - | - | - |
|rpban_input_frominside_log|posi|input| - | - |false|log|1| - |SET_NET4_PRIVATE| - |true|RPLOG=rpnftables RPTYPE=insideTOban RPSCOPE=private IPV=4 RPINFO=none ACTION=log|rp-ban-v4| - | - | - | - |
|rpban_forward_frominside_log|posi|forward| - | - |false|log|2| - |SET_NET4_PRIVATE| - |true|RPLOG=rpnftables RPTYPE=insideTOban RPSCOPE=private IPV=4 RPINFO=none ACTION=log|rp-ban-v4| - | - | - | - |
|rpban_input|posi|input| - | - |false|drop|3| - |rp-ban-v4| - |true|RPLOG=rpnftables RPTYPE=rpban RPSCOPE=public IPV=4 RPINFO=none ACTION=drop| - | - | - | - | - |
|rpban_forward|posi|forward| - | - |false|drop|4| - |rp-ban-v4| - |true|RPLOG=rpnftables RPTYPE=rpban RPSCOPE=public IPV=4 RPINFO=none ACTION=drop| - | - | - | - | - |
|forward_safe|top|forward| - | - |false|accept| - | - |SET_NET4_SAFE| - |false|no| - | - | - | - | - |
|input_safe|top|input| - | - |false|accept| - | - |SET_NET4_SAFE| - |false|no| - | - | - | - | - |
|fw_in_dhcp_netV4_1safe|top|input|udp| - |false|accept| - | - | - |67-68| - | - | - | - |1safe| - | - |
|fw_in_dhcp_netV4_2dmz|top|input|udp| - |false|accept| - | - | - |67-68| - | - | - | - |2dmz| - | - |
|fw_in_dhcp_netV4_3services|top|input|udp| - |false|accept| - | - | - |67-68| - | - | - | - |3services| - | - |
|fw_in_dhcp_netV4_4guest|top|input|udp| - |false|accept| - | - | - |67-68| - | - | - | - |4guest| - | - |
|fw_in_dhcp_netV4_5lab|top|input|udp| - |false|accept| - | - | - |67-68| - | - | - | - |5lab| - | - |
|fw_in_vxlan_10.151.250.0/24|top|input|udp| - |false|accept| - | - | - |8472| - | - | - | - | - |10.151.250.0/24| - |
|fw_in_vxlan_10.152.250.0/24|top|input|udp| - |false|accept| - | - | - |8472| - | - | - | - | - |10.152.250.0/24| - |
|fw_in_vxlan_10.153.250.0/24|top|input|udp| - |false|accept| - | - | - |8472| - | - | - | - | - |10.153.250.0/24| - |
|fw_in_vxlan_10.154.250.0/24|top|input|udp| - |false|accept| - | - | - |8472| - | - | - | - | - |10.154.250.0/24| - |
|fw_in_vxlan_10.156.250.0/24|top|input|udp| - |false|accept| - | - | - |8472| - | - | - | - | - |10.156.250.0/24| - |
|fw_v4_forward_wgmain_in_lab-mikro1_main_to_lab-mikro2_main|top|forward| - | - |false|accept| - | - | - | - | - | - | - | - |int_w_lab-mikro1_main_to_lab-mikro2_main| - | - |
|fw_in_wireguard_lab-mikro1_main_to_lab-mikro2_main|top|input|udp| - |false|accept| - | - | - |51820| - | - | - | - | - | - | - |
|fw_in_bgp_lab-mikro1_main_to_lab-mikro2_main|top|input|tcp| - |false|accept| - | - | - |179| - | - | - | - | - |10.151.250.0/30|10.151.250.0/30|
|fw_in_bfd_lab-mikro1_main_to_lab-mikro2_main|top|input|udp| - |false|accept| - | - | - |3784| - | - | - | - | - |10.151.250.0/30|10.151.250.0/30|
|fw_v4_forward_wgmain_in_lab-mikro1_main_to_lab-mikro3_main|top|forward| - | - |false|accept| - | - | - | - | - | - | - | - |int_w_lab-mikro1_main_to_lab-mikro3_main| - | - |
|fw_in_wireguard_lab-mikro1_main_to_lab-mikro3_main|top|input|udp| - |false|accept| - | - | - |51821| - | - | - | - | - | - | - |
|fw_in_bgp_lab-mikro1_main_to_lab-mikro3_main|top|input|tcp| - |false|accept| - | - | - |179| - | - | - | - | - |10.151.250.4/30|10.151.250.4/30|
|fw_in_bfd_lab-mikro1_main_to_lab-mikro3_main|top|input|udp| - |false|accept| - | - | - |3784| - | - | - | - | - |10.151.250.4/30|10.151.250.4/30|
|fw_v4_forward_wgmain_in_lab-mikro1_main_to_lab-mikro4_main|top|forward| - | - |false|accept| - | - | - | - | - | - | - | - |int_w_lab-mikro1_main_to_lab-mikro4_main| - | - |
|fw_in_wireguard_lab-mikro1_main_to_lab-mikro4_main|top|input|udp| - |false|accept| - | - | - |51822| - | - | - | - | - | - | - |
|fw_in_bgp_lab-mikro1_main_to_lab-mikro4_main|top|input|tcp| - |false|accept| - | - | - |179| - | - | - | - | - |10.154.250.0/30|10.154.250.0/30|
|fw_in_bfd_lab-mikro1_main_to_lab-mikro4_main|top|input|udp| - |false|accept| - | - | - |3784| - | - | - | - | - |10.154.250.0/30|10.154.250.0/30|
|fw_in_wireguard_lab-mikro1_main_to_lab-mikro5_main|top|input|udp| - |false|accept| - | - | - |51823| - | - | - | - | - | - | - |
|fw_in_bgp_lab-mikro1_main_to_lab-mikro5_main|top|input|tcp| - |false|accept| - | - | - |179| - | - | - | - | - |10.155.250.0/30|10.155.250.0/30|
|fw_in_bfd_lab-mikro1_main_to_lab-mikro5_main|top|input|udp| - |false|accept| - | - | - |3784| - | - | - | - | - |10.155.250.0/30|10.155.250.0/30|
|fw_in_wireguard_lab-mikro1_main_to_lab-mikro6_main|top|input|udp| - |false|accept| - | - | - |51824| - | - | - | - | - | - | - |
|fw_in_bgp_lab-mikro1_main_to_lab-mikro6_main|top|input|tcp| - |false|accept| - | - | - |179| - | - | - | - | - |10.156.250.0/30|10.156.250.0/30|
|fw_in_bfd_lab-mikro1_main_to_lab-mikro6_main|top|input|udp| - |false|accept| - | - | - |3784| - | - | - | - | - |10.156.250.0/30|10.156.250.0/30|
|fw_v4_forward_wgmain_in_lab-mikro1_main_to_externalhost1_main|top|forward| - | - |false|accept| - | - | - | - | - | - | - | - |int_w_lab-mikro1_main_to_externalhost1_main| - | - |
|fw_in_wireguard_lab-mikro1_main_to_externalhost1_main|top|input|udp| - |false|accept| - | - | - |61200| - | - | - | - | - | - | - |
|fw_in_bgp_lab-mikro1_main_to_externalhost1_main|top|input|tcp| - |false|accept| - | - | - |179| - | - | - | - | - |10.222.250.0/30|10.222.250.0/30|
|fw_in_bfd_lab-mikro1_main_to_externalhost1_main|top|input|udp| - |false|accept| - | - | - |3784| - | - | - | - | - |10.222.250.0/30|10.222.250.0/30|
|fw_in_wireguard_lab-mikro1_main_to_externalhost2_main|top|input|udp| - |false|accept| - | - | - |61202| - | - | - | - | - | - | - |
|fw_in_bgp_lab-mikro1_main_to_externalhost2_main|top|input|tcp| - |false|accept| - | - | - |179| - | - | - | - | - |10.223.250.0/30|10.223.250.0/30|
|fw_in_bfd_lab-mikro1_main_to_externalhost2_main|top|input|udp| - |false|accept| - | - | - |3784| - | - | - | - | - |10.223.250.0/30|10.223.250.0/30|
|fw_v4_forward_vpn_admin_in_mgmt_vpn|top|forward| - | - |false|accept| - | - | - | - | - | - | - | - |int_w_vpn_mgmt_vpn| - | - |
|fw_v4_input_vpn_admin_in_mgmt_vpn|top|input| - | - |false|accept| - | - | - | - | - | - | - | - |int_w_vpn_mgmt_vpn| - | - |
|fw_v4_input_vpn_mgmt_in_mgmt_vpn|top|input| - | - |false|accept| - | - | - | - | - | - | - | - |int_w_vpn_mgmt_vpn| - | - |
|local_auto__fw_in_w_vpn_mgmt_vpn|top|input|udp| - |false|accept| - | - | - |30001| - | - | - | - | - | - | - |
|fw_v4_forward_vpn_admin_in_admin_vpn1|top|forward| - | - |false|accept| - | - | - | - | - | - | - | - |int_w_vpn_admin_vpn1| - | - |
|fw_v4_input_vpn_admin_in_admin_vpn1|top|input| - | - |false|accept| - | - | - | - | - | - | - | - |int_w_vpn_admin_vpn1| - | - |
|fw_in_w_vpn_admin_vpn1|top|input|udp| - |false|accept| - | - | - |30002| - | - | - | - | - | - | - |
|fw_in_w_vpn_user_vpn2|top|input|udp| - |false|accept| - | - | - |30003| - | - | - | - | - | - | - |

### /ip/firewall/mangle  
comment|order|chain|dst_port|protocol|log|disabled|passthrough|action|new_packet_mark|tcp_flags|new_mss|src_address_list|dst_address_list|new_routing_mark|log_prefix|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|p1_tcp_a|top|prerouting|22,53,179,1194-1200,1883,3389,5201|tcp|false|false|true|mark-packet|p1| - | - | - | - | - | - |
|p1_udp_a|top|prerouting|53,179,119,500,1194-1200,3724,3478-3479,3000-4000|udp|false|false|true|mark-packet|p1| - | - | - | - | - | - |
|p1_udp_b|top|prerouting|4500,4784,5000-5030,6000-6030,6060,6113,6250,7000-7030,9000-10000|udp|false|false|true|mark-packet|p1| - | - | - | - | - | - |
|p1_udp_c|top|prerouting|50000-65535|udp|false|false|true|mark-packet|p1| - | - | - | - | - | - |
|p3_tcp_a|top|prerouting|80|tcp|false|false|true|mark-packet|p3| - | - | - | - | - | - |
|p3_udp_a|top|prerouting|6881-6889|udp|false|false|true|mark-packet|p3| - | - | - | - | - | - |
|ipv4_clamp_mss_to_pmtu|top|forward| - |tcp| - | - |true|change-mss| - |syn|clamp-to-pmtu| - | - | - | - |
|nordvpn_mark_forward|top|prerouting| - | - |false|false| - |mark-routing| - | - | - |SET_HOSTS4_ROUTEVIA_WG|!SET_NET4_PRIVATE|internet_vpn|no|
|nordvpn_mark_out|top|output| - | - |false|false| - |mark-routing| - | - | - |SET_HOSTS4_ROUTEVIA_WG|!SET_NET4_PRIVATE|internet_vpn|no|
|webapp_mark_internetvpn_forward|top|prerouting| - | - |false|false| - |mark-routing| - | - | - |SET_HOSTS4_WEBAPP_VPN|!SET_NET4_PRIVATE|internet_vpn|no|
|core_transit_lab-mikro2_mark|top|prerouting| - | - |false|false| - |mark-routing| - | - | - |SET_HOSTS4_VIA_lab-mikro2|!SET_NET4_PRIVATE|core_transit_lab-mikro2|no|
|core_transit_lab-mikro3_mark|top|prerouting| - | - |false|false| - |mark-routing| - | - | - |SET_HOSTS4_VIA_lab-mikro3|!SET_NET4_PRIVATE|core_transit_lab-mikro3|no|

### /ip/firewall/nat  
comment|order|chain|in_interface|dst_port|to_ports|protocol|log|log_prefix|disabled|action|to_addresses|dst_address|src_address|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|example_of_nat_rule1|top|dstnat|ether1|53|30001|udp|false|no|false|dst-nat| - | - | - |
|example_of_nat_rule2|top|dstnat|ether1|10811| - |tcp|false|no|false|dst-nat|10.5.2.15| - | - |
|NAT_FALLBACK_DNS_1|top|dstnat| - |53|53|udp|false| - | - |dst-nat|7.7.7.7|8.8.8.8|10.0.0.0/8|
|NAT_FALLBACK_DNS_2|top|dstnat| - |53|53|udp|false| - | - |dst-nat|6.6.6.6|8.8.4.4|10.0.0.0/8|

### /ipv6/firewall/address-list  
comment|address|
|---------|---------|
|SET_NET6_NOLOG|['::1/128', 'ff02::1/128', 'ff02::1:2/128', 'ff00::/8']|

### /ipv6/firewall/filter  
comment|order|chain|src_address_list|protocol|log|log_prefix|disabled|action|reject_with|dst_port|dst_address_list|connection_state|posi|icmp_options|in_interface|src_address|dst_address|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|input_internal_icmpv6_deny|bot|input|SET_NET6_PRIVATE|icmpv6|true|FW=in_reject T=icmp S=PRIV IPV=6 |false|reject|icmp-admin-prohibited| - | - | - | - | - | - | - | - |
|forward_internal_icmpv6_deny|bot|forward|SET_NET6_PRIVATE|icmpv6|true|FW=fw_reject T=icmp S=PRIV IPV=6 |false|reject|icmp-admin-prohibited| - | - | - | - | - | - | - | - |
|input_public_icmpv6_deny|bot|input| - |icmpv6|true|FW=in_reject T=icmp S=PUB IPV=6 |false|drop| - | - | - | - | - | - | - | - | - |
|forward_public_icmpv6_deny|bot|forward| - |icmpv6|true|FW=fw_reject T=icmp S=PUB IPV=6 |false|drop| - | - | - | - | - | - | - | - | - |
|inputv6_internal_ssh_deny|bot|input|SET_NET6_PRIVATE|tcp|true|FW=in_reject T=SSH S=PRIV IPV=6 |false|reject|icmp-admin-prohibited|22| - | - | - | - | - | - | - |
|forwardv6_internal_ssh_deny|bot|forward|SET_NET6_PRIVATE|tcp|true|FW=fw_reject T=SSH S=PRIV IPV=6 |false|reject|icmp-admin-prohibited|22| - | - | - | - | - | - | - |
|intputv6_public_ssh_deny|bot|input|SET_NET6_INTERNET|tcp|true|FW=in_drop T=SSH S=PUB IPV=6 |false|drop| - |22| - | - | - | - | - | - | - |
|forwardv6_public_ssh_deny|bot|forward|SET_NET6_INTERNET|tcp|true|FW=fw_drop T=SSH S=PUB IPV=6 |false|drop| - |22| - | - | - | - | - | - | - |
|inputv6_src_nolog_deny|bot|input|SET_NET6_NOLOG| - |false|no|false|drop| - | - | - | - | - | - | - | - | - |
|forwardv6_src_nolog_deny|bot|forward|SET_NET6_NOLOG| - |false|no|false|drop| - | - | - | - | - | - | - | - | - |
|inputv6_dst_nolog_deny|bot|input| - | - |false|no|false|drop| - | - |SET_NET6_NOLOG| - | - | - | - | - | - |
|forwardv6_dst_nolog_deny|bot|forward| - | - |false|no|false|drop| - | - |SET_NET6_NOLOG| - | - | - | - | - | - |
|intputv6_invalid_public_deny|bot|input|SET_NET6_INTERNET| - |false|no|false|drop| - | - | - |invalid| - | - | - | - | - |
|forwardv6_invalid_public_deny|bot|forward|SET_NET6_INTERNET| - |false|no|false|drop| - | - | - |invalid| - | - | - | - | - |
|inputv6_internal_deny|bot|input|SET_NET6_PRIVATE| - |true|FW=in_reject S=PRIV IPV=6 |false|reject|icmp-admin-prohibited| - | - | - | - | - | - | - | - |
|forwardv6_internal_deny|bot|forward|SET_NET6_PRIVATE| - |true|FW=fw_reject S=PRIV IPV=6 |false|reject|icmp-admin-prohibited| - | - | - | - | - | - | - | - |
|intputv6_public_deny|bot|input|SET_NET6_INTERNET| - |true|FW=in_drop S=PUB IPV=6 |false|drop| - | - | - | - | - | - | - | - | - |
|forwardv6_public_deny|bot|forward|SET_NET6_INTERNET| - |true|FW=fw_drop S=PUB IPV=6 |false|drop| - | - | - | - | - | - | - | - | - |
|internal_to_internetv6|posi|forward|SET_NET6_PRIVATE| - |false|no|false|accept| - | - |!SET_NET6_PRIVATE| - |5| - | - | - | - |
|fw_ipv6_disabled_sites|posi|forward|SET_NET6_PRIVATE| - |false|no|false|reject| - | - |SET_NET6_DISABLED_IPV6_SITES| - |4| - | - | - | - |
|rpban_input_frominside_log_v6|posi|input|SET_NET4_PRIVATE| - |true|RPLOG=rpnftables RPTYPE=insideTOban RPSCOPE=private IPV=6 RPINFO=none ACTION=log|false|log| - | - |rp-ban-v6| - |1| - | - | - | - |
|rpban_forward_frominside_log_v6|posi|forward|SET_NET4_PRIVATE| - |true|RPLOG=rpnftables RPTYPE=insideTOban RPSCOPE=private IPV=6 RPINFO=none ACTION=log|false|log| - | - |rp-ban-v6| - |2| - | - | - | - |
|rpban_input_v6|posi|input|rp-ban-v6| - |true|RPLOG=rpnftables RPTYPE=rpban RPSCOPE=public IPV=6 RPINFO=none ACTION=drop|false|drop| - | - | - | - |3| - | - | - | - |
|rpban_forward_v6|posi|forward|rp-ban-v6| - |true|RPLOG=rpnftables RPTYPE=rpban RPSCOPE=public IPV=6 RPINFO=none ACTION=drop|false|drop| - | - | - | - |4| - | - | - | - |
|icmpv6_local-1|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |1| - | - | - |
|icmpv6_local-2|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |2| - | - | - |
|icmpv6_local-3|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |3| - | - | - |
|icmpv6_local-4|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |4| - | - | - |
|icmpv6_local-128|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |128| - | - | - |
|icmpv6_local-129|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |129| - | - | - |
|icmpv6_local-133|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |133| - | - | - |
|icmpv6_local-134|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |134| - | - | - |
|icmpv6_local-135|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |135| - | - | - |
|icmpv6_local-136|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |136| - | - | - |
|icmpv6_local-137|top|input| - |icmpv6| - | - |false|accept| - | - | - | - | - |137| - | - | - |
|icmpv6_forward-1|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |1| - | - | - |
|icmpv6_forward-2|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |2| - | - | - |
|icmpv6_forward-3|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |3| - | - | - |
|icmpv6_forward-4|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |4| - | - | - |
|icmpv6_forward-128|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |128| - | - | - |
|icmpv6_forward-129|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |129| - | - | - |
|icmpv6_forward-133|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |133| - | - | - |
|icmpv6_forward-134|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |134| - | - | - |
|icmpv6_forward-135|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |135| - | - | - |
|icmpv6_forward-136|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |136| - | - | - |
|icmpv6_forward-137|top|forward| - |icmpv6| - | - |false|accept| - | - | - | - | - |137| - | - | - |
|INPUT stablished v6|posi|input| - | - | - | - | - |accept| - | - | - |established,related,untracked|5| - | - | - | - |
|FORWARD stablished v6|posi|forward| - | - | - | - | - |accept| - | - | - |established,related,untracked|6| - | - | - | - |
|local_v6_mgmt|top|input|SET_HOSTS6_ALLOW_MGMT|tcp|false|no|false|accept| - |22,8291,8729| - | - | - | - | - | - | - |
|inputv6_monitoring|top|input|SET_HOSTS6_MONITORING|udp|false|no|false|accept| - |161| - | - | - | - | - | - | - |
|fw_in_dhcp_netV6_1safe|top|input| - |udp| - | - |false|accept| - |546| - | - | - | - |1safe| - | - |
|fw_in_dhcp_netV6_2dmz|top|input| - |udp| - | - |false|accept| - |546| - | - | - | - |2dmz| - | - |
|fw_in_dhcp_netV6_3services|top|input| - |udp| - | - |false|accept| - |546| - | - | - | - |3services| - | - |
|fw_in_dhcp_netV6_4guest|top|input| - |udp| - | - |false|accept| - |546| - | - | - | - |4guest| - | - |
|fw_in_dhcp_netV6_5lab|top|input| - |udp| - | - |false|accept| - |546| - | - | - | - |5lab| - | - |
|fw_v6_forward_wgmain_in_lab-mikro1_main_to_lab-mikro2_main|top|forward| - | - | - | - |false|accept| - | - | - | - | - | - |int_w_lab-mikro1_main_to_lab-mikro2_main| - | - |
|fwv6_in_wireguard_lab-mikro1_main_to_lab-mikro2_main|top|input| - |udp| - | - |false|accept| - |51820| - | - | - | - | - | - | - |
|fw_in_bgpv6_lab-mikro1_main_to_lab-mikro2_main|top|input| - |tcp| - | - |false|accept| - |179| - | - | - | - | - |1::10:151:fa:0/127|1::10:151:fa:0/127|
|fw_in_bfdv6_lab-mikro1_main_to_lab-mikro2_main|top|input| - |udp| - | - |false|accept| - |3784| - | - | - | - | - |1::10:151:fa:0/127|1::10:151:fa:0/127|
|fw_v6_forward_wgmain_in_lab-mikro1_main_to_lab-mikro3_main|top|forward| - | - | - | - |false|accept| - | - | - | - | - | - |int_w_lab-mikro1_main_to_lab-mikro3_main| - | - |
|fwv6_in_wireguard_lab-mikro1_main_to_lab-mikro3_main|top|input| - |udp| - | - |false|accept| - |51821| - | - | - | - | - | - | - |
|fw_in_bgpv6_lab-mikro1_main_to_lab-mikro3_main|top|input| - |tcp| - | - |false|accept| - |179| - | - | - | - | - |1::10:151:fa:2/127|1::10:151:fa:2/127|
|fw_in_bfdv6_lab-mikro1_main_to_lab-mikro3_main|top|input| - |udp| - | - |false|accept| - |3784| - | - | - | - | - |1::10:151:fa:2/127|1::10:151:fa:2/127|
|fw_v6_forward_wgmain_in_lab-mikro1_main_to_lab-mikro4_main|top|forward| - | - | - | - |false|accept| - | - | - | - | - | - |int_w_lab-mikro1_main_to_lab-mikro4_main| - | - |
|fwv6_in_wireguard_lab-mikro1_main_to_lab-mikro4_main|top|input| - |udp| - | - |false|accept| - |51822| - | - | - | - | - | - | - |
|fw_in_bgpv6_lab-mikro1_main_to_lab-mikro4_main|top|input| - |tcp| - | - |false|accept| - |179| - | - | - | - | - |1::10:154:fa:0/127|1::10:154:fa:0/127|
|fw_in_bfdv6_lab-mikro1_main_to_lab-mikro4_main|top|input| - |udp| - | - |false|accept| - |3784| - | - | - | - | - |1::10:154:fa:0/127|1::10:154:fa:0/127|
|fwv6_in_wireguard_lab-mikro1_main_to_lab-mikro5_main|top|input| - |udp| - | - |false|accept| - |51823| - | - | - | - | - | - | - |
|fw_in_bgpv6_lab-mikro1_main_to_lab-mikro5_main|top|input| - |tcp| - | - |false|accept| - |179| - | - | - | - | - |1::10:155:fa:0/127|1::10:155:fa:0/127|
|fw_in_bfdv6_lab-mikro1_main_to_lab-mikro5_main|top|input| - |udp| - | - |false|accept| - |3784| - | - | - | - | - |1::10:155:fa:0/127|1::10:155:fa:0/127|
|fwv6_in_wireguard_lab-mikro1_main_to_lab-mikro6_main|top|input| - |udp| - | - |false|accept| - |51824| - | - | - | - | - | - | - |
|fw_in_bgpv6_lab-mikro1_main_to_lab-mikro6_main|top|input| - |tcp| - | - |false|accept| - |179| - | - | - | - | - |1::10:156:fa:0/127|1::10:156:fa:0/127|
|fw_in_bfdv6_lab-mikro1_main_to_lab-mikro6_main|top|input| - |udp| - | - |false|accept| - |3784| - | - | - | - | - |1::10:156:fa:0/127|1::10:156:fa:0/127|
|fw_v6_forward_wgmain_in_lab-mikro1_main_to_externalhost1_main|top|forward| - | - | - | - |false|accept| - | - | - | - | - | - |int_w_lab-mikro1_main_to_externalhost1_main| - | - |
|fwv6_in_wireguard_lab-mikro1_main_to_externalhost1_main|top|input| - |udp| - | - |false|accept| - |61200| - | - | - | - | - | - | - |
|fw_in_bgpv6_lab-mikro1_main_to_externalhost1_main|top|input| - |tcp| - | - |false|accept| - |179| - | - | - | - | - |1::10:222:fa:0/127|1::10:222:fa:0/127|
|fw_in_bfdv6_lab-mikro1_main_to_externalhost1_main|top|input| - |udp| - | - |false|accept| - |3784| - | - | - | - | - |1::10:222:fa:0/127|1::10:222:fa:0/127|
|fwv6_in_wireguard_lab-mikro1_main_to_externalhost2_main|top|input| - |udp| - | - |false|accept| - |61202| - | - | - | - | - | - | - |
|fw_in_bgpv6_lab-mikro1_main_to_externalhost2_main|top|input| - |tcp| - | - |false|accept| - |179| - | - | - | - | - |1::10:223:fa:0/127|1::10:223:fa:0/127|
|fw_in_bfdv6_lab-mikro1_main_to_externalhost2_main|top|input| - |udp| - | - |false|accept| - |3784| - | - | - | - | - |1::10:223:fa:0/127|1::10:223:fa:0/127|
|fw_v6_forward_vpn_admin_in_mgmt_vpn|top|forward| - | - | - | - |false|accept| - | - | - | - | - | - |int_w_vpn_mgmt_vpn| - | - |
|fw_v6_input_vpn_admin_in_mgmt_vpn|top|input| - | - | - | - |false|accept| - | - | - | - | - | - |int_w_vpn_mgmt_vpn| - | - |
|fw_v6_input_vpn_mgmt_in_mgmt_vpn|top|input| - | - | - | - |false|accept| - | - | - | - | - | - |int_w_vpn_mgmt_vpn| - | - |
|local_auto__fwv6_in_w_vpn_mgmt_vpn|top|input| - |udp| - | - |false|accept| - |30001| - | - | - | - | - | - | - |
|fw_v6_forward_vpn_admin_in_admin_vpn1|top|forward| - | - | - | - |false|accept| - | - | - | - | - | - |int_w_vpn_admin_vpn1| - | - |
|fw_v6_input_vpn_admin_in_admin_vpn1|top|input| - | - | - | - |false|accept| - | - | - | - | - | - |int_w_vpn_admin_vpn1| - | - |
|fwg6_in_w_vpn_admin_vpn1|top|input| - |udp| - | - |false|accept| - |30002| - | - | - | - | - | - | - |
|fwg6_in_w_vpn_user_vpn2|top|input| - |udp| - | - |false|accept| - |30003| - | - | - | - | - | - | - |

### /ipv6/firewall/mangle  
comment|order|chain|protocol|passthrough|action|tcp_flags|new_mss|dst_port|log|disabled|new_packet_mark|
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|
|ipv6_clamp_mss_to_pmtu|top|forward|tcp|true|change-mss|syn|clamp-to-pmtu| - | - | - | - |
|p1_tcp_a_v6|top|prerouting|tcp|true|mark-packet| - | - |22,53,179,1194-1200,1883,3389,5201|false|false|p1|
|p1_udp_a_v6|top|prerouting|udp|true|mark-packet| - | - |53,179,119,500,1194-1200,3724,3478-3479,3000-4000|false|false|p1|
|p1_udp_b_v6|top|prerouting|udp|true|mark-packet| - | - |4500,4784,5000-5030,6000-6030,6060,6113,6250,7000-7030,9000-10000|false|false|p1|
|p1_udp_c_v6|top|prerouting|udp|true|mark-packet| - | - |50000-65535|false|false|p1|
|p3_tcp_a_v6|top|prerouting|tcp|true|mark-packet| - | - |80|false|false|p3|
|p3_udp_a_v6|top|prerouting|udp|true|mark-packet| - | - |6881-6889|false|false|p3|

