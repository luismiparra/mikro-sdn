"""End to end: lab config -> generated configuration -> push to in-memory routers.

Nothing here talks to a real device: login() hands out one FakeRouterOsApi per device.
"""

import json
import os

import pytest
import yaml

import mikro_docs
import mikro_main
import mikro_shared
import mikro_wan
from fakes import FakeRouterOsApi

pytestmark = pytest.mark.functional

MANAGED = ["lab-mikro1", "lab-mikro2", "lab-mikro3", "lab-mikro4", "lab-mikro5", "lab-mikro6"]


@pytest.fixture
def lab(lab_secrets, config_dir, monkeypatch):
    """Lab config with fresh secrets, generated once, and a fake router per device."""
    mikro_shared.create_files()
    mikro_main.generate_config()

    routers = {}

    def login(user, password, ip, device):
        return routers.setdefault(device["name"], FakeRouterOsApi())

    monkeypatch.setattr(mikro_shared, "login", login)
    return {"secrets": lab_secrets, "routers": routers}


def _new_process():
    """Each production run is a new process; mikro_wan and mikro_docs keep state in module globals."""
    mikro_wan.core_devices.clear()
    mikro_wan.edge_devices.clear()
    mikro_wan.external_devices.clear()
    mikro_wan.d_config.clear()
    mikro_wan.externalconf = {}
    mikro_docs.globalbind_str_a = ""
    mikro_docs.globalbind_str_ptr = ""
    mikro_docs.global_doc_md = ""
    mikro_docs.global_dry_run_md = "#CHANGES FILE MODE:\n"


def _proposed(secrets, name):
    folder = secrets / "proposed"
    return json.loads((folder / f"{name}_global.json").read_text()), json.loads((folder / f"{name}_fw.json").read_text())


def _inventory():
    return {device["name"]: device for device in mikro_shared.load_inventory()}


# ---------------------------------------------------------------- generation

def test_generation_writes_config_for_every_managed_device(lab, web_dir):
    secrets = lab["secrets"]
    for name in MANAGED:
        general, firewall = _proposed(secrets, name)
        assert general and firewall
        assert {item["resource"] for item in firewall} <= {"/ip/firewall/filter", "/ipv6/firewall/filter",
                                                            "/ip/firewall/nat", "/ip/firewall/mangle",
                                                            "/ipv6/firewall/mangle", "/ip/firewall/address-list",
                                                            "/ipv6/firewall/address-list"}
        assert not {"/ip/firewall/filter", "/ip/firewall/nat"} & {item["resource"] for item in general}
        comments = [item["comment"] for item in general + firewall if "comment" in item]
        assert len(comments) == len(set(comments)), f"duplicated comments in {name}"
        assert yaml.safe_load((secrets / "proposed" / f"{name}_global.yml").read_text()) == general
        assert (web_dir / f"{name}.html").exists()

    # external edges are not managed: no proposed config, wireguard/frr files instead
    assert not (secrets / "proposed" / "externalhost1_global.json").exists()
    exports = sorted(path.name for path in (secrets / "external_export").iterdir())
    assert "frr_externalhost1.conf" in exports and "frr_externalhost2.conf" in exports
    assert len([name for name in exports if name.startswith("wg_externalhost1_")]) == 3


