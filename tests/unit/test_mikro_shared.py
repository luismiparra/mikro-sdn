import ipaddress
import json
import logging

import pytest
import yaml

import mikro_docs
import mikro_shared
from fakes import FakeRouterOsApi, FakeRouterOsError

DEVICE = {"name": "dev1"}


# ---------------------------------------------------------------- create_files

def test_create_files_builds_structure_and_css(secrets_dir, web_dir):
    mikro_shared.create_files()

    assert json.loads((secrets_dir / "secrets.json").read_text()) == {}
    for folder in ["external_export", "mgmt_export", "vpnconfig", "external"]:
        assert (secrets_dir / folder).is_dir()
    assert "body" in (web_dir / "style.css").read_text()


def test_create_files_keeps_existing_secrets_and_creates_missing_web(secrets_dir, monkeypatch):
    (secrets_dir / "external").mkdir()
    (secrets_dir / "external" / "external.json").write_text("{}")
    (secrets_dir / "external" / "external.yml").write_text("{}")
    (secrets_dir / "secrets.json").write_text('{"keep": 1}')
    web = secrets_dir / "new_web"
    monkeypatch.setattr(mikro_shared, "pathweb", str(web))

    mikro_shared.create_files()

    assert json.loads((secrets_dir / "secrets.json").read_text()) == {"keep": 1}
    assert (web / "style.css").exists()


def test_create_files_never_wipes_restored_secrets(secrets_dir):
    # secrets.json restored from a backup into a SECRETS without the external folder
    (secrets_dir / "secrets.json").write_text('{"keep": 1}')

    mikro_shared.create_files()

    assert json.loads((secrets_dir / "secrets.json").read_text()) == {"keep": 1}
    assert json.loads((secrets_dir / "external" / "external.json").read_text()) == {}
    assert yaml.safe_load((secrets_dir / "external" / "external.yml").read_text()) == {}


# ---------------------------------------------------------------- getRunningBy

def test_get_running_by_finds_item_by_tag():
    running = {"/ip/address": [{"address": "1"}, {"comment": "a", "id": "*1"}, {"comment": "b", "id": "*2"}]}
    assert mikro_shared.getRunningBy(running, "/ip/address", "b", "comment", DEVICE) == {"comment": "b", "id": "*2"}


def test_get_running_by_returns_false_when_missing():
    running = {"/ip/address": [{"comment": "a"}]}
    assert mikro_shared.getRunningBy(running, "/ip/address", "zzz", "comment", DEVICE) is False
    assert mikro_shared.getRunningBy(running, "/ip/route", "a", "comment", DEVICE) is False


def test_get_running_by_logs_and_returns_false_on_bad_data(caplog):
    with caplog.at_level(logging.ERROR):
        assert mikro_shared.getRunningBy(None, "/ip/address", "a", "comment", DEVICE) is False
    assert "Error getRunningBy" in caplog.text


# ---------------------------------------------------------------- needAnUpdate

def test_need_an_update_without_id_always_updates():
    item = {"resource": "/x", "comment": "a"}
    assert mikro_shared.needAnUpdate(item, {"comment": "a"}, DEVICE) is True
    assert item["id"] is None


def test_need_an_update_equal_item_ignores_custom_keys():
    item = {"resource": "/x", "use_set": False, "order": "top", "posi": "1", "comment": "a", "dst_port": "53"}
    router = {"id": "*1", "comment": "a", "dst-port": "53"}
    assert mikro_shared.needAnUpdate(item, router, DEVICE) is False


def test_need_an_update_detects_change_in_dashed_key():
    item = {"resource": "/x", "dst_port": "53"}
    router = {"id": "*1", "dst-port": "54"}
    assert mikro_shared.needAnUpdate(item, router, DEVICE) is True
    assert item["id"] == "*1"


def test_need_an_update_detects_change_in_plain_key():
    item = {"resource": "/x", "chain": "input"}
    router = {"id": "*7", "chain": "forward"}
    assert mikro_shared.needAnUpdate(item, router, DEVICE) is True
    assert item["id"] == "*7"


