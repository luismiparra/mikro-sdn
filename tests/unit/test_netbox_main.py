"""build_netbox end to end over FakeNetbox, plus the inventory/intended builders it uses."""

import importlib
import json
import logging
import runpy
import sys

import pytest

import netbox_api
import netbox_get
import netbox_intended
import netbox_inventory
import netbox_main
import netbox_shared
from conftest import make_device
from fakes import FakeNetbox


def lab_inventory():
    dev1 = make_device(
        name="dev1", role="core", location="site1", **{"as": "65110"},
        netbox={"device": {"device_model": "mikrotik-chr"},
                "organization": {"region": "LAB", "site_group": "site_lab"}},
        **{"wg-vpn": [{"name": "vpn1", "subnet": 200, "number_client": 2}]},
    )
    dev2 = make_device(
        name="dev2", role="edge", location="site2", enabled=False, mgmt_int="192.168.88.12",
        subnetv4="10.22.0.0/16", subnetv6="2001:db8:10:0:10:22:0:0/96", **{"as": "65120"},
        netbox={"device": {"device_model": "rb5009"},
                "organization": {"region": "LAB", "site_group": "site_prod"}},
    )
    dev2["lan"]["vlans"] = [{"id": 1, "name": "1safe", "ipv6": True}]
    ext1 = make_device(name="ext1", role="external_edge", location="ext", lan=None, **{"as": "64000"})
    return [dev1, dev2, ext1]


def proposed_dev1():
    return [
        {"resource": "/interface/vlan", "name": "mgmt-vlan", "comment": "management"},
        {"resource": "/interface/wireguard", "name": "wg1", "comment": "fabric"},
        {"resource": "/ip/address", "address": "10.21.1.1/24", "interface": "mgmt-vlan", "comment": "a"},
        {"resource": "/ipv6/address", "address": "2001:db8:10::1/64", "interface": "unknown", "comment": "b"},
        {"resource": "/ip/pool", "name": "pool-safe/24", "ranges": "10.21.1.100-10.21.1.200"},
        {"resource": "/system/identity", "name": "dev1"},
    ]


def serials(device, resource):
    if device["name"] == "dev2":
        return False
    return {"system-id": f"ID-{device['name']}"}


@pytest.fixture
def netbox(tmp_path, monkeypatch):
    netbox_get.clear_cache()
    proposed = tmp_path / "proposed"
    proposed.mkdir()
    (proposed / "dev1_global.json").write_text(json.dumps(proposed_dev1()))
    monkeypatch.setattr(netbox_intended, "path_secrets", str(tmp_path))
    monkeypatch.setattr(netbox_inventory.netbox_external_api, "getMikrotikApiItem", serials)

    nb = FakeNetbox()
    nb.dcim.device_types.add(slug="mikrotik-chr")
    nb.dcim.device_types.add(slug="rb5009")
    monkeypatch.setattr(netbox_main.pynetbox, "api", lambda *args, **kwargs: nb)
    nb.inventory = lab_inventory()
    monkeypatch.setattr(netbox_shared, "load_inventory", lambda: nb.inventory)
    yield nb
    netbox_get.clear_cache()


def writes(nb):
    calls = []
    for app in (nb.dcim, nb.ipam, nb.extras):
        for name, endpoint in app._endpoints.items():
            calls += [(name, op) for op, _ in endpoint.calls if op != "all"]
            endpoint.calls.clear()
    return calls


def by(endpoint, field):
    return {getattr(record, field): record for record in endpoint.records}


