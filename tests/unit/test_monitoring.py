import os
import runpy

import pytest
import yaml

import mon_monitors
import mon_shared
from fakes import FakeResponse

DEVICE = {"name": "dev1", "role": "core", "mgmt_int": "10.0.0.1"}
MON_MAIN = os.path.join(os.path.dirname(mon_shared.__file__), "mon_main.py")


def _metrics():
    return {"vpn_infra_peers": 0, "vpn_infra_down_peers": 0, "ipv4_dhcp_leases": 0, "sites_online": 0,
            "site_offline": 0, "authusers": 0, "vpn_users_up": 0}


def _serve(monkeypatch, responses):
    """mon_shared.getItem answers by resource."""
    monkeypatch.setattr(mon_shared, "getItem", lambda device, resource: responses.get(resource, False))


# ---------------------------------------------------------------- mon_shared

@pytest.mark.parametrize("text, seconds", [("10s", 10), ("1m30s", 90), ("2h", 7200), ("1d", 86400),
                                           ("1w2d3h4m5s", 788645), ("42", 42), ("1.5m", 90)])
def test_convert_to_seconds(text, seconds):
    assert mon_shared.convert_to_seconds(text) == seconds


def test_load_inventory_sets_role_from_key(tmp_path):
    (tmp_path / "b.yml").write_text(yaml.dump({"edge": [{"name": "e1"}]}))
    (tmp_path / "a.yaml").write_text(yaml.dump({"core": [{"name": "c1"}, {"name": "c2"}]}))
    (tmp_path / "notes.txt").write_text("skip")
    inventory = mon_shared.load_inventory(str(tmp_path))
    assert [(d["name"], d["role"]) for d in inventory] == [("c1", "core"), ("c2", "core"), ("e1", "edge")]


def test_get_item(monkeypatch):
    seen = {}

    def get(url, auth, verify):
        seen.update(url=url, auth=auth, verify=verify)
        return FakeResponse(200, [{"id": 1}])

    monkeypatch.setattr(mon_shared.requests, "get", get)
    assert mon_shared.getItem(DEVICE, "/ip/address") == [{"id": 1}]
    assert seen["url"] == "https://10.0.0.1/rest/ip/address" and seen["verify"] is False


def test_get_item_errors(monkeypatch):
    monkeypatch.setattr(mon_shared.requests, "get", lambda *a, **k: FakeResponse(401))
    assert mon_shared.getItem(DEVICE, "/ip/address") is False

    def boom(*a, **k):
        raise ConnectionError("down")

    monkeypatch.setattr(mon_shared.requests, "get", boom)
    assert mon_shared.getItem(DEVICE, "/ip/address") is False


def test_post_item(monkeypatch):
    seen = {}

    def post(url, auth, data, headers, verify):
        seen.update(url=url, data=data, headers=headers)
        return FakeResponse(200, [{"seq": 0}])

    monkeypatch.setattr(mon_shared.requests, "post", post)
    assert mon_shared.postItem(DEVICE, "/ping", {"address": "1.1.1.1"}) == [{"seq": 0}]
    assert seen["data"] == '{"address": "1.1.1.1"}' and seen["headers"]["content-type"] == "application/json"


def test_post_item_errors(monkeypatch):
    monkeypatch.setattr(mon_shared.requests, "post", lambda *a, **k: FakeResponse(500, {"error": "x"}))
    assert mon_shared.postItem(DEVICE, "/ping", {}) is False

    def boom(*a, **k):
        raise TimeoutError("slow")

    monkeypatch.setattr(mon_shared.requests, "post", boom)
    assert mon_shared.postItem(DEVICE, "/ping", {}) is False


def test_send_to_influx(monkeypatch):
    written = []

    class WriteApi:
        def write(self, bucket, org, data):
            written.append((bucket, org, data))

    class Client:
        def __init__(self, url, token, org):
            self.args = (url, token, org)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def write_api(self, write_options):
            return WriteApi()

    monkeypatch.setattr(mon_shared, "InfluxDBClient", Client)
    mon_shared.sendToInflux(["m value=1"])
    mon_shared.sendToInflux([])
    assert written == [(mon_shared.influx_bucket, mon_shared.influx_org, ["m value=1"])]


# ---------------------------------------------------------------- monitors