def test_need_an_update_key_missing_in_router():
    item = {"resource": "/x", "new_key": "v"}
    assert mikro_shared.needAnUpdate(item, {"id": "*1"}, DEVICE) is True


# ---------------------------------------------------------------- getRunningConfig

def test_get_running_config_reads_each_resource_once():
    api = FakeRouterOsApi({"/a": [{"id": "*1"}], "/b": []})
    rules = [{"resource": "/a"}, {"resource": "/a"}, {"resource": "/b"}]
    assert mikro_shared.getRunningConfig(api, rules, DEVICE) == {"/a": [{"id": "*1"}], "/b": []}
    assert len([c for c in api.calls if c[0] == "get"]) == 2


def test_get_running_config_returns_false_on_error():
    api = FakeRouterOsApi(failures={("/a", "get"): FakeRouterOsError("boom")})
    assert mikro_shared.getRunningConfig(api, [{"resource": "/a"}], DEVICE) is False


# ---------------------------------------------------------------- removeDuplicatesInRunning

def _dup_state(dynamic=None):
    first = {"id": "*1", "comment": "same"}
    second = {"id": "*2", "comment": "same"}
    if dynamic is not None:
        first["dynamic"], second["dynamic"] = dynamic
    return {"/ip/address": [first, second, {"id": "*3"}]}


@pytest.mark.xfail(strict=True, reason="BUG: the loops keep iterating the stale running list after the "
                   "refresh, so the pair is seen again reversed and the first copy is removed too")
@pytest.mark.parametrize("dynamic", [None, ("false", "false")])
def test_remove_duplicates_keeps_one_copy(dynamic):
    api = FakeRouterOsApi(_dup_state(dynamic))
    mikro_shared.removeDuplicatesInRunning(api, [{"resource": "/ip/address"}], False, DEVICE)
    assert [i["id"] for i in api.state["/ip/address"]] == ["*1", "*3"]


@pytest.mark.parametrize("dynamic", [None, ("false", "false")])
def test_remove_duplicates_current_behaviour_removes_both_copies(dynamic):
    api = FakeRouterOsApi(_dup_state(dynamic))
    mikro_shared.removeDuplicatesInRunning(api, [{"resource": "/ip/address"}], False, DEVICE)
    assert [i["id"] for i in api.state["/ip/address"]] == ["*3"]


def test_remove_duplicates_ignores_dynamic_items():
    api = FakeRouterOsApi(_dup_state(("true", "true")))
    mikro_shared.removeDuplicatesInRunning(api, [{"resource": "/ip/address"}], False, DEVICE)
    assert len(api.state["/ip/address"]) == 3


@pytest.mark.parametrize("dynamic", [None, ("false", "false")])
def test_remove_duplicates_dry_run_only_documents(dynamic):
    api = FakeRouterOsApi(_dup_state(dynamic))
    mikro_shared.removeDuplicatesInRunning(api, [{"resource": "/ip/address"}], True, DEVICE)
    assert len(api.state["/ip/address"]) == 3
    assert "REMOVE DUPLICATE IN RUNNING" in mikro_docs.global_dry_run_md
    assert "DUPLICATED IN RUNNING" in mikro_docs.global_dry_run_md


# ---------------------------------------------------------------- filterDuplicatedConfigRules

def test_filter_duplicated_config_rules_keeps_first_and_uncommented():
    rules = [{"comment": "a", "v": 1}, {"comment": "a", "v": 2}, {"use_set": True}, {"comment": "b"}]
    assert mikro_shared.filterDuplicatedConfigRules(rules) == [{"comment": "a", "v": 1}, {"use_set": True}, {"comment": "b"}]


def test_filter_duplicated_config_rules_compares_only_commented_items():
    rules = [{"use_set": True}, {"comment": "a"}]
    assert mikro_shared.filterDuplicatedConfigRules(rules) == rules