def test_build_netbox_creates_the_whole_inventory(netbox):
    netbox_main.build_netbox()

    assert set(by(netbox.extras.tags, "name")) == {netbox_shared.netbox_tag, netbox_shared.netbox_global_tag}
    assert set(by(netbox.ipam.rirs, "slug")) == {"private"}
    assert set(by(netbox.dcim.site_groups, "slug")) == {"site_prod", "site_lab"}
    assert set(by(netbox.dcim.regions, "slug")) == {"lab"}
    assert set(by(netbox.ipam.asns, "asn")) == {"65110", "65120"}
    assert set(by(netbox.dcim.device_roles, "slug")) == {"core", "edge", "external-edge"}
    assert set(by(netbox.ipam.vlans, "name")) == {"1safe", "2dmz"}

    sites = by(netbox.dcim.sites, "slug")
    assert sites["site1"].status == "active"
    assert sites["site2"].status == "staging"
    assert sites["site1"].region == by(netbox.dcim.regions, "slug")["lab"].id

    devices = by(netbox.dcim.devices, "name")
    assert {name: d.serial for name, d in devices.items()} == {"dev1": "ID-dev1", "dev2": "none", "ext1": "none"}
    assert devices["dev1"].site == sites["site1"].id
    assert devices["dev1"].device_type == by(netbox.dcim.device_types, "slug")["mikrotik-chr"].id

    interfaces = by(netbox.dcim.interfaces, "name")
    assert set(interfaces) == {"dev1_mgmt-vlan", "dev1_wg1"}
    assert interfaces["dev1_mgmt-vlan"].mgmt_only is True
    assert interfaces["dev1_wg1"].mgmt_only is False
    assert interfaces["dev1_wg1"].device == devices["dev1"].id

    addresses = by(netbox.ipam.ip_addresses, "address")
    assert addresses["10.21.1.1/24"].assigned_object_id == interfaces["dev1_mgmt-vlan"].id
    assert not hasattr(addresses["2001:db8:10::1/64"], "assigned_object_id")
    assert {"10.21.200.2/24", "10.21.200.3/24"} <= set(addresses)

    prefixes = by(netbox.ipam.prefixes, "prefix")
    assert {"10.21.0.0/16", "10.21.1.0/24", "10.21.2.0/24", "10.21.250.0/24", "10.21.200.0/24",
            "10.22.0.0/16", "10.22.1.0/24"} <= set(prefixes)
    assert prefixes["10.21.1.0/24"].vlan == by(netbox.ipam.vlans, "name")["1safe"].id

    assert set(by(netbox.ipam.ip_ranges, "start_address")) == {"10.21.1.100/24"}
    assert by(netbox.ipam.ip_ranges, "start_address")["10.21.1.100/24"].end_address == "10.21.1.200/24"


def test_second_run_without_changes_writes_nothing(netbox):
    netbox_main.build_netbox()
    writes(netbox)
    netbox_get.clear_cache()

    netbox_main.build_netbox()

    assert writes(netbox) == []


def test_run_after_inventory_change_updates_and_deletes_in_bulk(netbox):
    netbox_main.build_netbox()
    writes(netbox)
    netbox_get.clear_cache()
    netbox.inventory[0]["description"] = "renamed core"
    del netbox.inventory[1]

    netbox_main.build_netbox()

    devices = by(netbox.dcim.devices, "name")
    assert set(devices) == {"dev1", "ext1"}
    assert devices["dev1"].description == "renamed core"
    assert "10.22.0.0/16" not in by(netbox.ipam.prefixes, "prefix")
    done = writes(netbox)
    assert ("devices", "update") in done and ("devices", "delete") in done
    assert done.count(("devices", "delete")) == 1


