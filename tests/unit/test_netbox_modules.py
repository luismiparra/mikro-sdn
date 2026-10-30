"""Branches of the netbox helpers not reached by the build_netbox flow."""

import logging

import pytest

import netbox_api
import netbox_external_api
import netbox_get
import netbox_inventory
import netbox_shared
from conftest import make_device
from fakes import FakeNetbox, FakeResponse, tag

RP = netbox_shared.netbox_tag
GLOBAL = netbox_shared.netbox_global_tag


@pytest.fixture
def nb():
    netbox_get.clear_cache()
    nb = FakeNetbox()
    rp = nb.extras.tags.add(name=RP, slug="msdn-test")
    nb.extras.tags.add(name=GLOBAL, slug="msdn-global")
    nb.owner_tag = tag(RP, id=rp.id)
    yield nb
    netbox_get.clear_cache()


#----------- netbox_get

@pytest.mark.parametrize("lookup, value", [
    (netbox_get.get_interface_id_from_name, "x"),
    (netbox_get.get_vlan_vid_from_name, "x"),
    (netbox_get.get_device_from_name, "x"),
    (netbox_get.get_device_role_id_from_slug, "x"),
    (netbox_get.get_device_type_id_from_slug, "x"),
    (netbox_get.get_region_id_from_name, "x"),
    (netbox_get.get_region_id_from_name, None),
    (netbox_get.get_role_id_from_name, "x"),
    (netbox_get.get_role_id_from_name, None),
    (netbox_get.get_asn_id_from_number, "65000"),
    (netbox_get.get_asn_id_from_number, None),
    (netbox_get.get_rir_id_from_slug, "x"),
    (netbox_get.get_site_id_from_slug, "x"),
    (netbox_get.get_site_groups_id_from_slug, "x"),
    (netbox_get.get_tag_by_slug, "x"),
])
def test_lookups_return_none_when_missing(nb, lookup, value):
    assert lookup(nb, value) is None


def test_lookups_find_existing_objects(nb):
    role = nb.dcim.device_roles.add(slug="core")
    asn = nb.ipam.asns.add(asn=65110)
    interface = nb.dcim.interfaces.add(name="dev1_wg1")

    assert netbox_get.get_role_id_from_name(nb, "Core") == role.id
    assert netbox_get.get_asn_id_from_number(nb, "65110") == asn.id
    assert netbox_get.get_interface_id_from_name(nb, "dev1_wg1") == interface.id


def test_invalidate_drops_records_and_indexes(nb):
    netbox_get.get_vlan_vid_from_name(nb, "v1")
    nb.ipam.vlans.add(name="v1")
    assert netbox_get.get_vlan_vid_from_name(nb, "v1") is None

    netbox_get.invalidate(nb, "ipam", "vlans")

    assert netbox_get.get_vlan_vid_from_name(nb, "v1") is not None


#----------- netbox_api helpers

def test_normalize_key_leaves_unparseable_values():
    assert netbox_api._normalize_key("prefix", "not-an-ip") == "not-an-ip"
    assert netbox_api._normalize_key("asn", None) is None
    assert netbox_api._normalize_key("name", "Dev1") == "Dev1"


def test_same_value_with_unsortable_lists():
    assert netbox_api._same_value([{"a": 1}, {"b": 2}], [{"a": 1}, {"b": 2}])
    assert not netbox_api._same_value([{"a": 1}], [{"a": 2}])
    assert netbox_api._same_value([2, 1], [1, 2])
    assert netbox_api._same_value(None, "")


def test_tag_slugs_accepts_dicts_and_records():
    class Record:
        tags = [{"slug": "a"}, type("T", (), {"slug": "b"})()]

    assert netbox_api._tag_slugs(Record()) == ["a", "b"]


def test_failed_updates_and_deletes_are_logged_per_item(nb, caplog):
    endpoint = nb.ipam.prefixes
    endpoint.add(prefix="10.70.1.0/24", description="old", tags=[nb.owner_tag])
    endpoint.add(prefix="10.70.2.0/24", tags=[nb.owner_tag])
    endpoint.fail_on.update(update=True, delete=True)

    result = netbox_api.sync_resources(
        nb, "ipam", "prefixes", [{"prefix": "10.70.1.0/24", "description": "new"}], "prefix", RP)

    assert result == {"created": 0, "updated": 0, "deleted": 0, "unchanged": 0}
    assert "Error updating" in caplog.text and "Error deleting" in caplog.text
    assert len(endpoint.records) == 2


def test_create_update_resources_never_deletes(nb):
    nb.ipam.prefixes.add(prefix="10.70.9.0/24", tags=[nb.owner_tag])

    result = netbox_api.create_update_resources(
        nb, "ipam", "prefixes", [{"prefix": "10.70.1.0/24"}], "prefix", RP)

    assert result["created"] == 1 and result["deleted"] == 0
    assert len(nb.ipam.prefixes.records) == 2