# ---------------------------------------------------------------- addConfig / newUpdateConfig

def test_add_config_strips_custom_keys_and_restores_resource():
    api = FakeRouterOsApi()
    item = {"resource": "/ip/address", "use_set": False, "comment": "c", "address": "1.1.1.1/32"}
    assert mikro_shared.addConfig(api.get_resource("/ip/address"), item, DEVICE) is True
    assert api.calls[-1] == ("add", "/ip/address", {"comment": "c", "address": "1.1.1.1/32"})
    assert item["resource"] == "/ip/address"


def test_add_config_failure_returns_false():
    api = FakeRouterOsApi(failures={("/ip/address", "add"): FakeRouterOsError("bad")})
    item = {"resource": "/ip/address", "comment": "c"}
    assert mikro_shared.addConfig(api.get_resource("/ip/address"), item, DEVICE) is False
    assert item["resource"] == "/ip/address"


def test_new_update_config_with_router_item_sets_id():
    api = FakeRouterOsApi({"/ip/dns": [{"id": "*5", "servers": "1.1.1.1"}]})
    item = {"resource": "/ip/dns", "use_set": True, "order": "top", "posi": "3", "servers": "8.8.8.8"}
    mikro_shared.newUpdateConfig(api, item, {"id": "*5"}, DEVICE)
    assert api.calls[-1] == ("set", "/ip/dns", {"servers": "8.8.8.8", "id": "*5"})
    assert api.state["/ip/dns"][0]["servers"] == "8.8.8.8"
    assert item["resource"] == "/ip/dns" and item["posi"] == "3"


def test_new_update_config_without_router_item_or_posi():
    api = FakeRouterOsApi()
    item = {"resource": "/ip/dns", "servers": "8.8.8.8"}
    mikro_shared.newUpdateConfig(api, item, None, DEVICE)
    assert api.calls[-1] == ("set", "/ip/dns", {"servers": "8.8.8.8"})
    assert item["posi"] is None


def test_new_update_config_failure_restores_tags():
    api = FakeRouterOsApi(failures={("/ip/dns", "set"): FakeRouterOsError("bad")})
    item = {"resource": "/ip/dns", "posi": "1", "servers": "8.8.8.8"}
    assert mikro_shared.newUpdateConfig(api, item, None, DEVICE) is False
    assert item["resource"] == "/ip/dns" and item["posi"] == "1"


# ---------------------------------------------------------------- process_config

def _device(**extra):
    device = {"name": "dev1", "location": "site1", "disable-ipv6": "no",
              "gatewayv4_list": [ipaddress.ip_address("10.0.0.1"), ipaddress.ip_address("10.70.1.1")]}
    device.update(extra)
    return device


def test_process_config_adds_updates_and_sets_ipv6():
    api = FakeRouterOsApi({"/ip/address": [{"id": "*1", "comment": "keep", "address": "old"}]})
    rules = [
        {"resource": "/ip/address", "use_set": False, "comment": "keep", "address": "new"},
        {"resource": "/ip/address", "use_set": False, "comment": "added", "address": "x"},
    ]
    mikro_shared.process_config(api, rules, _device(), False)

    assert api.by_comment("/ip/address", "keep")["address"] == "new"
    assert api.by_comment("/ip/address", "added")["address"] == "x"
    assert api.state["/ipv6/settings"][0]["disable-ipv6"] == "no"
    assert "ADD config" in mikro_docs.global_dry_run_md and "UPDATE config" in mikro_docs.global_dry_run_md


def test_process_config_dry_run_writes_nothing():
    api = FakeRouterOsApi({"/ip/address": [{"id": "*1", "comment": "keep", "address": "old"}]})
    rules = [
        {"resource": "/ip/address", "use_set": False, "comment": "keep", "address": "new"},
        {"resource": "/ip/address", "use_set": False, "comment": "added", "address": "x"},
        {"resource": "/ip/dns", "use_set": True, "servers": "1.1.1.1"},
    ]
    mikro_shared.process_config(api, rules, _device(**{"disable-ipv6": "yes"}), True)
    assert api.writes() == []