def test_wan_mesh_is_consistent_on_both_ends(lab):
    secrets = lab["secrets"]
    keys = json.loads((secrets / "secrets.json").read_text())
    general = {name: _proposed(secrets, name)[0] for name in MANAGED}

    def find(name, comment):
        return next(item for item in general[name] if item.get("comment") == comment)

    # lab-mikro1 (wan_order 0) <-> lab-mikro4 (wan_order 3)
    candidate = "lab-mikro1_main__lab-mikro4_main"
    wg1 = find("lab-mikro1", "int_w_lab-mikro1_main_to_lab-mikro4_main")
    wg4 = find("lab-mikro4", "int_w_lab-mikro4_main_to_lab-mikro1_main")
    peer1 = find("lab-mikro1", "int_wg_peer_lab-mikro1_main_to_lab-mikro4_main")
    peer4 = find("lab-mikro4", "int_wg_peer_lab-mikro4_main_to_lab-mikro1_main")
    assert wg1["listen_port"] == "51822" and wg4["listen_port"] == "51820"
    assert peer1["endpoint_port"] == wg4["listen_port"] and peer4["endpoint_port"] == wg1["listen_port"]
    assert peer1["public_key"] == keys[candidate]["lab-mikro4_main_public"]
    assert peer4["public_key"] == keys[candidate]["lab-mikro1_main_public"]
    assert peer1["preshared_key"] == peer4["preshared_key"] == keys[candidate]["preshared"]

    bgp1 = find("lab-mikro1", f"bgp_v4_{candidate}")
    bgp4 = find("lab-mikro4", f"bgp_v4_{candidate}")
    ip1 = find("lab-mikro1", f"ip_wg_{bgp4['remote.address']}_30")["address"].split("/")[0]
    assert ip1 == bgp4["remote.address"]
    assert (bgp1["as"], bgp1["remote.as"]) == (bgp4["remote.as"], bgp4["as"])


def test_generation_is_stable_between_runs(lab):
    secrets = lab["secrets"]
    first = {name: _proposed(secrets, name) for name in MANAGED}
    _new_process()
    mikro_main.generate_config()
    second = {name: _proposed(secrets, name) for name in MANAGED}
    assert first == second
    assert (secrets / "old_proposed" / "lab-mikro1_global.json").exists()


@pytest.mark.xfail(strict=True, raises=KeyError,
                   reason="BUG: mikro_wan keeps devices and connections in module globals, a second "
                          "generate_config() in the same process skips every link and the external "
                          "files fail (latent: production runs one generation per process)")
def test_generation_twice_in_the_same_process(lab):
    mikro_main.generate_config()


# ---------------------------------------------------------------- push

def _push(device_name, mode="global", dry_run=False):
    device = _inventory()[device_name]
    mikro_main.clean_and_push(device, mode, dry_run, False)


def test_push_global_configures_the_router(lab):
    _push("lab-mikro1")
    router = lab["routers"]["lab-mikro1"]
    general, firewall = _proposed(lab["secrets"], "lab-mikro1")

    for item in general + firewall:
        if "comment" in item and "address-list" not in item["resource"]:
            assert router.by_comment(item["resource"], item["comment"]), item["comment"]
    assert router.state["/system/identity"][0]["name"] == "lab-mikro1"
    assert router.state["/ipv6/settings"][0]["disable-ipv6"] == "no"

    # every posi rule is moved to its position, bot rules end the chain
    moves = {(call[2]["numbers"], call[2]["destination"]) for call in router.calls
             if call[0] == "call" and call[1] == "/ip/firewall/filter"}
    for item in firewall:
        if item.get("order") == "posi" and item["resource"] == "/ip/firewall/filter":
            rule = router.by_comment("/ip/firewall/filter", item["comment"])
            assert (rule["id"], str(item["posi"])) in moves, item["comment"]
    filters = [item.get("comment") for item in router.state["/ip/firewall/filter"]]
    bot = [item["comment"] for item in firewall if item.get("order") == "bot" and item["resource"] == "/ip/firewall/filter"]
    assert filters[-len(bot):] == bot


def test_firewall_order_does_not_depend_on_the_filesystem_order(lab, monkeypatch):
    # The final rule order comes from the config file order (top rules are added in that
    # order, posi rules are moved one after another), it must be the same on every machine
    _push("lab-mikro1")
    first = [item.get("comment") for item in lab["routers"]["lab-mikro1"].state["/ip/firewall/filter"]]

    listdir = os.listdir
    monkeypatch.setattr(mikro_shared.os, "listdir", lambda path: list(reversed(listdir(path))))
    _new_process()
    mikro_main.generate_config()
    lab["routers"].clear()
    _push("lab-mikro1")
    second = [item.get("comment") for item in lab["routers"]["lab-mikro1"].state["/ip/firewall/filter"]]

    assert first == second


