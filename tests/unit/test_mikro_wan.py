import json

import pytest
import yaml

import mikro_shared
import mikro_wan


def _node(device_factory, name, role, wan_order, site_id, **extra):
    device = device_factory(name=name, role=role, wan_order=wan_order, site_id=site_id,
                            location=f"loc_{name}", external_endpoint=f"{name}.example.com",
                            subnetv4=f"10.{80 + site_id}.0.0/16",
                            subnetv6=f"2001:db8:10:0:10:{80 + site_id}:0:0/96",
                            subnetv6slaac="2001:db8:10:8800::/53",
                            as_=None, **extra)
    device.pop("as_")
    device["as"] = str(65100 + site_id)
    mikro_shared.prepare_sdn(device)
    return device


def _external(device_factory, name, wan_order, site_id, **extra):
    device = _node(device_factory, name, "external_edge", wan_order, site_id,
                   allow_out_prefix_v4="10.91.222.200/32",
                   allow_out_prefix_v6="2001:db8:10:0:10:91:0:0/96", **extra)
    device.pop("api_version")
    return device


def _by_comment(config, comment):
    matches = [item for item in config if item.get("comment") == comment]
    assert matches, f"{comment} not generated"
    return matches[0]


def _connect(device1, device2, secrets=None, role="main"):
    for device in (device1, device2):
        mikro_wan.d_config.setdefault(device["name"], [])
        if device["role"] == "external_edge":
            mikro_wan.externalconf.setdefault(device["name"], {})
    return mikro_wan.create_connection(device1, device2, secrets, role)


# ---------------------------------------------------------------- wan_pairs / conn_slot

def test_wan_pairs_core_mesh_then_edges_ordered_by_wan_order(device_factory):
    core_b = _node(device_factory, "core_b", "core", 0, 1)
    core_a = _node(device_factory, "core_a", "core", 1, 2)
    edge = _node(device_factory, "edge", "edge", 2, 3)

    pairs = mikro_wan.wan_pairs([core_a, core_b], [edge])

    assert [(d1["name"], d2["name"]) for d1, d2 in pairs] == [
        ("core_b", "core_a"), ("edge", "core_b"), ("edge", "core_a")]


def test_conn_slot_skips_own_position(device_factory):
    device = {"name": "a", "wan_order": 3}
    assert mikro_wan.conn_slot(device, {"name": "b", "wan_order": 1}) == 1
    assert mikro_wan.conn_slot(device, {"name": "c", "wan_order": 5}) == 4


def test_conn_slot_out_of_range_stops(monkeypatch):
    stops = []
    monkeypatch.setattr(mikro_shared, "errorStop", lambda: stops.append(True))
    assert mikro_wan.conn_slot({"name": "a", "wan_order": 0}, {"name": "b", "wan_order": 65}) == 64
    assert stops == [True]


# ---------------------------------------------------------------- create_connection core <-> core