def test_process_config_unchanged_item_is_not_written():
    api = FakeRouterOsApi({"/ip/address": [{"id": "*1", "comment": "keep", "address": "same"}]})
    rules = [{"resource": "/ip/address", "use_set": False, "comment": "keep", "address": "same"}]
    mikro_shared.process_config(api, rules, _device(), False)
    assert [c for c in api.writes() if c[1] == "/ip/address"] == []


def test_process_config_disables_ipv6_when_requested():
    api = FakeRouterOsApi()
    rules = [{"resource": "/ip/dns", "use_set": True, "servers": "1.1.1.1"}]
    mikro_shared.process_config(api, rules, _device(**{"disable-ipv6": "yes"}), False)
    assert api.state["/ipv6/settings"][0]["disable-ipv6"] == "yes"


def test_process_config_use_set_by_name_found_and_ip_service_exception():
    api = FakeRouterOsApi({"/ip/service": [{"id": "*1", "name": "telnet", "disabled": "false"}],
                           "/user": [{"id": "*2", "name": "admin", "group": "read"}]})
    rules = [
        {"resource": "/ip/service", "use_set": True, "name": "telnet", "disabled": "true"},
        {"resource": "/user", "use_set": True, "name": "admin", "group": "full"},
    ]
    mikro_shared.process_config(api, rules, _device(), False)
    assert api.state["/ip/service"][0]["disabled"] == "true"
    assert ("set", "/ip/service", {"disabled": "true", "id": "*1"}) in api.calls
    assert api.state["/user"][0]["group"] == "full"


def test_process_config_use_set_by_name_found_dry_run():
    api = FakeRouterOsApi({"/user": [{"id": "*2", "name": "admin", "group": "read"}]})
    rules = [{"resource": "/user", "use_set": True, "name": "admin", "group": "full"}]
    mikro_shared.process_config(api, rules, _device(), True)
    assert api.writes() == []


def test_process_config_use_set_by_name_missing():
    api = FakeRouterOsApi()
    rules = [
        {"resource": "/iot/mqtt/brokers", "use_set": True, "name": "broker", "address": "10.0.0.1"},
        {"resource": "/snmp/community", "use_set": True, "name": "public", "addresses": "10.0.0.0/8"},
    ]
    mikro_shared.process_config(api, rules, _device(), False)
    assert api.state["/iot/mqtt/brokers"][0]["name"] == "broker"
    assert ("set", "/snmp/community", {"name": "public", "addresses": "10.0.0.0/8"}) in api.calls


def test_process_config_use_set_by_name_missing_dry_run():
    api = FakeRouterOsApi()
    rules = [{"resource": "/snmp/community", "use_set": True, "name": "public"}]
    mikro_shared.process_config(api, rules, _device(), True)
    assert api.writes() == []


def test_process_config_singleton_exceptions():
    api = FakeRouterOsApi()
    rules = [
        {"resource": "/snmp", "use_set": True, "enabled": "yes"},
        {"resource": "/system/identity", "use_set": True},
        {"resource": "/system/logging/action", "use_set": True, "numbers": "3", "vlan_src": "1"},
    ]
    mikro_shared.process_config(api, rules, _device(), False)
    assert api.state["/snmp"][0]["location"] == "site1"
    assert api.state["/system/identity"][0]["name"] == "dev1"
    assert api.state["/system/logging/action"][0]["src-address"] == "10.70.1.1"
    assert "vlan-src" not in api.state["/system/logging/action"][0]


def test_process_config_traffic_flow_adds_when_missing_and_updates_when_present():
    api = FakeRouterOsApi()
    rule = {"resource": "/ip/traffic-flow/target", "use_set": True, "numbers": "0", "port": "4739", "vlan_src": "0"}
    mikro_shared.process_config(api, [dict(rule)], _device(), False)
    target = api.state["/ip/traffic-flow/target"]
    assert len(target) == 1 and target[0]["src-address"] == "10.0.0.1" and "numbers" not in target[0]

    mikro_shared.process_config(api, [dict(rule, port="9999")], _device(), False)
    assert ("set", "/ip/traffic-flow/target",
            {"numbers": "0", "port": "9999", "src-address": "10.0.0.1"}) in api.calls


