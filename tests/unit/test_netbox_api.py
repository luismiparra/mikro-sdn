import pytest

import netbox_api
import netbox_get
import netbox_inventory
import netbox_shared
from fakes import FakeNetbox, tag

RP = netbox_shared.netbox_tag
GLOBAL = netbox_shared.netbox_global_tag


@pytest.fixture
def nb():
    netbox_get.clear_cache()
    nb = FakeNetbox()
    rp = nb.extras.tags.add(name=RP, slug="msdn-test")
    nb.extras.tags.add(name=GLOBAL, slug="msdn-global")
    nb.owner_tag = tag(RP, id=rp.id)
    nb.other_tag = tag("someone-else", id=99)
    yield nb
    netbox_get.clear_cache()


def prefix(value, description="d", tag_id=1):
    return {"prefix": value, "status": "active", "description": description, "tags": [tag_id]}


def test_sync_creates_everything_in_one_bulk_request(nb):
    desired = [prefix(f"10.70.{i}.0/24") for i in range(10)]

    result = netbox_api.sync_resources(nb, "ipam", "prefixes", desired, "prefix", RP)

    assert result["created"] == 10
    assert nb.ipam.prefixes.calls == [("all", None), ("create", 10)]


def test_sync_only_updates_changed_fields_and_skips_unchanged(nb):
    endpoint = nb.ipam.prefixes
    same = endpoint.add(prefix="10.70.1.0/24", status="active", description="d", tags=[nb.owner_tag])
    changed = endpoint.add(prefix="10.70.2.0/24", status="active", description="old", tags=[nb.owner_tag])

    result = netbox_api.sync_resources(
        nb, "ipam", "prefixes", [prefix("10.70.1.0/24"), prefix("10.70.2.0/24", "new")], "prefix", RP)

    assert result == {"created": 0, "updated": 1, "deleted": 0, "unchanged": 1}
    assert changed.updated_with == {"id": changed.id, "description": "new"}
    assert same.updated_with is None
    assert endpoint.calls == [("all", None), ("update", 1)]


def test_sync_deletes_only_tagged_objects_missing_from_the_list(nb):
    endpoint = nb.ipam.prefixes
    endpoint.add(prefix="10.70.1.0/24", tags=[nb.owner_tag])
    endpoint.add(prefix="10.70.2.0/24", tags=[nb.owner_tag])
    foreign = endpoint.add(prefix="10.70.3.0/24", tags=[nb.other_tag])

    result = netbox_api.sync_resources(nb, "ipam", "prefixes", [], "prefix", RP)

    assert result["deleted"] == 2
    assert endpoint.records == [foreign]
    assert endpoint.calls == [("all", None), ("delete", 2)]


def test_sync_does_not_update_objects_owned_by_another_tag(nb):
    foreign = nb.ipam.prefixes.add(prefix="10.70.1.0/24", description="x", tags=[nb.other_tag])

    netbox_api.sync_resources(nb, "ipam", "prefixes", [prefix("10.70.1.0/24")], "prefix", RP)

    assert foreign.updated_with is None
    assert nb.ipam.prefixes.created == []


def test_sync_matches_ip_keys_whatever_their_notation(nb):
    nb.ipam.ip_addresses.add(address="2001:db8:99:0:0:0:0:1/64", status="active", tags=[nb.owner_tag])

    result = netbox_api.sync_resources(
        nb, "ipam", "ip_addresses", [{"address": "2001:db8:99::1/64", "status": "active", "tags": [1]}], "address", RP)

    assert result == {"created": 0, "updated": 0, "deleted": 0, "unchanged": 1}


def test_sync_deduplicates_the_desired_list(nb):
    netbox_api.sync_resources(
        nb, "ipam", "prefixes", [prefix("10.70.1.0/24", "a"), prefix("10.70.1.0/24", "b")], "prefix", RP)

    assert [item["description"] for item in nb.ipam.prefixes.created] == ["b"]


def test_failed_bulk_chunk_is_retried_item_by_item(nb):
    nb.ipam.prefixes.fail_on["create"] = lambda item: item["prefix"] == "10.70.2.0/24"

    result = netbox_api.sync_resources(
        nb, "ipam", "prefixes", [prefix(f"10.70.{i}.0/24") for i in range(4)], "prefix", RP)

    assert result["created"] == 3
    assert sorted(item["prefix"] for item in nb.ipam.prefixes.created) == ["10.70.0.0/24", "10.70.1.0/24", "10.70.3.0/24"]


def test_large_lists_are_sent_in_chunks(nb, monkeypatch):
    monkeypatch.setattr(netbox_api, "BULK_CHUNK", 3)

    netbox_api.sync_resources(nb, "ipam", "prefixes", [prefix(f"10.70.{i}.0/24") for i in range(7)], "prefix", RP)

    assert nb.ipam.prefixes.calls[1:] == [("create", 3), ("create", 3), ("create", 1)]


def test_dry_run_does_not_write(nb, monkeypatch):
    monkeypatch.setattr(netbox_shared, "dry_run", True)
    nb.ipam.prefixes.add(prefix="10.79.0.0/24", tags=[nb.owner_tag])

    netbox_api.sync_resources(nb, "ipam", "prefixes", [prefix("10.70.1.0/24")], "prefix", RP)

    assert nb.ipam.prefixes.calls == [("all", None)]


def test_lookups_read_each_endpoint_once(nb):
    for i in range(5):
        nb.ipam.vlans.add(name=f"vlan{i}")

    ids = [netbox_get.get_vlan_vid_from_name(nb, f"vlan{i}") for i in range(5)] * 3

    assert None not in ids
    assert nb.ipam.vlans.calls == [("all", None)]


def test_cache_is_refreshed_after_a_sync_writes(nb):
    assert netbox_get.get_vlan_vid_from_name(nb, "1safe") is None

    netbox_api.sync_vlans(nb, [{"id": 1, "name": "1safe"}])

    assert netbox_get.get_vlan_vid_from_name(nb, "1safe") is not None


def test_device_serials_are_read_in_parallel(monkeypatch):
    seen = []
    monkeypatch.setattr(netbox_inventory.netbox_external_api, "getMikrotikApiItem",
                        lambda device, resource: seen.append(device["name"]) or {"serial-number": f"SN-{device['name']}"})
    inventory = [{"name": f"r{i}", "role": "core"} for i in range(5)] + [{"name": "ext", "role": "external_edge"}]

    devices = netbox_inventory.get_inventory_devices(None, inventory)

    assert [d["serial"] for d in devices] == [f"SN-r{i}" for i in range(5)] + ["none"]
    assert sorted(seen) == [f"r{i}" for i in range(5)]
