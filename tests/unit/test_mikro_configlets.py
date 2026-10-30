"""Configlets that turn inventory data into lists of RouterOS items."""

import ipaddress

import pytest
import yaml

import mikro_autoupdate
import mikro_internet
import mikro_netwatch
import mikro_radius_server
import mikro_wifi
from conftest import wifi_profile


def _comments(config):
    return [item.get("comment") for item in config]


def _by_comment(config, comment):
    return next(item for item in config if item.get("comment") == comment)


# ---------------------------------------------------------------- autoupdate

def test_autoupdate_schedulers():
    config = mikro_autoupdate.load_config({"name": "dev1"})
    assert _comments(config) == ["script_autoupdate", "script_boot_get_config", "script_clean_usermanagersessions",
                                 "script_enable_all_wireguard_interfaces", "script_auto_reboot_if_mgmt_lost"]
    assert all(item["resource"] == "/system/scheduler" and item["use_set"] is False for item in config)
    assert _by_comment(config, "script_autoupdate")["disabled"] == "true"
    assert "/system reboot" in _by_comment(config, "script_auto_reboot_if_mgmt_lost")["on-event"]
    assert "url=http://192.0.2.200/router_boot_update" in _by_comment(config, "script_boot_get_config")["on-event"]


def test_autoupdate_reboot_script_pings_every_mgmt_check_host(monkeypatch):
    monkeypatch.setattr(mikro_autoupdate, "mgmt_check_hosts", ["192.0.2.1", "192.0.2.2", "192.0.2.3", "192.0.2.4"])
    script = _by_comment(mikro_autoupdate.load_config({"name": "dev1"}), "script_auto_reboot_if_mgmt_lost")["on-event"]
    assert 'local host4 "192.0.2.4"' in script and "[/ping $host4 count=$pingCount]" in script
    assert script.endswith("/system reboot}\r")


def test_autoupdate_without_boot_url_and_check_hosts_skips_their_schedulers(monkeypatch):
    # Unset, the router never calls an unknown url on boot nor reboots because hosts it can not reach
    monkeypatch.setattr(mikro_autoupdate, "boot_update_url", None)
    monkeypatch.setattr(mikro_autoupdate, "mgmt_check_hosts", [])
    config = mikro_autoupdate.load_config({"name": "dev1"})
    assert _comments(config) == ["script_autoupdate", "script_clean_usermanagersessions",
                                 "script_enable_all_wireguard_interfaces"]


# ---------------------------------------------------------------- internet

TRANSITS = [{"transit_device": "core2", "ipv4": "10.71.250.2"}]


@pytest.mark.parametrize("role, transit", [("edge", False), ("core", False)])
def test_internet_via_vpn_for_edges_and_non_transit_cores(device_factory, role, transit):
    device = device_factory(role=role, core_internet_transit=transit, core_transits=TRANSITS,
                            internet_vpn_ip="10.71.250.1")
    config = mikro_internet.load_config(device)

    for comment in ["routing_table_internet_vpn", "routing_rule_internet_vpn", "routing_rule_main",
                    "vpnexit_mark_forward", "vpnexit_mark_out", "webapp_mark_internetvpn_forward"]:
        assert comment in _comments(config)
    assert _by_comment(config, "ip_route_internet_vpn")["gateway"] == "10.71.250.1"
    assert _by_comment(config, "ip_route_core_transit_core2")["gateway"] == "10.71.250.2"
    netwatch = _by_comment(config, "netwatch_core_transit_core2")
    assert 'core_transit_core2_mark' in netwatch["down_script"]


def test_internet_without_vpn_ip_has_no_default_route(device_factory):
    device = device_factory(role="edge", core_transits=[])
    config = mikro_internet.load_config(device)
    assert "ip_route_internet_vpn" not in _comments(config)
    assert "routing_table_internet_vpn" in _comments(config)


def test_internet_transit_core_only_gets_internet_list(device_factory):
    device = device_factory(role="core", core_internet_transit=True, core_transits=[])
    assert _comments(mikro_internet.load_config(device)) == ["list_internet", "list_internet_item_int_eth1"]


# ---------------------------------------------------------------- netwatch

def test_netwatch_with_mqtt(device_factory, monkeypatch):
    monkeypatch.setattr(mikro_netwatch, "mqtt_user", "mq_user")
    monkeypatch.setattr(mikro_netwatch, "mqtt_pass", "mq_pass")
    device = device_factory(mqtt_netwatch_monitor=True)
    config = mikro_netwatch.load_config(device)

    broker = config[0]
    assert broker["resource"] == "/iot/mqtt/brokers" and broker["use_set"] is True
    assert (broker["username"], broker["password"], broker["client_id"]) == ("mq_user", "mq_pass", "dev1")
    assert (broker["address"], broker["port"]) == ("192.0.2.14", "1883")
    assert _by_comment(config, "NAT_FALLBACK_DNS_1")["to_addresses"] == "7.7.7.7"
    assert _by_comment(config, "NAT_FALLBACK_DNS_2")["dst_address"] == "8.8.4.4"
    assert "internet1" in _by_comment(config, "netwatch_internet1")["test_script"]
    assert "internet2" in _by_comment(config, "netwatch_internet2")["test_script"]