def test_create_connection_core_core(device_factory):
    core1 = _node(device_factory, "core1", "core", 0, 1, core_internet_transit=True,
                  core_priority=True, external_ddns=True, mqtt_netwatch_monitor=True,
                  ipv6_advertise_static=True)
    core2 = _node(device_factory, "core2", "core", 1, 2, core_internet_transit=True,
                  core_priority=False, external_ddns=True, mqtt_netwatch_monitor=False,
                  ipv6_advertise_static=False, api_version=719)

    secrets = _connect(core1, core2)

    candidate = "core1_main__core2_main"
    assert set(secrets[candidate]) == {"core1_main_private", "core1_main_public", "core2_main_private",
                                       "core2_main_public", "preshared"}
    assert core1["connections"] == [candidate] and core2["connections"] == [candidate]
    assert core1["conn_number"] == 0 and core2["conn_number"] == 0

    c1 = mikro_wan.d_config["core1"]
    c2 = mikro_wan.d_config["core2"]

    wg1 = _by_comment(c1, "int_w_core1_main_to_core2_main")
    assert wg1["listen_port"] == "51820"
    assert wg1["private_key"] == secrets[candidate]["core1_main_private"]
    peer1 = _by_comment(c1, "int_wg_peer_core1_main_to_core2_main")
    assert peer1["endpoint_address"] == "core2.example.com"
    assert peer1["public_key"] == secrets[candidate]["core2_main_public"]
    peer2 = _by_comment(c2, "int_wg_peer_core2_main_to_core1_main")
    assert peer2["endpoint_address"] == "core1.example.com"
    assert "responder" not in peer2

    # transit /30 taken from core1 (device1) for both ends
    assert _by_comment(c1, "ip_wg_10.81.250.1_30")["address"] == "10.81.250.1/30"
    assert _by_comment(c2, "ip_wg_10.81.250.2_30")["address"] == "10.81.250.2/30"
    assert core1["internet_vpn_ip"] == "10.81.250.2" and core2["internet_vpn_ip"] == "10.81.250.1"
    assert core1["core_transits"] == [{"transit_device": "core2", "ipv4": "10.81.250.2"}]
    assert core2["core_transits"] == [{"transit_device": "core1", "ipv4": "10.81.250.1"}]
    assert core1["peer_from_core1_to_core2"] == "10.81.250.2"
    assert core2["self_from_core2_to_core1"] == "10.81.250.2"

    # firewall in both directions
    for comment in ["fw_v4_forward_wgmain_in_core2_main_to_core1_main", "fw_v6_forward_wgmain_in_core2_main_to_core1_main",
                    "fw_in_bgp_core2_main_to_core1_main", "fw_in_bfdv6_core2_main_to_core1_main",
                    "list_item_int_w_core2_main_to_core1_main"]:
        _by_comment(c2, comment)
    for comment in ["fw_v4_forward_wgmain_in_core1_main_to_core2_main", "fw_in_wireguard_core1_main_to_core2_main",
                    "list_item_int_w_core1_main_to_core2_main", "fw_in_bgpv6_core1_main_to_core2_main"]:
        _by_comment(c1, comment)

    # DDNS scripts on both ends, port random only for edges
    _by_comment(c1, "script_DDNS_wg_peer_core1_main_to_core2_main")
    _by_comment(c2, "script_DDNS_wg_peer_core2_main_to_core1_main")
    assert not [i for i in c1 if "PORT_RANDOM" in i.get("comment", "")]

    # netwatch with mqtt only where enabled
    assert "mqtt" in _by_comment(c1, "netwatch_wg_core1_main_to_core2_main")["test_script"]
    assert _by_comment(c2, "netwatch_wg_core2_main_to_core1_main")["test_script"] == "# no test configure"

    # bgp
    bgp1 = [i for i in c1 if i["comment"] == f"bgp_v4_{candidate}"][0]
    bgp2 = [i for i in c2 if i["comment"] == f"bgp_v4_{candidate}"][0]
    assert bgp1["instance"] == "bgp_instance_main_core1" and bgp1["input.filter"] == "filter_v4_any"
    assert bgp1["output.filter_chain"] == "filter_v4_any" and bgp1["use-bfd"] == "true"
    assert bgp2["router-id"] == core2["mgmt_int"] and bgp2["input.filter"] == "filter_v4_any_priority"
    bgp6_1 = [i for i in c1 if i["comment"] == f"bgp_v6_{candidate}"][0]
    bgp6_2 = [i for i in c2 if i["comment"] == f"bgp_v6_{candidate}"][0]
    assert bgp6_1["output.redistribute"] == "connected,static" and bgp6_1["afi"] == "ipv6"
    assert bgp6_1["output.filter_chain"] == "filter_v6_any"
    assert bgp6_2["output.redistribute"] == "connected" and bgp6_2["afi"] == "ipv6"
    assert bgp6_2["input.filter"] == "filter_v6_any_priority"


def test_create_connection_is_idempotent_and_reuses_secrets(device_factory, fake_wg_keys):
    core1 = _node(device_factory, "core1", "core", 0, 1)
    core2 = _node(device_factory, "core2", "core", 1, 2)
    secrets = _connect(core1, core2, {})
    generated = len(mikro_wan.d_config["core1"])

    again = _connect(core1, core2, secrets)
    assert again is secrets
    assert len(mikro_wan.d_config["core1"]) == generated

    core3 = _node(device_factory, "core3", "core", 0, 1)
    core4 = _node(device_factory, "core4", "core", 1, 2)
    known = {"core3_main__core4_main": {"core3_main_private": "K3", "core3_main_public": "P3",
                                        "core4_main_private": "K4", "core4_main_public": "P4",
                                        "preshared": "PSK"}}
    _connect(core3, core4, known)
    assert _by_comment(mikro_wan.d_config["core3"], "int_w_core3_main_to_core4_main")["private_key"] == "K3"


