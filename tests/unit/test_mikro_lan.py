import mikro_lan
import mikro_shared


def _lan_device(device_factory, **overrides):
    device = device_factory(**overrides)
    mikro_shared.prepare_sdn(device)
    return device


def _by_comment(config, comment):
    matches = [item for item in config if item.get("comment") == comment]
    assert matches, f"{comment} not generated"
    return matches[0]


def _comments(config, prefix):
    return [item["comment"] for item in config if item.get("comment", "").startswith(prefix)]


def test_load_config_basic_lan(device_factory):
    device = _lan_device(device_factory)
    config = mikro_lan.load_config(device, [device])

    loopback = _by_comment(config, "ip_lo_10.0.0.1")
    assert loopback["address"] == "10.0.0.1/32" and loopback["disabled"] == "true"
    assert _by_comment(config, "bridge-vlans")["pvid"] == "999"
    assert _by_comment(config, "vlan_1safe")["vlan_id"] == "1"
    assert _by_comment(config, "vlan_isolated")["vlan_id"] == "999"
    _by_comment(config, "list_item_int_v_2dmz")

    # isolated_trunk False -> trunk native vlan 1, untagged in vlan 1
    assert _by_comment(config, "int_br_TRUNK_ether3")["pvid"] == "1"
    assert _by_comment(config, "int_br_vlan_1")["tagged"] == "bridge-vlans"
    assert _by_comment(config, "int_br_vlan_2")["tagged"] == "bridge-vlans,ether3"

    assert _by_comment(config, "ip_1safe_10.21.1.1")["address"] == "10.21.1.1/24"
    assert _comments(config, "ip_1safe_2001:db8")  # ipv6 only on vlans with ipv6
    assert not _comments(config, "ip_2dmz_2001:db8:10:0:10:21:2")
    assert _comments(config, "ip_2dmz_2001:db8:10:8802")  # slaac
    assert _by_comment(config, "pool_10.21.1.0/24")["ranges"] == "10.21.1.100-10.21.1.250"
    pool6 = _by_comment(config, "pool_2001:db8:10:0:10:21:1:0/112")
    assert pool6["prefix_length"] == "112"
    assert _by_comment(config, "dhcpV4_1safe")["address_pool"] == "pool_10.21.1.0/24"
    network = _by_comment(config, "dhcp_netV4_2dmz")
    assert network["dns_server"] == "8.8.8.8,8.8.4.4" and network["gateway"] == "10.21.2.1"
    assert _by_comment(config, "fw_in_dhcp_netV4_1safe")["dst_port"] == "67-68"
    assert _by_comment(config, "dhcpV6_1safe")["lease_time"] == "1d"
    assert _by_comment(config, "fw_in_dhcp_netV6_2dmz")["dst_port"] == "546"
    assert not _comments(config, "vxlan")


def test_load_config_reads_the_old_misspelled_trunk_keys(device_factory):
    # issolated_trunk / trunk_ports_issolated were the keys before they were renamed
    device = _lan_device(device_factory)
    device["lan"].pop("isolated_trunk", None)
    device["lan"].update({"trunk_ports": ["ether3", "ether4"], "trunk_ports_issolated": ["ether4"],
                          "issolated_trunk": True})
    config = mikro_lan.load_config(device, [device])

    trunk = [item for item in config if item.get("comment", "").startswith("int_br_TRUNK_")]
    assert [(item["interface"], item["pvid"]) for item in trunk] == [("ether3", "999"), ("ether4", "999")]


def test_load_config_ports_and_vips(device_factory):
    device = _lan_device(device_factory)
    device["lan"].update({
        "trunk_ports": ["ether3", "ether4"],
        "trunk_ports_isolated": ["ether4", "ether5"],
        "isolated_trunk": False,
        "safe_ports": ["ether6"],
        "access_ports": [{"port": "ether7", "vlan": "2"}],
    })
    device["lan"]["vlans"][0]["ipv4_vip_pool"] = ["10.72.0.0/30"]
    device["lan"]["vlans"][0]["ipv6_vip_pool"] = ["2001:db8::/120"]
    config = mikro_lan.load_config(device, [device])

    trunk = [item for item in config if item.get("comment", "").startswith("int_br_TRUNK_")]
    assert [(item["interface"], item["pvid"]) for item in trunk] == [("ether3", "1"), ("ether4", "999"), ("ether5", "999")]
    assert _by_comment(config, "int_br_1SAFE_access_ether6")["pvid"] == "1"
    assert _by_comment(config, "int_br_vlan_2_access_ether7")["pvid"] == "2"
    assert _by_comment(config, "int_br_vlan_1")["tagged"] == "bridge-vlans,ether4,ether5"

    assert _comments(config, "ip_VIP_1safe_") == ["ip_VIP_1safe_10.72.0.1", "ip_VIP_1safe_10.72.0.2"]
    # ipv6 vip pools are capped at IP_VIP_LIMIT addresses
    assert len(_comments(config, "ipv6_VIP_1safe_")) == mikro_lan.IP_VIP_LIMIT


