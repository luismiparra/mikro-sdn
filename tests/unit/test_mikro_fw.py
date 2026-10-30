import logging

import pytest

import mikro_docs
import mikro_fw
from fakes import FakeRouterOsApi, FakeRouterOsError

DEVICE = {"name": "dev1"}


# ---------------------------------------------------------------- addFWRule / moveFWRule

def test_add_fw_rule_strips_custom_keys():
    api = FakeRouterOsApi()
    item = {"resource": "/ip/firewall/filter", "order": "posi", "posi": "2", "comment": "r", "chain": "input"}
    assert mikro_fw.addFWRule(api.get_resource("/ip/firewall/filter"), item, DEVICE) is True
    assert api.calls[-1] == ("add", "/ip/firewall/filter", {"comment": "r", "chain": "input"})
    assert item["resource"] == "/ip/firewall/filter" and item["posi"] == "2" and "order" not in item


def test_add_fw_rule_without_posi_and_failure(caplog):
    api = FakeRouterOsApi(failures={("/ip/firewall/filter", "add"): FakeRouterOsError("bad")})
    item = {"resource": "/ip/firewall/filter", "comment": "r"}
    with caplog.at_level(logging.ERROR):
        assert mikro_fw.addFWRule(api.get_resource("/ip/firewall/filter"), item, DEVICE) is False
    assert "ADD FW rule Error IN RULE r" in caplog.text


def test_move_fw_rule():
    api = FakeRouterOsApi({"/ip/firewall/filter": [{"id": "*1"}, {"id": "*2"}]})
    item = {"resource": "/ip/firewall/filter", "comment": "r", "posi": 0}
    assert mikro_fw.moveFWRule(api.get_resource("/ip/firewall/filter"), item, {"id": "*2"}, DEVICE) is True
    assert [i["id"] for i in api.state["/ip/firewall/filter"]] == ["*2", "*1"]


def test_move_fw_rule_already_in_place_is_success():
    error = FakeRouterOsError("can not move object before itself")
    api = FakeRouterOsApi(failures={("/ip/firewall/filter", "call"): error})
    item = {"resource": "/ip/firewall/filter", "comment": "r", "posi": 0}
    assert mikro_fw.moveFWRule(api.get_resource("/ip/firewall/filter"), item, {"id": "*1"}, DEVICE) is True


def test_move_fw_rule_other_error_fails():
    api = FakeRouterOsApi(failures={("/ip/firewall/filter", "call"): FakeRouterOsError("no such item")})
    item = {"resource": "/ip/firewall/filter", "comment": "r", "posi": 0}
    assert mikro_fw.moveFWRule(api.get_resource("/ip/firewall/filter"), item, {"id": "*1"}, DEVICE) is False


# ---------------------------------------------------------------- clean_config

def _fw_state():
    return {
        "/ip/firewall/filter": [
            {"id": "*1"},
            {"id": "*2", "comment": "keep"},
            {"id": "*3", "comment": "local_auto_manual"},
            {"id": "*4", "comment": "old_static", "dynamic": "false"},
            {"id": "*5", "comment": "old_dynamic", "dynamic": "true"},
            {"id": "*6", "comment": "old_plain"},
        ],
        "/ip/firewall/address-list": [
            {"id": "*7"},
            {"id": "*8", "comment": "ACL_TEST_1.1.1.1"},
            {"id": "*9", "comment": "automation_test1_x"},
            {"id": "*A", "comment": "ACL_TEST_9.9.9.9"},
        ],
    }


_RULES = [{"comment": "keep"}, {"comment": "ACL_TEST", "address": ["1.1.1.1"]}]


def test_clean_config_removes_rules_not_in_config():
    api = FakeRouterOsApi(_fw_state())
    mikro_fw.clean_config(api, _RULES, False, DEVICE)
    assert [i["id"] for i in api.state["/ip/firewall/filter"]] == ["*2", "*3", "*5"]
    assert [i["id"] for i in api.state["/ip/firewall/address-list"]] == ["*8", "*9"]


def test_clean_config_dry_run_only_documents():
    api = FakeRouterOsApi(_fw_state())
    mikro_fw.clean_config(api, _RULES, True, DEVICE)
    assert api.writes() == []
    assert mikro_docs.global_dry_run_md.count("REMOVING") == 5


class _BrokenResource:
    def __init__(self, path):
        self.path = path

    def get(self):
        raise FakeRouterOsError("no such command")


class _BrokenApi:
    def get_resource(self, path):
        # RouterOS paths as the library reports them, with the trailing slash
        return _BrokenResource(path + "/")


def test_clean_config_errors_are_logged(caplog):
    with caplog.at_level(logging.DEBUG):
        mikro_fw.clean_config(_BrokenApi(), [], False, DEVICE)
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    debugs = [r for r in caplog.records if r.levelno == logging.DEBUG and "Remove non comment" in r.message]
    assert len(errors) == 7 and len(debugs) == 1  # /ipv6/firewall/nat/ is ignored


# ---------------------------------------------------------------- process_fw_rules

def _rules():
    return [
        {"resource": "/ip/firewall/address-list", "comment": "ACL_TEST", "address": ["1.1.1.1", "2.2.2.2"]},
        {"resource": "/ip/firewall/filter", "order": "top", "comment": "top_new", "chain": "input"},
        {"resource": "/ip/firewall/filter", "order": "top", "comment": "top_changed", "chain": "forward"},
        {"resource": "/ip/firewall/filter", "order": "top", "comment": "top_same", "chain": "input"},
        {"resource": "/ip/firewall/filter", "order": "posi", "posi": "0", "comment": "posi_rule", "chain": "input"},
        {"resource": "/ip/firewall/filter", "order": "bot", "comment": "bot_existing", "action": "drop"},
        {"resource": "/ip/firewall/filter", "order": "bot", "comment": "bot_new", "action": "drop"},
    ]