def test_global_checks_counts_active_sessions(monkeypatch):
    _serve(monkeypatch, {"/user-manager/session": [{"active": "true"}, {"active": "false"}, {}]})
    metrics = _metrics()
    assert mon_monitors.mikro_global_checks(DEVICE, metrics) == []
    assert metrics["authusers"] == 1


def test_dhcp_status_counts_bound_leases(monkeypatch):
    _serve(monkeypatch, {"/ip/dhcp-server/lease": [{"status": "bound"}, {"status": "waiting"}, {}]})
    metrics = _metrics()
    assert mon_monitors.dhcp_status(DEVICE, metrics) == []
    assert metrics["ipv4_dhcp_leases"] == 1


def test_netwatch_status_lines(monkeypatch):
    common = {"comment": "c", "host": "1.1.1.1", "done-tests": "10", "failed-tests": "0"}
    _serve(monkeypatch, {"/tool/netwatch": [
        dict(common, type="simple"),
        dict(common, type="icmp", status="up", **{"loss-count": "0", "loss-percent": "0", "rtt-avg": "10ms",
                                                   "rtt-jitter": "1ms", "rtt-max": "12ms", "rtt-min": "9ms",
                                                   "rtt-stdev": "1ms"}),
        dict(common, type="icmp", status="down", **{"loss-count": "3", "loss-percent": "100"}),
        dict(common, type="tcp-conn", **{"tcp-connect-time": "5ms"}),
        dict(common, type="http-get"),
        {"comment": "no type"},
    ]})
    lines = mon_monitors.netwatch_status(DEVICE)
    assert len(lines) == 4
    assert lines[0].startswith("mikro_netwatch_simple,host=dev1")
    assert "rtt-avg=0.01" in lines[1]
    assert lines[2].endswith("loss-count=3,loss-percent=100")
    assert lines[3].endswith("tcp-connect-time=0.005")


def test_wireguard_peer_status(monkeypatch):
    _serve(monkeypatch, {"/interface/wireguard/peers": [
        {"interface": "int_w_a_main_to_b_main", "last-handshake": "30s"},
        {"interface": "int_w_a_main_to_c_main", "last-handshake": "1h"},
        {"interface": "int_w_a_main_to_d_main"},
        {"interface": "int_w_vpn_admin", "last-handshake": "10s"},
        {"interface": "int_w_vpn_user", "last-handshake": "2h"},
        {"interface": "int_w_vpn_user"},
        {"interface": "other"},
    ]})
    metrics = _metrics()
    lines = mon_monitors.wireguard_peer_status(DEVICE, metrics)
    assert metrics["vpn_infra_peers"] == 3 and metrics["vpn_infra_down_peers"] == 2
    assert metrics["vpn_users_up"] == 1
    assert "healthy=True,last-handshake=30.0" in lines[0]
    assert "healthy=False,last-handshake=3600.0" in lines[1]
    assert lines[2].endswith("healthy=False,last-handshake=-1")


def test_monitors_without_data_return_nothing(monkeypatch):
    _serve(monkeypatch, {})
    metrics = _metrics()
    assert mon_monitors.wireguard_peer_status(DEVICE, metrics) == []
    assert mon_monitors.netwatch_status(DEVICE) == []
    assert mon_monitors.dhcp_status(DEVICE, metrics) == []
    assert mon_monitors.mikro_global_checks(DEVICE, metrics) == []
    assert mon_monitors.wireguard_ping_bgp(DEVICE) is None
    assert mon_monitors.internet_ping(DEVICE) is None


def _ping_answers(monkeypatch, alive_for):
    """postItem /ping: a reply with time for destinations in alive_for, lost otherwise."""
    requests = []

    def post(device, resource, data):
        requests.append(data)
        last = {"packet-loss": "0", "time": "15ms"} if data["address"] in alive_for else {"packet-loss": "100"}
        return [{}] * (mon_monitors.ICMP_COUNT - 1) + [last]

    monkeypatch.setattr(mon_shared, "postItem", post)
    return requests


def test_wireguard_ping_bgp(monkeypatch):
    _serve(monkeypatch, {"/routing/bgp/connection": [{"remote.address": "10.0.0.2", "comment": "up"},
                                                     {"remote.address": "10.0.0.6", "comment": "down"}]})
    requests = _ping_answers(monkeypatch, {"10.0.0.2"})
    lines = mon_monitors.wireguard_ping_bgp(DEVICE)
    assert requests[0]["ttl"] == "1"
    assert "name=up healthy=True,response=0.015" in lines[0]
    assert "name=down healthy=False,packet_lost=100" in lines[1]