def test_remove_resources_not_in_list(nb, monkeypatch):
    keep = nb.ipam.prefixes.add(prefix="10.70.1.0/24", tags=[nb.owner_tag])
    nb.ipam.prefixes.add(prefix="10.70.2.0/24", tags=[nb.owner_tag])
    data = [{"prefix": "10.70.1.0/24"}]

    monkeypatch.setattr(netbox_shared, "dry_run", True)
    assert netbox_api.remove_resources_not_in_list(nb, "ipam", "prefixes", data, "prefix", RP) == 0
    monkeypatch.setattr(netbox_shared, "dry_run", False)
    assert netbox_api.remove_resources_not_in_list(nb, "ipam", "prefixes", data, "prefix", RP) == 1
    assert nb.ipam.prefixes.records == [keep]
    assert data == [{"prefix": "10.70.1.0/24"}]
    assert netbox_api.remove_resources_not_in_list(nb, "ipam", "prefixes", data, "prefix", RP) == 0


def test_sync_roles_unknown_role_gets_a_default_color(nb):
    netbox_api.sync_roles(nb, ["lab"])

    assert nb.dcim.device_roles.records[0].color == "9e9e9e"


def test_create_or_update_tag_creates_a_missing_tag(nb):
    created = netbox_api.create_or_update_tag(nb, "New Tag")

    assert created.slug == "new-tag"
    assert netbox_api.create_or_update_tag(nb, "New Tag").id == created.id


def test_static_objects_log_creation_errors(nb, caplog):
    caplog.set_level(logging.INFO)
    nb.ipam.rirs.fail_on["create"] = True
    nb.dcim.site_groups.fail_on["create"] = True

    netbox_api.create_private_rir(nb)
    netbox_api.create_site_groups(nb)

    assert "Error creating private RIR" in caplog.text
    assert "Error creating site group" in caplog.text


def test_wg_vpn_ipv6_prefix_when_the_last_vlan_has_ipv6(nb):
    device = make_device(**{"wg-vpn": [{"name": "vpn1", "subnet": 200, "number_client": 2}]})
    device["lan"]["vlans"] = [{"id": 1, "name": "1safe", "ipv6": True}]

    prefixes = {p["prefix"] for p in netbox_inventory.get_inventory_prefixes(nb, [device])}

    assert "2001:db8:10:0:10:21:c8:0/112" in prefixes


#----------- netbox_shared

def test_load_inventory_reads_only_yaml_files_in_order(tmp_path, monkeypatch):
    inventory = tmp_path / "inventory"
    inventory.mkdir()
    (inventory / "b.yml").write_text("edge:\n- name: b\n")
    (inventory / "a.yaml").write_text("core:\n- name: a\n- name: a2\n")
    (inventory / ".DS_Store").write_text("junk")
    monkeypatch.setattr(netbox_shared, "pathconfig", str(tmp_path))

    assert netbox_shared.load_inventory() == [
        {"name": "a", "role": "core"}, {"name": "a2", "role": "core"}, {"name": "b", "role": "edge"}]


def test_subnet_calculators():
    assert netbox_shared.calculate_ipv4_3octect("10.21.0.0/16", 7) == "10.21.7.0/24"
    assert netbox_shared.calculate_ipv6_subnet_7hextet("2001:db8:10:0:10:21:0:0/96", 255) == \
        "2001:0db8:0010:0000:0010:0021:ff:0000/112"
    with pytest.raises(ValueError):
        netbox_shared.calculate_ipv4_3octect("10.21.0.0/16", 256)
    with pytest.raises(ValueError):
        netbox_shared.calculate_ipv6_subnet_7hextet("2001:db8:99::/96", 65536)


def test_generate_ip_list():
    assert netbox_shared.generate_ip_list("10.0.0.0/24", 1, 2, 24) == ["10.0.0.2/24", "10.0.0.3/24"]
    with pytest.raises(ValueError):
        netbox_shared.generate_ip_list("10.0.0.0/30", 1, 5, 30)


#----------- netbox_external_api

DEVICE = {"name": "dev1", "mgmt_int": "192.168.88.11"}


def test_mikrotik_api_returns_json_on_200(monkeypatch):
    asked = {}

    def get(url, **kwargs):
        asked.update(url=url, **kwargs)
        return FakeResponse(200, {"serial-number": "SN1"})

    monkeypatch.setattr(netbox_external_api.requests, "get", get)

    assert netbox_external_api.getMikrotikApiItem(DEVICE, "/system/routerboard") == {"serial-number": "SN1"}
    assert asked["url"] == "https://192.168.88.11/rest/system/routerboard"
    assert asked["verify"] is False


def test_mikrotik_api_returns_false_on_error_status(monkeypatch):
    monkeypatch.setattr(netbox_external_api.requests, "get", lambda url, **kwargs: FakeResponse(401))

    assert netbox_external_api.getMikrotikApiItem(DEVICE, "/system/routerboard") is False


def test_mikrotik_api_returns_false_when_unreachable(monkeypatch, caplog):
    def get(url, **kwargs):
        raise ConnectionError("timeout")

    monkeypatch.setattr(netbox_external_api.requests, "get", get)

    assert netbox_external_api.getMikrotikApiItem(DEVICE, "/system/routerboard") is False
    assert "Error getting device --> dev1" in caplog.text