def test_process_config_traffic_flow_missing_dry_run():
    api = FakeRouterOsApi()
    rule = {"resource": "/ip/traffic-flow/target", "use_set": True, "numbers": "0", "vlan_src": "0"}
    mikro_shared.process_config(api, [rule], _device(), True)
    assert api.writes() == []


def test_process_config_system_logging_adds_when_action_missing():
    api = FakeRouterOsApi({"/system/logging": [{"id": "*1", "action": "memory", "topics": "info"}]})
    rule = {"resource": "/system/logging", "use_set": True, "numbers": "4", "action": "remote", "topics": "!debug"}
    mikro_shared.process_config(api, [dict(rule)], _device(), False)
    assert api.state["/system/logging"][1]["action"] == "remote"

    mikro_shared.process_config(api, [dict(rule)], _device(), False)
    assert ("set", "/system/logging", {"numbers": "4", "action": "remote", "topics": "!debug"}) in api.calls


def test_process_config_system_logging_dry_run():
    api = FakeRouterOsApi()
    rule = {"resource": "/system/logging", "use_set": True, "numbers": "4", "action": "remote"}
    mikro_shared.process_config(api, [rule], _device(), True)
    assert api.writes() == []


def test_process_config_rule_without_comment_and_use_set_stops(monkeypatch):
    stops = []
    monkeypatch.setattr(mikro_shared, "errorStop", lambda: stops.append(True))
    api = FakeRouterOsApi()
    mikro_shared.process_config(api, [{"resource": "/ip/dns", "use_set": False}], _device(), False)
    assert stops == [True]


def test_process_config_unexpected_error_stops(monkeypatch):
    stops = []
    monkeypatch.setattr(mikro_shared, "errorStop", lambda: stops.append(True))
    api = FakeRouterOsApi()
    assert mikro_shared.process_config(api, [{"resource": "/ip/dns"}], _device(), False) is False
    assert stops == [True]


# ---------------------------------------------------------------- connection_name

def test_connection_name_is_order_independent():
    assert mikro_shared.connection_name("b", "a") == "a__b"
    assert mikro_shared.connection_name("a", "b") == "a__b"


# ---------------------------------------------------------------- login

def test_login_returns_api(monkeypatch):
    captured = {}

    class Pool:
        def __init__(self, host, **kwargs):
            captured["host"] = host
            captured.update(kwargs)

        def get_api(self):
            return "API"

    monkeypatch.setattr(mikro_shared.routeros_api, "RouterOsApiPool", Pool)
    assert mikro_shared.login("u", "p", "10.0.0.1", DEVICE) == "API"
    assert captured["host"] == "10.0.0.1" and captured["port"] == 8729 and captured["use_ssl"] is True


@pytest.mark.parametrize("error", [ConnectionError("refused"), RuntimeError("other")])
def test_login_errors_return_false(monkeypatch, error):
    class Pool:
        def __init__(self, *args, **kwargs):
            raise error

    monkeypatch.setattr(mikro_shared.routeros_api, "RouterOsApiPool", Pool)
    assert mikro_shared.login("u", "p", "10.0.0.1", DEVICE) is False


# ---------------------------------------------------------------- load_config / load_config_by_device

def _write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, sort_keys=False))