@pytest.mark.parametrize("extra", [{"mqtt_netwatch_monitor": False}, {}])
def test_netwatch_without_mqtt(device_factory, extra):
    device = device_factory(**extra)
    config = mikro_netwatch.load_config(device)
    assert config[0]["comment"] == "netwatch_dns1"
    assert _by_comment(config, "netwatch_internet1")["test_script"] == "# no test configure"
    assert _by_comment(config, "netwatch_internet2")["test_script"] == "# no test configure"
    assert _by_comment(config, "netwatch_tcp_dns_2")["type"] == "tcp-conn"


def test_netwatch_mqtt_without_server_skips_the_broker(device_factory, monkeypatch, caplog):
    monkeypatch.setattr(mikro_netwatch, "MQTT_SERVER", None)
    config = mikro_netwatch.load_config(device_factory(mqtt_netwatch_monitor=True))
    assert "/iot/mqtt/brokers" not in [item["resource"] for item in config]
    assert "MQTT_SERVER not set" in caplog.text


# ---------------------------------------------------------------- radius server

def test_radius_server_users_and_routers(lab_secrets):
    config = mikro_radius_server.load_config({"name": "dev1", "domain": "example.int"})
    assert config[0] == {"resource": "/user-manager", "certificate": "radius.example.int.crt",
                         "enabled": "yes", "use_set": True}
    assert _by_comment(config, "radius_user_alice")["password"] == "alice_pass"


def test_radius_server_certificate_from_env(lab_secrets, monkeypatch):
    monkeypatch.setattr(mikro_radius_server, "radius_certificate", "my_radius.crt")
    config = mikro_radius_server.load_config({"name": "dev1", "domain": "example.int"})
    assert config[0]["certificate"] == "my_radius.crt"
    router = _by_comment(config, "radius_router_router1_10.71.1.1")
    assert router["shared_secret"] == "router1_secret" and router["address"] == "10.71.1.1"


# ---------------------------------------------------------------- wifi

def _wifi_device(device_factory, **extra):
    device = device_factory(**extra)
    device["gatewayv4_list"] = [ipaddress.ip_address("10.21.0.1"), ipaddress.ip_address("10.21.1.1")]
    return device


def test_wifi_local_radius(device_factory, lab_secrets, monkeypatch):
    monkeypatch.setattr(mikro_wifi, "radius_password", "radius_pw")
    device = _wifi_device(device_factory, radius_core=False)
    config = mikro_wifi.load_config(device, [device])

    assert _by_comment(config, "radius_local")["src_address"] == "127.0.0.1"
    vlan_radius = _by_comment(config, "radius_vlan")
    assert vlan_radius["src_address"] == "10.21.1.1" and vlan_radius["secret"] == "radius_pw"
    profile = _by_comment(config, "sec_profile_wpa")
    assert profile["supplicant_identity"] == "dev1"
    assert profile["resource"] == "/interface/wireless/security-profiles"
    assert _by_comment(config, "int_wifi_1")["resource"] == "/interface/wireless"
    assert _by_comment(config, "list_item_int_v_wlan1")["list"] == "list_inside"
    assert _by_comment(config, "int_br_1SAFE_access_wlan1")["pvid"] == "1"
    assert _by_comment(config, "wifi_mac_aa:bb:cc:dd:ee:01")["mac_address"] == "AA:BB:CC:DD:EE:01"


def test_wifi_core_radius_uses_transit_ips(device_factory, lab_secrets):
    device = _wifi_device(device_factory, name="edge1", role="edge", radius_core=True,
                          peer_from_edge1_to_core1="10.71.250.2", self_from_edge1_to_core1="10.71.250.1")
    inventory = [device, {"name": "core1", "role": "core"}]
    config = mikro_wifi.load_config(device, inventory)
    radius = _by_comment(config, "radius_core1")
    assert (radius["address"], radius["src_address"], radius["service"]) == ("10.71.250.2", "10.71.250.1", "wireless")


def test_wifi_without_radius_flag(device_factory, lab_secrets):
    device = _wifi_device(device_factory)
    device.pop("radius_core")
    config = mikro_wifi.load_config(device, [device])
    assert not [item for item in config if item["resource"] == "/radius"]


def test_wifi_profile_file_is_per_device(device_factory, lab_secrets):
    profile = wifi_profile()
    profile["int_wifi"][0]["name"] = "wlan_guest"
    (lab_secrets / "guest.yml").write_text(yaml.dump(profile))
    device = _wifi_device(device_factory, wifi_profile="guest")
    config = mikro_wifi.load_config(device, [device])
    assert "int_br_1SAFE_access_wlan_guest" in _comments(config)