def test_create_connection_core_core_without_priority_or_transit(device_factory):
    core1 = _node(device_factory, "core1", "core", 0, 1, api_version=710, ipv6_advertise_static=False)
    core2 = _node(device_factory, "core2", "core", 1, 2, use_bfd=False, ipv6_advertise_static=True)
    _connect(core1, core2)
    c1, c2 = mikro_wan.d_config["core1"], mikro_wan.d_config["core2"]
    bgp1 = _by_comment(c1, "bgp_v4_core1_main__core2_main")
    bgp2 = _by_comment(c2, "bgp_v4_core1_main__core2_main")
    assert bgp1["router-id"] == core1["mgmt_int"] and bgp1["use-bfd"] == "false"
    assert bgp2["input.filter"] == "filter_v4_any"
    bgp6_1 = _by_comment(c1, "bgp_v6_core1_main__core2_main")
    bgp6_2 = _by_comment(c2, "bgp_v6_core1_main__core2_main")
    assert bgp6_1["address_families"] == "ipv6" and bgp6_1["router-id"] == core1["mgmt_int"]
    assert bgp6_2["input.filter"] == "filter_v6_any" and bgp6_2["use-bfd"] == "false"
    assert bgp6_1["output.redistribute"] == "connected"
    assert bgp6_2["output.redistribute"] == "connected,static"
    assert "internet_vpn_ip" not in core1 and "internet_vpn_ip" not in core2
    assert not [i for i in c1 if i["comment"].startswith("script_DDNS")]


# ---------------------------------------------------------------- create_connection edge -> core

@pytest.mark.parametrize("site_id, start, end", [(5, 15100, 15200), (50, 15200, 15300), (150, 11800, 11900)])
def test_create_connection_edge_core_port_random_ranges(device_factory, site_id, start, end):
    edge = _node(device_factory, "edge", "edge", 2, 3)
    core = _node(device_factory, "core", "core", 0, site_id)
    _connect(edge, core)
    script = _by_comment(mikro_wan.d_config["edge"], "script_PORT_RANDOM_wg_peer_edge_main_to_core_main")
    assert f"from={start} to={end}" in script["on-event"]


@pytest.mark.parametrize("api_version, key", [(717, "responder"), (716, "is_responder")])
def test_create_connection_edge_core(device_factory, api_version, key):
    edge = _node(device_factory, "edge", "edge", 2, 3, mqtt_netwatch_monitor=False)
    core = _node(device_factory, "core", "core", 0, 1, core_internet_transit=True, core_priority=True,
                 external_ddns=True, mqtt_netwatch_monitor=True, api_version=api_version)
    _connect(edge, core)

    e, c = mikro_wan.d_config["edge"], mikro_wan.d_config["core"]
    candidate = "core_main__edge_main"
    assert edge["conn_number"] == 0 and core["conn_number"] == 1
    assert _by_comment(e, "int_w_edge_main_to_core_main")["listen_port"] == "51820"
    assert _by_comment(c, "int_w_core_main_to_edge_main")["listen_port"] == "51821"
    assert _by_comment(c, "int_wg_peer_core_main_to_edge_main")[key] == "true"
    assert "endpoint_address" not in _by_comment(c, "int_wg_peer_core_main_to_edge_main")
    assert edge["internet_vpn_ip"] == "10.83.250.2"
    assert edge["core_transits"] == [{"transit_device": "core", "ipv4": "10.83.250.2"}]
    assert core["core_transits"] == []
    _by_comment(e, "script_DDNS_wg_peer_edge_main_to_core_main")
    assert not [i for i in c if i["comment"].startswith("script_DDNS")]

    bgp_e = _by_comment(e, f"bgp_v4_{candidate}")
    bgp_c = _by_comment(c, f"bgp_v4_{candidate}")
    assert bgp_e["input.filter"] == "filter_v4_any_priority" and bgp_e["output.filter_chain"] == "filter_v4_loc_edge"
    assert bgp_c["input.filter"] == "filter_v4_loc_edge"
    bgp6_e = _by_comment(e, f"bgp_v6_{candidate}")
    bgp6_c = _by_comment(c, f"bgp_v6_{candidate}")
    assert bgp6_e["output.filter_chain"] == "filter_v6_loc_edge" and bgp6_e["input.filter"] == "filter_v6_any_priority"
    assert bgp6_c["input.filter"] == "filter_v6_loc_edge"
    assert ("instance" in bgp6_c) == (api_version >= 720)


def test_create_connection_backbone_untrusted_uses_external_lists(device_factory):
    edge = _node(device_factory, "edge", "edge", 1, 3, backbone_untrusted=True)
    core = _node(device_factory, "core", "core", 0, 1, backbone_untrusted=True)
    _connect(edge, core)
    e, c = mikro_wan.d_config["edge"], mikro_wan.d_config["core"]
    assert _by_comment(e, "list_external_item_int_w_edge_main_to_core_main")["list"] == "list_external_wireguard_main"
    assert _by_comment(c, "list_external_item_int_w_core_main_to_edge_main")["list"] == "list_external_wireguard_main"
    assert not [i for i in e + c if i["comment"].startswith("fw_v4_forward_wgmain")]


# ---------------------------------------------------------------- create_connection external_edge -> core