def _running():
    return {
        "/ip/firewall/address-list": [
            {"id": "*1", "comment": "ACL_TEST_1.1.1.1", "list": "ACL_TEST", "address": "1.1.1.1"},
            {"id": "*2", "comment": "ACL_TEST_2.2.2.2", "list": "OLD", "address": "2.2.2.2"},
        ],
        "/ip/firewall/filter": [
            {"id": "*3", "comment": "bot_existing", "action": "drop"},
            {"id": "*4", "comment": "top_changed", "chain": "input"},
            {"id": "*5", "comment": "top_same", "chain": "input"},
        ],
    }


def test_process_fw_rules_applies_add_update_bot_and_posi():
    api = FakeRouterOsApi(_running())
    mikro_fw.process_fw_rules(api, _rules(), False, DEVICE)

    assert api.by_comment("/ip/firewall/address-list", "ACL_TEST_2.2.2.2")["list"] == "ACL_TEST"
    assert api.by_comment("/ip/firewall/filter", "top_changed")["chain"] == "forward"
    assert api.by_comment("/ip/firewall/filter", "top_new")["chain"] == "input"
    assert not [c for c in api.writes() if c[2].get("id") == "*5"]

    order = [item["comment"] for item in api.state["/ip/firewall/filter"]]
    assert order[0] == "posi_rule"
    assert order[-2:] == ["bot_existing", "bot_new"]
    assert ("remove", "/ip/firewall/filter", {"id": "*3"}) in api.calls


def test_process_fw_rules_adds_new_address_list_entries():
    api = FakeRouterOsApi()
    mikro_fw.process_fw_rules(api, _rules()[:1], False, DEVICE)
    entries = api.state["/ip/firewall/address-list"]
    assert [(e["comment"], e["list"], e["address"]) for e in entries] == [
        ("ACL_TEST_1.1.1.1", "ACL_TEST", "1.1.1.1"), ("ACL_TEST_2.2.2.2", "ACL_TEST", "2.2.2.2")]


def test_process_fw_rules_dry_run_writes_nothing():
    api = FakeRouterOsApi(_running())
    rules = _rules() + [{"resource": "/ip/firewall/address-list", "comment": "NEW", "address": ["3.3.3.3"]}]
    mikro_fw.process_fw_rules(api, rules, True, DEVICE)
    assert api.writes() == []
    for text in ["UPDATE adl config", "ADD adl config", "UPDATE fw config", "ADD fw config"]:
        assert text in mikro_docs.global_dry_run_md


def test_process_fw_rules_posi_rule_missing_on_router_is_skipped():
    api = FakeRouterOsApi()
    rules = [{"resource": "/ip/firewall/filter", "order": "posi", "posi": "0", "comment": "p", "chain": "input"}]
    mikro_fw.process_fw_rules(api, rules, True, DEVICE)
    real = FakeRouterOsApi()
    real.get_resource = lambda path: _AddIgnoredResource(real, path)
    mikro_fw.process_fw_rules(real, [dict(rules[0])], False, DEVICE)
    assert not [c for c in real.calls if c[0] == "call"]


class _AddIgnoredResource:
    """A router that accepts the add but never shows the rule (e.g. filtered out)."""

    def __init__(self, router, path):
        self.inner = FakeRouterOsApi.get_resource(router, path)

    def get(self, **filters):
        return [] if filters else self.inner.get()

    def add(self, **values):
        self.inner.router.calls.append(("add", self.inner.path, values))


def test_add_fw_rule_failure_loses_resource_key():
    api = FakeRouterOsApi(failures={("/ip/firewall/filter", "add"): FakeRouterOsError("bad")})
    item = {"resource": "/ip/firewall/filter", "comment": "r"}
    mikro_fw.addFWRule(api.get_resource("/ip/firewall/filter"), item, DEVICE)
    assert "resource" not in item


@pytest.mark.xfail(strict=True, raises=KeyError,
                   reason="BUG: a failed addFWRule does not restore item['resource'] and the "
                          "dry_run_add that follows aborts the whole firewall push")
def test_process_fw_rules_survives_a_failed_add():
    api = FakeRouterOsApi(failures={("/ip/firewall/filter", "add"): FakeRouterOsError("bad")})
    rules = [{"resource": "/ip/firewall/filter", "order": "top", "comment": "a", "chain": "input"},
             {"resource": "/ip/firewall/filter", "order": "top", "comment": "b", "chain": "input"}]
    mikro_fw.process_fw_rules(api, rules, False, DEVICE)


class _EmptyPathResource(_BrokenResource):
    pass


class _EmptyPathApi:
    def get_resource(self, path):
        return _EmptyPathResource("" if "address-list" in path else path)


def test_clean_config_ignored_address_list_path_logs_debug(caplog):
    with caplog.at_level(logging.DEBUG):
        mikro_fw.clean_config(_EmptyPathApi(), [], False, DEVICE)
    debugs = [r for r in caplog.records if r.levelno == logging.DEBUG and "Remove non comment" in r.message]
    assert len(debugs) == 2