def test_netbox_main_runs_as_a_script(netbox, monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.setattr(sys.modules["pynetbox"], "api", lambda *args, **kwargs: netbox)

    runpy.run_path(netbox_main.__file__, run_name="__main__")

    assert "NETBOX -> ------------------------DONE" in caplog.text
    assert by(netbox.dcim.devices, "name")


def test_build_netbox_reports_every_sync(netbox, monkeypatch):
    reports = []
    monkeypatch.setattr(netbox_main.mikro_log, "report", lambda *args: reports.append(args))
    netbox_main.build_netbox()
    netbox_main.build_netbox()

    title, headers, rows = reports[-1]
    assert title == "NETBOX -> Sync result"
    assert headers[0] == "Resource"
    assert [row[0] for row in rows][-4:] == ["dcim.interfaces", "ipam.prefixes", "ipam.ip_addresses", "ipam.ip_ranges"]
    #The second run starts a new table and finds everything in place
    assert len(rows) == len(reports[0][2])
    assert all(row[1:4] == ["0", "0", "0"] for row in rows)


def test_sync_report_cells(monkeypatch):
    reports = []
    monkeypatch.setattr(netbox_main.mikro_log, "report", lambda *args: reports.append(args))
    monkeypatch.setattr(netbox_api, "sync_results", [
        ("dcim.devices", {"created": 2, "updated": 1, "deleted": 0, "unchanged": 5}, (2, 3, 0), False),
        ("ipam.prefixes", {"created": 0, "updated": 0, "deleted": 0, "unchanged": 4}, (1, 2, 3), True),
    ])
    netbox_main.sync_report()
    assert reports[0][2] == [["dcim.devices", "2", "❌ 1/3", "0", 5],
                             ["ipam.prefixes", "🧪 1", "🧪 2", "🧪 3", 4]]


def test_netbox_main_debug_mode(monkeypatch):
    monkeypatch.setenv("DEBUGMODE", "1")
    try:
        assert importlib.reload(netbox_main).prod is False
    finally:
        monkeypatch.setenv("DEBUGMODE", "")
        importlib.reload(netbox_main)


#----------- inventory builders

def test_get_inventory_regions_skips_devices_without_netbox_data():
    inventory = [{"name": "a"}, {"netbox": {}}, {"netbox": {"organization": {}}},
                 {"netbox": {"organization": {"region": "R1"}}}, {"netbox": {"organization": {"region": "R1"}}}]

    assert netbox_inventory.get_inventory_regions(None, inventory) == ["R1"]


def test_get_inventory_vlans_and_roles_are_unique():
    inventory = lab_inventory()

    assert [v["name"] for v in netbox_inventory.get_inventory_vlans(None, inventory)] == ["1safe", "2dmz"]
    assert netbox_inventory.get_inventory_device_roles(None, inventory + [{"name": "x"}]) == ["core", "edge", "external_edge"]


def test_get_inventory_vlans_skips_lan_without_vlans():
    assert netbox_inventory.get_inventory_vlans(None, [{"lan": {"vlans": None}}]) == []


def test_device_serial_reads_routerboard_for_physical_models(monkeypatch):
    asked = []
    monkeypatch.setattr(netbox_inventory.netbox_external_api, "getMikrotikApiItem",
                        lambda device, resource: asked.append(resource) or {"serial-number": "SN1"})

    assert netbox_inventory.get_device_serial({"role": "edge", "netbox": {"device": {"device_model": "rb5009"}}}) == "SN1"
    assert asked == ["/system/routerboard"]


def test_device_serial_is_none_when_the_chr_does_not_answer(monkeypatch):
    monkeypatch.setattr(netbox_inventory.netbox_external_api, "getMikrotikApiItem", lambda device, resource: False)

    assert netbox_inventory.get_device_serial({"role": "core", "netbox": {"device": {"device_model": "mikrotik-chr"}}}) == "none"


@pytest.fixture
def tagged_nb():
    netbox_get.clear_cache()
    nb = FakeNetbox()
    nb.extras.tags.add(name=netbox_shared.netbox_tag, slug="msdn-test")
    yield nb
    netbox_get.clear_cache()


def prefixes_of(nb, inventory):
    return {p["prefix"] for p in netbox_inventory.get_inventory_prefixes(nb, inventory)}


@pytest.mark.xfail(strict=True, reason="BUG: the client WG VPN ipv6 prefix depends on the ipv6 flag of the last LAN vlan "
                                       "(stale `vlan` variable) instead of being always generated")
def test_wg_vpn_ipv6_prefix_does_not_depend_on_the_last_vlan(tagged_nb):
    device = lab_inventory()[0]
    device["lan"]["vlans"] = [{"id": 1, "name": "1safe", "ipv6": False}]

    assert "2001:db8:10:0:10:21:c8:0/112" in prefixes_of(tagged_nb, [device])


@pytest.mark.xfail(strict=True, reason="BUG: a device without LAN vlans `continue`s before the WG fabric and WG VPN "
                                       "prefixes, so they are never generated")
def test_wg_vpn_prefixes_are_generated_without_lan_vlans(tagged_nb):
    device = lab_inventory()[0]
    device["lan"]["vlans"] = []

    assert "10.21.200.0/24" in prefixes_of(tagged_nb, [device])


@pytest.mark.xfail(strict=True, reason="BUG: for a vlan without ipv6 the ipv4 prefix of the vlan is appended twice "
                                       "(append outside the `if vlan.get('ipv6')`)")
def test_vlan_without_ipv6_adds_its_prefix_once(tagged_nb):
    device = lab_inventory()[0]
    device["lan"]["vlans"] = [{"id": 2, "name": "2dmz", "ipv6": False}]
    del device["wg-vpn"]

    prefixes = [p["prefix"] for p in netbox_inventory.get_inventory_prefixes(tagged_nb, [device])]

    assert prefixes.count("10.21.2.0/24") == 1


def test_device_without_wg_vpn_has_no_client_prefixes(tagged_nb):
    device = lab_inventory()[1]

    assert not any(p.startswith("10.22.200.") for p in prefixes_of(tagged_nb, [device]))


def test_intended_builders_skip_devices_without_proposed_config(tmp_path, monkeypatch, tagged_nb):
    monkeypatch.setattr(netbox_intended, "path_secrets", str(tmp_path))
    inventory = lab_inventory()

    assert netbox_intended.get_intended_interfaces(tagged_nb, inventory) == []
    assert netbox_intended.get_intended_ip_addresses(tagged_nb, inventory) == []
    assert netbox_intended.get_intended_ip_ranges(tagged_nb, inventory) == []


def test_intended_ip_addresses_without_wg_vpn(tmp_path, monkeypatch, tagged_nb):
    (tmp_path / "proposed").mkdir()
    (tmp_path / "proposed" / "dev2_global.json").write_text(json.dumps(
        [{"resource": "/ip/address", "address": "10.22.1.1/24", "interface": "bridge", "comment": "c"}]))
    monkeypatch.setattr(netbox_intended, "path_secrets", str(tmp_path))

    addresses = netbox_intended.get_intended_ip_addresses(tagged_nb, [lab_inventory()[1]])

    assert [a["address"] for a in addresses] == ["10.22.1.1/24"]
    assert addresses[0]["dns_name"] == "bridge-dev2.example.int."