def test_second_push_does_not_add_or_remove(lab):
    _push("lab-mikro2")
    router = lab["routers"]["lab-mikro2"]
    router.calls.clear()

    _push("lab-mikro2")

    assert not [call for call in router.calls if call[0] in ("add", "remove") and
                not _is_bot_rule(call)]


def _is_bot_rule(call):
    # bottom rules are re-added on every push to keep them last
    return call[1] in ("/ip/firewall/filter", "/ipv6/firewall/filter", "/ip/firewall/nat", "/ip/firewall/mangle",
                       "/ipv6/firewall/mangle")


def test_clean_removes_unknown_items_and_keeps_local_ones(lab):
    router = lab["routers"].setdefault("lab-mikro3", FakeRouterOsApi({
        "/ip/address": [{"id": "*100", "comment": "manual_leftover", "address": "192.0.2.1/32"},
                        {"id": "*101", "comment": "local_auto_keep_me", "address": "192.0.2.2/32"}],
        "/ip/firewall/filter": [{"id": "*102", "chain": "input", "action": "accept"}],
    }))
    _push("lab-mikro3")
    assert router.by_comment("/ip/address", "manual_leftover") is None
    assert router.by_comment("/ip/address", "local_auto_keep_me")
    assert not [item for item in router.state["/ip/firewall/filter"] if "comment" not in item]


def test_dry_run_documents_without_touching_the_router(lab, web_dir):
    _push("lab-mikro4", dry_run=True)
    assert lab["routers"]["lab-mikro4"].writes() == []
    mikro_docs.savedry_run()
    changes = (web_dir / "Changes.md").read_text()
    assert "##SIMULATION DRY RUN" in changes and "ADD config" in changes
    assert "PRIVATE_KEY" not in changes


def test_dry_run_never_writes(lab):
    # lab-mikro4 has mqtt_netwatch_monitor, the mqtt broker used to be written even in a dry run
    _push("lab-mikro4", dry_run=True)
    assert lab["routers"]["lab-mikro4"].writes() == []


def test_firewall_mode_only_touches_firewall(lab):
    _push("lab-mikro5", mode="firewall")
    paths = {call[1] for call in lab["routers"]["lab-mikro5"].writes()}
    assert paths and all("firewall" in path for path in paths)


def test_unreachable_device_is_skipped(lab, monkeypatch):
    monkeypatch.setattr(mikro_shared, "login", lambda *args: False)
    _push("lab-mikro1")
    assert "lab-mikro1" not in lab["routers"]


# ---------------------------------------------------------------- whole run

def test_control_automation_full_run(lab, web_dir, monkeypatch):
    _new_process()
    monkeypatch.setattr(mikro_main, "MULTIMODE", True)
    mikro_main.control_automation("global", False, False, False)

    # lab-mikro6 has push_config/push_clean disabled in the inventory
    assert sorted(lab["routers"]) == MANAGED[:-1]
    assert (web_dir / "Global.md").read_text().count("#DEVICE:") == len(MANAGED)
    assert "lab-mikro1" in (web_dir / "bind_A.txt").read_text()
    assert (web_dir / "Changes.html").exists()
    assert (lab["secrets"] / "external" / "external.md").exists()


def test_control_automation_single_device_by_name(lab):
    _new_process()
    mikro_main.control_automation("firewall", False, "lab-mikro5", False)
    assert list(lab["routers"]) == ["lab-mikro5"]


def test_device_with_push_disabled_is_never_contacted(lab):
    _push("lab-mikro6")
    assert "lab-mikro6" not in lab["routers"]