def test_internet_ping(monkeypatch):
    _serve(monkeypatch, {
        "/ip/address": [{"interface": "4guest", "address": "10.71.4.1/24", "comment": "x"},
                        {"interface": "4guest", "address": "10.71.4.2/24"},
                        {"interface": "1safe", "address": "10.71.1.1/24", "comment": "x"}],
        "/ipv6/address": [{"interface": "1safe", "address": "2001:db8::1/64", "comment": "x"},
                          {"interface": "wan", "address": "2001:db8:1::1/64", "comment": "x"}],
    })
    alive = {mon_monitors.INTERNET_HOSTS_IPV4[0], mon_monitors.INTERNET_HOSTS_IPV6[0]}
    requests = _ping_answers(monkeypatch, alive)

    lines = mon_monitors.internet_ping(DEVICE)

    assert len(lines) == 2 + 2 + 2
    assert sum("healthy=True" in line for line in lines) == 3
    assert [line.split(",")[0] for line in lines] == ["mikro_internet_ipv4_icmp"] * 2 + \
        ["mikro_internet_ipv6_icmp"] * 2 + ["mikro_vpninternet_ipv4_icmp"] * 2
    assert {r.get("src-address") for r in requests} == {None, "2001:db8::1", "10.71.4.1"}


def test_monitor_device_alive_sends_measurements(monkeypatch):
    monkeypatch.setattr(mon_monitors, "ping", lambda host, count: type("R", (), {"is_alive": True})())
    monkeypatch.setattr(mon_monitors, "wireguard_peer_status", lambda d, m: ["wg"])
    monkeypatch.setattr(mon_monitors, "netwatch_status", lambda d: ["nw"])
    monkeypatch.setattr(mon_monitors, "dhcp_status", lambda d, m: [])
    monkeypatch.setattr(mon_monitors, "mikro_global_checks", lambda d, m: [])
    sent = []
    monkeypatch.setattr(mon_shared, "sendToInflux", sent.append)
    metrics = _metrics()
    mon_monitors.monitorDevice(DEVICE, metrics)
    assert sent == [["wg", "nw"]] and metrics["sites_online"] == 1


def test_monitor_device_alive_without_measurements(monkeypatch):
    monkeypatch.setattr(mon_monitors, "ping", lambda host, count: type("R", (), {"is_alive": True})())
    _serve(monkeypatch, {})
    sent = []
    monkeypatch.setattr(mon_shared, "sendToInflux", sent.append)
    mon_monitors.monitorDevice(DEVICE, _metrics())
    assert sent == []


def test_monitor_device_offline(monkeypatch):
    monkeypatch.setattr(mon_monitors, "ping", lambda host, count: type("R", (), {"is_alive": False})())
    metrics = _metrics()
    mon_monitors.monitorDevice(DEVICE, metrics)
    assert metrics["site_offline"] == 1 and metrics["sites_online"] == 0


# ---------------------------------------------------------------- mon_main

@pytest.mark.parametrize("debug", ["", "1"])
def test_main_monitors_enabled_devices_and_sends_globals(monkeypatch, tmp_path, debug):
    (tmp_path / "inv.yml").write_text(yaml.dump({
        "core": [{"name": "c1", "enabled": True, "monitoring": True},
                 {"name": "c2", "enabled": False, "monitoring": True}],
        "edge": [{"name": "e1", "enabled": True, "monitoring": False}],
        "external_edge": [{"name": "x1", "enabled": True, "monitoring": True}],
    }))
    monkeypatch.setenv("INVENTORY", str(tmp_path))
    monkeypatch.setenv("DEBUGMODE", debug)
    monitored = []

    def monitor(device, metrics):
        monitored.append(device["name"])
        metrics["sites_online"] += 1

    monkeypatch.setattr(mon_monitors, "monitorDevice", monitor)
    sent = []
    monkeypatch.setattr(mon_shared, "sendToInflux", sent.append)

    runpy.run_path(MON_MAIN, run_name="__main__")

    assert monitored == ["c1"]
    assert len(sent) == 1 and sent[0][0].startswith("mikro_global vpn_infra_peers=0")
    assert "sites_online=1" in sent[0][0]