def test_load_config_ipv4_vip_limit(device_factory):
    device = _lan_device(device_factory)
    device["lan"]["vlans"][1]["ipv4_vip_pool"] = ["10.72.0.0/24"]
    config = mikro_lan.load_config(device, [device])
    assert len(_comments(config, "ip_VIP_2dmz_")) == mikro_lan.IP_VIP_LIMIT


def test_load_config_without_trunks_has_no_bridge_vlans(device_factory):
    device = _lan_device(device_factory)
    device["lan"]["trunk_ports"] = None
    config = mikro_lan.load_config(device, [device])
    assert not [item for item in config if item["resource"] == "/interface/bridge/vlan"]


def _vxlan_peer(device_factory, name, site_id, enable=True, role="edge"):
    return device_factory(name=name, site_id=site_id, role=role, enable_vxlan=enable,
                          subnetv4=f"10.{20 + site_id}.0.0/16")


def test_load_config_vxlan_mesh(device_factory):
    device = _lan_device(device_factory, enable_vxlan=True, enable_vxlan_to_vlan=True, api_version=716)
    remote = _vxlan_peer(device_factory, "dev2", 2)
    remote["lan"]["vlans"] = remote["lan"]["vlans"][:1]
    no_vxlan = _vxlan_peer(device_factory, "dev3", 3, enable=False)
    external = _vxlan_peer(device_factory, "ext", 9, role="external_edge")
    config = mikro_lan.load_config(device, [device, remote, no_vxlan, external])

    assert _by_comment(config, "ip_lo_10.0.0.1")["disabled"] == "false"
    assert _comments(config, "fw_in_vxlan_") == ["fw_in_vxlan_10.21.250.0/24", "fw_in_vxlan_10.22.250.0/24"]

    local = _by_comment(config, "vxlan_local_dev1_1safe_11")
    assert local["mtu"] == "1230" and local["vni"] == "11"
    vtep = _by_comment(config, "vtep_10.0.0.2__dev1_1safe_11")
    assert vtep["remote_ip"] == "10.0.0.2" and vtep["port"] == "4789"
    assert _by_comment(config, "int_br_11_dev1_1safe")["pvid"] == "1"

    _by_comment(config, "vxlan_remote_dev2_1safe_21")
    assert _by_comment(config, "vtep_10.0.0.2_dev2_1safe_21")["port"] == "4789"
    assert _by_comment(config, "321_vx_21_dev2_1safe")["vlan_id"] == "321"
    assert _by_comment(config, "int_br_dev2_1safe_21")["pvid"] == "321"
    assert _by_comment(config, "int_br_vlan_321")["tagged"] == "bridge-vlans,ether3"


def test_load_config_vxlan_without_vlan_export(device_factory):
    device = _lan_device(device_factory, enable_vxlan=True, enable_vxlan_to_vlan=False, api_version=720)
    device["lan"]["trunk_ports"] = []
    remote = _vxlan_peer(device_factory, "dev2", 2)
    config = mikro_lan.load_config(device, [device, remote])

    assert "port" not in _by_comment(config, "vtep_10.0.0.2__dev1_1safe_11")
    assert "port" not in _by_comment(config, "vtep_10.0.0.2_dev2_2dmz_22")
    assert not _comments(config, "322_vx_")


def test_load_config_vxlan_to_vlan_without_trunks(device_factory):
    device = _lan_device(device_factory, enable_vxlan=True, enable_vxlan_to_vlan=True)
    device["lan"]["trunk_ports"] = []
    remote = _vxlan_peer(device_factory, "dev2", 2)
    config = mikro_lan.load_config(device, [device, remote])
    _by_comment(config, "321_vx_21_dev2_1safe")
    assert not _comments(config, "int_br_vlan_321")


def test_load_config_external_role_keeps_loopback_disabled(device_factory):
    device = _lan_device(device_factory, role="external_edge", enable_vxlan=True)
    config = mikro_lan.load_config(device, [device])
    assert _by_comment(config, "ip_lo_10.0.0.1")["disabled"] == "true"
    assert not _comments(config, "vxlan")