def test_create_connection_external_edge_core(device_factory):
    external = _external(device_factory, "ext", 2, 7, external_wg_main_port=61200)
    core = _node(device_factory, "core", "core", 0, 1, backbone_untrusted=True)
    _connect(external, core)

    candidate = "core_main__ext_main"
    # only the netwatch rule lands in the external device config, it is never pushed
    assert [i["resource"] for i in mikro_wan.d_config["ext"]] == ["/tool/netwatch"]
    ext_conf = mikro_wan.externalconf["ext"][candidate]
    assert set(ext_conf) == {"connection", "wireguard_interface", "wireguard_peer", "ip_address",
                             "ipv6_address", "ipv4_bgp_config", "ipv6_bgp_config"}
    assert ext_conf["wireguard_peer"]["endpoint_port"] == "61200"
    assert ext_conf["ipv4_bgp_config"]["router-id"] == external["mgmt_int"]
    assert ext_conf["ipv6_bgp_config"]["address_families"] == "ipv6"

    c = mikro_wan.d_config["core"]
    assert _by_comment(c, "int_w_core_main_to_ext_main")["listen_port"] == "61200"
    assert _by_comment(c, "fw_in_wireguard_core_main_to_ext_main")["dst_port"] == "61200"
    assert _by_comment(c, "fwv6_in_wireguard_core_main_to_ext_main")["dst_port"] == "61200"
    assert _by_comment(c, "filter_external_v4_loc_ext")["rule"].startswith("if (dst in 10.91.222.200/32")
    _by_comment(c, "filter_external_v6_loc_ext")
    assert _by_comment(c, f"bgp_v4_{candidate}")["input.filter"] == "filter_external_v4_loc_ext"
    assert _by_comment(c, f"bgp_v6_{candidate}")["input.filter"] == "filter_external_v6_loc_ext"


def test_create_connection_core_to_external_edge_as_device2(device_factory):
    # device2 external: its bgp router-id branch and the skipped forward rules
    core = _node(device_factory, "core", "core", 0, 1)
    external = _external(device_factory, "ext", 1, 7)
    _connect(core, external)
    e = mikro_wan.d_config["ext"]
    assert _by_comment(e, "bgp_v4_core_main__ext_main")["router-id"] == external["mgmt_int"]
    assert _by_comment(e, "bgp_v6_core_main__ext_main")["address_families"] == "ipv6"
    assert not [i for i in e if i["comment"].startswith("fw_v4_forward_wgmain")]


def test_create_connection_external_without_fixed_port(device_factory):
    external = _external(device_factory, "ext", 2, 7)
    core = _node(device_factory, "core", "core", 0, 1)
    _connect(external, core)
    assert _by_comment(mikro_wan.d_config["core"], "int_w_core_main_to_ext_main")["listen_port"] == "51821"


# ---------------------------------------------------------------- loadWan

def test_load_wan_builds_mesh_and_persists_secrets(device_factory, secrets_dir, monkeypatch):
    (secrets_dir / "external").mkdir()
    (secrets_dir / "external_export").mkdir()
    (secrets_dir / "secrets.json").write_text("{}")

    inventory = [
        _node(device_factory, "core1", "core", 0, 1),
        _node(device_factory, "core2", "core", 1, 2, api_version=717),
        _node(device_factory, "edge1", "edge", 2, 3),
        _node(device_factory, "edge_old", "edge", 3, 4, api_version=717),
        _external(device_factory, "ext1", 4, 7, external_wg_main_port=61200),
        _node(device_factory, "off", "core", 5, 8, enabled=False),
    ]

    d_config = mikro_wan.loadWan(inventory)

    assert set(d_config) == {"core1", "core2", "edge1", "edge_old", "ext1"}
    assert _by_comment(d_config["core1"], "bgp_instance_main_core1")["as"] == "65101"
    assert not [i for i in d_config["core2"] if i["resource"] == "/routing/bgp/instance"]
    _by_comment(d_config["edge1"], "bgp_instance_main_edge1")
    assert not [i for i in d_config["edge_old"] if i["resource"] == "/routing/bgp/instance"]

    secrets = json.loads((secrets_dir / "secrets.json").read_text())
    assert len(secrets) == 1 + 2 + 2 + 2
    external = yaml.safe_load((secrets_dir / "external" / "external.yml").read_text())
    assert set(external["ext1"]) == {"core1_main__ext1_main", "core2_main__ext1_main"}
    assert json.loads((secrets_dir / "external" / "external.json").read_text()) == external
    assert (secrets_dir / "external_export" / "frr_ext1.conf").exists()


@pytest.mark.xfail(strict=True, raises=UnboundLocalError,
                   reason="BUG: site_id >= 255 leaves the port random range undefined")
def test_create_connection_edge_to_core_with_site_id_255(device_factory):
    edge = _node(device_factory, "edge", "edge", 2, 3)
    core = _node(device_factory, "core", "core", 0, 1)
    core["site_id"] = 255
    _connect(edge, core)
