"""The web portal end to end: Flask routes over the lab inventory and an in-memory
RouterOS REST address-list. No request leaves the test process."""

import itertools
import os
import runpy

import pytest

import app as portal
import web_shared

pytestmark = pytest.mark.functional

APP_PATH = os.path.join(os.path.dirname(portal.__file__), "app.py")
CLIENT_IP = "10.23.4.20"  # inside lab-mikro3 (labsite3)


class FakeRest:
    """/ip/firewall/address-list of every router, keyed by router mgmt ip."""

    def __init__(self):
        self.lists = {}
        self.ids = itertools.count(1)
        self.calls = []

    def entries(self, device):
        return self.lists.setdefault(device["mgmt_int"], [])

    def get(self, device, resource):
        self.calls.append(("get", device["name"]))
        return [dict(entry) for entry in self.entries(device)]

    def put(self, device, resource, data):
        self.calls.append(("put", device["name"]))
        entry = dict(data, **{".id": f"*{next(self.ids)}"})
        self.entries(device).append(entry)
        return entry

    def patch(self, device, resource, data, entry_id):
        self.calls.append(("patch", device["name"]))
        entry = next(e for e in self.entries(device) if e[".id"] == entry_id)
        entry.update(data)
        return entry

    def delete(self, device, resource, entry_id):
        self.calls.append(("delete", device["name"]))
        self.lists[device["mgmt_int"]] = [e for e in self.entries(device) if e[".id"] != entry_id]
        return []


@pytest.fixture
def rest(monkeypatch):
    fake = FakeRest()
    monkeypatch.setattr(web_shared, "getItem", fake.get)
    monkeypatch.setattr(web_shared, "putItem", fake.put)
    monkeypatch.setattr(web_shared, "patchItem", fake.patch)
    monkeypatch.setattr(web_shared, "deleteItem", fake.delete)
    return fake


@pytest.fixture
def client():
    portal.app.config["TESTING"] = True
    return portal.app.test_client()


def _get(client, path, ip=CLIENT_IP):
    return client.get(path, environ_base={"REMOTE_ADDR": ip})


def _site(rest, name="lab-mikro3"):
    device = next(d for d in portal.my_inventory if d["name"] == name)
    return rest.entries(device)


# ---------------------------------------------------------------- pages

def test_index_shows_location_and_default_status(client, rest):
    response = _get(client, "/")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "labsite3" in page and CLIENT_IP in page
    assert "On ✅" in page and "Off 👀" in page


def test_pages_use_the_org_name_and_home_url(client, rest):
    page = _get(client, "/").get_data(as_text=True)
    assert "<title>lab Network Automation</title>" in page
    assert 'href="http://portal.example.int"' in page


def test_localhost_is_mapped_to_a_lab_client(client, rest):
    page = client.get("/").get_data(as_text=True)
    assert "labsite2" in page


def test_disable_and_enable_pihole(client, rest):
    page = _get(client, "/disable_pihole").get_data(as_text=True)
    assert "Off ❌" in page
    [entry] = _site(rest)
    assert entry["comment"] == f"auto_webapp_ACL4_PORTAL_DNS_{CLIENT_IP}"
    assert (entry["list"], entry["timeout"], entry["address"]) == ("ACL4_PORTAL_DNS", "1d", CLIENT_IP)

    # disabling again updates the same entry, forever extends the timeout
    _get(client, "/disable_pihole_forever")
    [entry] = _site(rest)
    assert entry["timeout"] == "30d"
    assert ("patch", "lab-mikro3") in rest.calls

    page = _get(client, "/enable_pihole").get_data(as_text=True)
    assert "On ✅" in page and _site(rest) == []


def test_enable_and_disable_vpn(client, rest):
    page = _get(client, "/enable_vpn").get_data(as_text=True)
    assert "On 🚀" in page
    [entry] = _site(rest)
    assert entry["list"] == "ACL4_PORTAL_VPN" and "timeout" not in entry

    _get(client, "/enable_vpn")
    assert len(_site(rest)) == 1 and ("patch", "lab-mikro3") in rest.calls

    page = _get(client, "/disable_vpn").get_data(as_text=True)
    assert "Off 👀" in page and _site(rest) == []


def test_enable_without_entry_and_disable_without_entry_do_nothing(client, rest):
    _get(client, "/enable_pihole")
    _get(client, "/disable_vpn")
    assert not [call for call in rest.calls if call[0] in ("put", "patch", "delete")]


def test_each_client_only_touches_its_own_site(client, rest):
    _get(client, "/disable_pihole", ip="10.21.1.50")
    assert len(_site(rest, "lab-mikro1")) == 1
    assert _site(rest, "lab-mikro3") == []


def test_unknown_ip_is_rejected():
    assert portal.getLocation(portal.my_inventory, "192.168.77.10") is False
    assert portal.getLocation(portal.my_inventory, "10.89.0.1") is False


# ---------------------------------------------------------------- router boot hook

def test_router_boot_update_launches_automation_for_known_router(client, monkeypatch):
    launched = []
    monkeypatch.setattr(portal.os, "system", launched.append)
    monkeypatch.setattr(portal, "main_auto_py_exec", "1-mikro-auto/mikro_main.py")
    response = _get(client, "/router_boot_update", ip="192.168.88.13")
    assert response.get_data(as_text=True) == "ok"
    assert launched == ["python3 1-mikro-auto/mikro_main.py lab-mikro3 &"]


def test_router_boot_update_localhost_maps_to_lab_router(client, monkeypatch):
    launched = []
    monkeypatch.setattr(portal.os, "system", launched.append)
    assert client.get("/router_boot_update").get_data(as_text=True) == "ok"
    assert launched and "lab-mikro1" in launched[0]


@pytest.mark.parametrize("ip", ["192.168.88.99", "10.21.100.7", "192.168.77.1"])
def test_router_boot_update_unknown_router(client, monkeypatch, ip):
    launched = []
    monkeypatch.setattr(portal.os, "system", launched.append)
    assert _get(client, "/router_boot_update", ip=ip).get_data(as_text=True) == "device_not_found"
    assert launched == []


def test_router_boot_check_allows_managed_subnet(monkeypatch):
    inventory = [{"name": "prod1", "mgmt_int": "10.21.100.7"}]
    assert portal.router_bootCheck(inventory, "10.21.100.7") == inventory[0]


# ---------------------------------------------------------------- status texts

def test_status_texts():
    assert portal.piholeStatusSTR({"x": 1}) == "Off ❌"
    assert portal.piholeStatusSTR(False) == "On ✅"
    assert portal.vpnStatusSTR({"x": 1}) == "On 🚀"
    assert portal.vpnStatusSTR(False) == "Off 👀"


def test_debug_mode_starts_development_server(monkeypatch):
    started = []
    monkeypatch.setenv("DEBUGMODE", "1")
    monkeypatch.setattr("flask.Flask.run", lambda self, host, port: started.append((host, port)))
    runpy.run_path(APP_PATH)
    assert started == [("0.0.0.0", 8080)]


def test_actions_from_localhost_use_the_lab_test_client(client, rest):
    for path in ["/disable_pihole", "/enable_vpn"]:
        client.get(path)
    entries = _site(rest, "lab-mikro2")
    assert {entry["address"] for entry in entries} == {"10.22.1.2"}
    for path in ["/enable_pihole", "/disable_vpn"]:
        client.get(path)
    assert _site(rest, "lab-mikro2") == []