def test_load_config_tags_resource_and_skips_duplicates(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(mikro_shared, "pathconfig", str(tmp_path))
    _write_yaml(tmp_path / "firewall" / "global" / "a.yml", {
        "/ip/firewall/filter": [{"comment": "r1"}, {"comment": "r1"}],
        "/ip/dns": [{"use_set": True, "servers": "x"}, {"use_set": False, "servers": "y"}],
    })
    with caplog.at_level(logging.WARNING):
        rules = mikro_shared.load_config("global", "firewall")
    assert rules == [{"comment": "r1", "resource": "/ip/firewall/filter"},
                     {"use_set": True, "servers": "x", "resource": "/ip/dns"}]
    assert "Duplicated rule" in caplog.text


def test_load_config_by_device_defaults_use_set(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mikro_shared, "pathconfig", str(tmp_path))
    _write_yaml(tmp_path / "dhcp" / "ipv4" / "dev1" / "v4.yml", {
        "/ip/dhcp-server/lease": [{"comment": "l1"}, {"comment": "l1"}],
        "/ip/dns": [{"use_set": True}, {"servers": "skip"}],
    })
    rules = mikro_shared.load_config_by_device("ipv4", "dhcp", "dev1")
    assert rules == [{"comment": "l1", "resource": "/ip/dhcp-server/lease", "use_set": False},
                     {"use_set": True, "resource": "/ip/dns"}]
    assert "Duplicated rule" in capsys.readouterr().out


def test_config_files_numeric_prefix_order(tmp_path):
    for name in ["10-web.yml", "2-contrack.yml", "100-drop.yml", "1-adl.yml", "v4.yml", "1-adlv6.yml"]:
        (tmp_path / name).write_text("{}")
    assert mikro_shared.config_files(str(tmp_path)) == [
        "1-adl.yml", "1-adlv6.yml", "2-contrack.yml", "10-web.yml", "100-drop.yml", "v4.yml"]


def test_load_config_reads_files_in_numeric_order(tmp_path, monkeypatch):
    monkeypatch.setattr(mikro_shared, "pathconfig", str(tmp_path))
    _write_yaml(tmp_path / "firewall" / "global" / "10-late.yml", {"/ip/firewall/filter": [{"comment": "late"}]})
    _write_yaml(tmp_path / "firewall" / "global" / "2-early.yml", {"/ip/firewall/filter": [{"comment": "early"}]})
    assert [rule["comment"] for rule in mikro_shared.load_config("global", "firewall")] == ["early", "late"]


# ---------------------------------------------------------------- load_inventory / assign_wan_order

def test_load_inventory_sorted_and_skips_non_yaml(tmp_path, monkeypatch):
    monkeypatch.setattr(mikro_shared, "pathconfig", str(tmp_path))
    _write_yaml(tmp_path / "inventory" / "b.yml", {"edge": [{"name": "b", "wan_order": 1}]})
    _write_yaml(tmp_path / "inventory" / "a.yaml", {"core": [{"name": "a", "wan_order": "0"}]})
    (tmp_path / "inventory" / ".DS_Store").write_text("junk")
    inventory = mikro_shared.load_inventory()
    assert [d["name"] for d in inventory] == ["a", "b"]
    assert inventory[0]["wan_order"] == 0


def test_assign_wan_order_appends_unpinned_after_pinned(caplog):
    inventory = [{"name": "z", "wan_order": 3}, {"name": "c"}, {"name": "b"}]
    with caplog.at_level(logging.WARNING):
        mikro_shared.assign_wan_order(inventory)
    assert {d["name"]: d["wan_order"] for d in inventory} == {"z": 3, "b": 4, "c": 5}
    assert "No wan_order in inventory" in caplog.text


def test_assign_wan_order_without_pinned_starts_at_zero():
    inventory = [{"name": "b"}, {"name": "a"}]
    mikro_shared.assign_wan_order(inventory)
    assert {d["name"]: d["wan_order"] for d in inventory} == {"a": 0, "b": 1}


def test_assign_wan_order_duplicated_stops(monkeypatch):
    stops = []
    monkeypatch.setattr(mikro_shared, "errorStop", lambda: stops.append(True))
    mikro_shared.assign_wan_order([{"name": "a", "wan_order": 1}, {"name": "b", "wan_order": 1}])
    assert stops == [True]


# ---------------------------------------------------------------- objectExists*

def test_object_exists():
    rules = [{"use_set": True}, {"comment": "a"}]
    assert mikro_shared.objectExists(rules, "a") is True
    assert mikro_shared.objectExists(rules, "b") is False


def test_object_exists_addr_list():
    rules = [{"comment": "x"}, {"comment": "ACL_TEST", "address": ["1.1.1.1", "2.2.2.2"]}]
    assert mikro_shared.objectExistsAddrList(rules, "ACL_TEST_2.2.2.2") is True
    assert mikro_shared.objectExistsAddrList(rules, "ACL_TEST_3.3.3.3") is False


# ---------------------------------------------------------------- clean_config

@pytest.fixture
def clean_routes(tmp_path, monkeypatch):
    def _write(routes):
        (tmp_path / "clean_routes.yml").write_text(yaml.dump(routes))
        monkeypatch.setattr(mikro_shared, "pathconfig", str(tmp_path))
    return _write


def _clean_state():
    return {"/ip/address": [
        # without comment
        {"id": "*1", "default": "false"},
        {"id": "*2", "default": "true"},
        {"id": "*3", "dynamic": "false"},
        {"id": "*4", "dynamic": "true"},
        {"id": "*5"},
        {"id": "*6", "default-name": "ether1"},
        # with comment, not in config
        {"id": "*7", "comment": "local_auto_manual"},
        {"id": "*8", "comment": "gone1", "default": "false"},
        {"id": "*9", "comment": "gone2", "default": "true"},
        {"id": "*A", "comment": "gone3", "builtin": "false"},
        {"id": "*B", "comment": "gone4", "builtin": "true"},
        {"id": "*C", "comment": "gone5", "dynamic": "false"},
        {"id": "*D", "comment": "gone6", "dynamic": "true"},
        {"id": "*E", "comment": "gone7"},
        {"id": "*F", "comment": "gone8", "default-name": "ether2"},
        # in config
        {"id": "*10", "comment": "keep"},
    ]}


def test_clean_config_removes_only_removable_items(clean_routes):
    clean_routes(["/ip/address"])
    api = FakeRouterOsApi(_clean_state())
    mikro_shared.clean_config(api, [{"comment": "keep"}], False, {"name": "dev1", "api_version": 720})
    remaining = sorted(item["id"] for item in api.state["/ip/address"])
    assert remaining == sorted(["*2", "*4", "*6", "*7", "*9", "*B", "*D", "*F", "*10"])


def test_clean_config_dry_run_only_documents(clean_routes):
    clean_routes(["/ip/address"])
    api = FakeRouterOsApi(_clean_state())
    mikro_shared.clean_config(api, [{"comment": "keep"}], True, {"name": "dev1", "api_version": 720})
    assert len(api.state["/ip/address"]) == 16
    assert "REMOVING No comment" in mikro_docs.global_dry_run_md
    assert "REMOVING No config" in mikro_docs.global_dry_run_md


def test_clean_config_skips_bgp_instance_before_720(clean_routes):
    clean_routes(["/routing/bgp/instance"])
    api = FakeRouterOsApi({"/routing/bgp/instance": [{"id": "*1"}]})
    mikro_shared.clean_config(api, [], False, {"name": "dev1", "api_version": 717})
    assert api.calls == []


@pytest.mark.parametrize("path, level", [("/interface/wireless", logging.DEBUG), ("/ip/route", logging.ERROR)])
def test_clean_config_errors_are_logged(clean_routes, caplog, path, level):
    clean_routes([path])
    api = FakeRouterOsApi(failures={(path, "get"): FakeRouterOsError("no such command")})
    with caplog.at_level(logging.DEBUG):
        assert mikro_shared.clean_config(api, [], False, {"name": "dev1", "api_version": 720}) is False
    assert any(record.levelno == level and path in record.message for record in caplog.records)


# ---------------------------------------------------------------- prepare_sdn

def test_prepare_sdn_with_lan_builds_subnets_and_transits(device_factory):
    device = device_factory()
    mikro_shared.prepare_sdn(device)

    assert len(device["subnetsv4_list"]) == 251
    assert str(device["subnetsv4_list"][3]) == "10.21.3.0/24"
    assert str(device["gatewayv4_list"][3]) == "10.21.3.1"
    assert len(device["subnetsv6_list"]) == 252
    assert device["subnetsv6_list"][1].prefixlen == 112
    assert device["subnetsv6slaac_list"][1].prefixlen == 64
    assert len(device["subnet_transitv4"]) == 64
    transit = device["subnet_transitv4"][2]
    assert str(transit["subnet"]) == "10.21.250.8/30"
    assert (str(transit["ip1"]), str(transit["ip2"])) == ("10.21.250.9", "10.21.250.10")
    assert device["subnet_transitv6"][0]["subnet"].prefixlen == 127


def test_prepare_sdn_without_lan_only_builds_transits(device_factory):
    device = device_factory()
    device.pop("lan")
    mikro_shared.prepare_sdn(device)
    assert "subnetsv4_list" not in device
    assert len(device["subnet_transitv6"]) == 64


# ---------------------------------------------------------------- errorStop

def test_error_stop_exits(monkeypatch):
    monkeypatch.setenv("DEBUGMODE", "")
    with pytest.raises(SystemExit):
        mikro_shared.errorStop()


def test_error_stop_in_debug_waits_for_input(monkeypatch):
    prompts = []
    monkeypatch.setenv("DEBUGMODE", "1")
    monkeypatch.setattr("builtins.input", lambda text: prompts.append(text))
    mikro_shared.errorStop()
    assert prompts


def test_error_stop_disabled(monkeypatch):
    monkeypatch.setattr(mikro_shared, "STOP_ON_ERROR", False)
    mikro_shared.errorStop()


# ---------------------------------------------------------------- deprecated helpers

class _DeprecatedResource:
    def __init__(self, running=None, fail=False):
        self.running = running or [{}]
        self.fail = fail
        self.sets = []

    def get(self, id):
        return self.running

    def set(self, **values):
        if self.fail:
            raise RuntimeError("bad")
        self.sets.append(values)


def test_update_config_no_change_does_not_set():
    resource = _DeprecatedResource([{"chain": "input", "dst-port": "53"}])
    item = {"resource": "/x", "use_set": False, "chain": "input", "dst_port": "53"}
    assert mikro_shared.updateConfig(resource, item, "*1") is True
    assert resource.sets == []


def test_update_config_changes_are_set():
    resource = _DeprecatedResource([{"chain": "input", "dst-port": "53"}])
    item = {"resource": "/x", "use_set": False, "chain": "forward", "dst_port": "54"}
    assert mikro_shared.updateConfig(resource, item, "*1") is True
    assert resource.sets == [{"chain": "forward", "dst_port": "54", "id": "*1"}]
    assert item["resource"] == "/x"


def test_update_config_unknown_key_raises():
    # The debug log references the alternative key that does not exist
    resource = _DeprecatedResource([{"chain": "input"}])
    with pytest.raises(KeyError):
        mikro_shared.updateConfig(resource, {"resource": "/x", "unknown_key": "v"}, "*1")


def test_update_config_without_id_and_failure():
    resource = _DeprecatedResource(fail=True)
    item = {"resource": "/x", "chain": "input"}
    assert mikro_shared.updateConfig(resource, item, None) is False
    assert item["resource"] == "/x"


def test_force_update_config():
    resource = _DeprecatedResource()
    item = {"resource": "/x", "use_set": True, "chain": "input"}
    assert mikro_shared.forceUpdateConfig(resource, item, "*2") is True
    assert resource.sets == [{"chain": "input", "id": "*2"}]

    failing = _DeprecatedResource(fail=True)
    item = {"resource": "/x", "chain": "input"}
    assert mikro_shared.forceUpdateConfig(failing, item, None) is False
    assert item["resource"] == "/x"
