import json
import os
import runpy
import sys

import pytest
import yaml

import mikro_docs
import mikro_fw
import mikro_main
import mikro_shared

MAIN_PATH = os.path.join(os.path.dirname(mikro_main.__file__), "mikro_main.py")


def _device(**extra):
    device = {"name": "dev1", "role": "core", "push_clean": True, "push_config": True, "clean_config": False,
              "mgmt_int": "10.0.0.1", "mgmt_ext": "dev1.example.com", "mgmt_aux": "10.79.9.9",
              "subnetv4": "10.21.0.0/16", "subnetv6": "2001:db8:10:0:10:21:0:0/96"}
    device.update(extra)
    return device


@pytest.fixture
def proposed(secrets_dir):
    folder = secrets_dir / "proposed"
    folder.mkdir()
    (folder / "dev1_fw.json").write_text(json.dumps([{"resource": "/ip/firewall/filter", "comment": "fw"}]))
    (folder / "dev1_global.json").write_text(json.dumps([{"resource": "/ip/address", "comment": "ip"}]))
    return folder


@pytest.fixture
def recorder(monkeypatch):
    """Replace the device facing calls with recorders."""
    calls = []

    def record(name, result=None):
        def _call(*args, **kwargs):
            calls.append((name, args))
            return result
        return _call

    monkeypatch.setattr(mikro_fw, "clean_config", record("fw.clean"))
    monkeypatch.setattr(mikro_shared, "clean_config", record("shared.clean"))
    monkeypatch.setattr(mikro_shared, "process_config", record("shared.push"))
    monkeypatch.setattr(mikro_fw, "process_fw_rules", record("fw.push"))
    return calls


def _login(monkeypatch, answers):
    """login() answers by ip: an api object or False."""
    tried = []

    def login(user, password, ip, device):
        tried.append(ip)
        return answers.get(ip, False)

    monkeypatch.setattr(mikro_shared, "login", login)
    return tried


# ---------------------------------------------------------------- clean_config

@pytest.mark.parametrize("mode, expected", [("global", ["fw.clean", "shared.clean"]), ("firewall", ["fw.clean"]),
                                            ("config", [])])
def test_clean_config_modes(monkeypatch, proposed, recorder, mode, expected):
    _login(monkeypatch, {"10.0.0.1": "API"})
    mikro_main.clean_config(_device(), mode, False)
    assert [name for name, _ in recorder] == expected
    if expected:
        assert recorder[0][1][1] == [{"resource": "/ip/firewall/filter", "comment": "fw"}]


def test_clean_config_clean_device_cleans_everything(monkeypatch, recorder, secrets_dir):
    _login(monkeypatch, {"10.0.0.1": "API"})
    mikro_main.clean_config(_device(clean_config=True), "global", True)
    assert [(name, args[1]) for name, args in recorder] == [("fw.clean", []), ("shared.clean", [])]


def test_clean_config_falls_back_to_external_ip(monkeypatch, proposed, recorder):
    tried = _login(monkeypatch, {"dev1.example.com": "API"})
    mikro_main.clean_config(_device(), "firewall", False)
    assert tried == ["10.0.0.1", "dev1.example.com"] and len(recorder) == 1


def test_clean_config_unreachable(monkeypatch, proposed, recorder):
    _login(monkeypatch, {})
    mikro_main.clean_config(_device(), "global", False)
    assert recorder == []


def test_clean_config_aux_ip(monkeypatch, proposed, recorder):
    tried = _login(monkeypatch, {"10.79.9.9": "API"})
    mikro_main.clean_config(_device(), "firewall", False, aux_ip=True)
    assert tried == ["10.79.9.9"] and len(recorder) == 1

    tried.clear()
    _login(monkeypatch, {})
    recorder.clear()
    mikro_main.clean_config(_device(), "firewall", False, aux_ip=True)
    assert recorder == []


def test_clean_config_disabled(monkeypatch, recorder):
    tried = _login(monkeypatch, {"10.0.0.1": "API"})
    mikro_main.clean_config(_device(push_clean=False), "global", False)
    assert tried == [] and recorder == []


# ---------------------------------------------------------------- push_config

@pytest.mark.parametrize("mode, expected", [("global", ["shared.push", "fw.push"]), ("firewall", ["fw.push"])])
def test_push_config_modes(monkeypatch, proposed, recorder, mode, expected):
    _login(monkeypatch, {"10.0.0.1": "API"})
    mikro_main.push_config(_device(), mode, False)
    assert [name for name, _ in recorder] == expected


def test_push_config_connection_paths(monkeypatch, proposed, recorder):
    tried = _login(monkeypatch, {"dev1.example.com": "API"})
    mikro_main.push_config(_device(), "firewall", False)
    assert tried == ["10.0.0.1", "dev1.example.com"] and len(recorder) == 1

    recorder.clear()
    _login(monkeypatch, {})
    mikro_main.push_config(_device(), "firewall", False)
    mikro_main.push_config(_device(), "firewall", False, aux_ip=True)
    assert recorder == []

    _login(monkeypatch, {"10.79.9.9": "API"})
    mikro_main.push_config(_device(), "firewall", False, aux_ip=True)
    assert len(recorder) == 1


@pytest.mark.parametrize("extra", [{"push_config": False}, {"clean_config": True}])
def test_push_config_disabled(monkeypatch, recorder, extra):
    tried = _login(monkeypatch, {"10.0.0.1": "API"})
    mikro_main.push_config(_device(**extra), "global", False)
    assert tried == [] and recorder == []


# ---------------------------------------------------------------- clean_and_push

@pytest.mark.parametrize("dry_run, header", [(True, "##SIMULATION DRY RUN"), (False, "##PUSH MODE REAL")])
def test_clean_and_push_managed_role(monkeypatch, dry_run, header):
    order = []
    monkeypatch.setattr(mikro_main, "clean_config", lambda *a: order.append("clean"))
    monkeypatch.setattr(mikro_main, "push_config", lambda *a: order.append("push"))
    assert mikro_main.clean_and_push(_device(), "global", dry_run, False) is True
    assert order == ["clean", "push"]
    assert header in mikro_docs.global_dry_run_md


def test_clean_and_push_ignores_unmanaged_roles(monkeypatch):
    order = []
    monkeypatch.setattr(mikro_main, "clean_config", lambda *a: order.append("clean"))
    assert mikro_main.clean_and_push(_device(role="external_edge"), "global", False, False) is True
    assert order == []


# ---------------------------------------------------------------- generate_config

def test_generate_config_assembles_and_splits_firewall(monkeypatch, secrets_dir, config_dir, tmp_path):
    config_root = tmp_path / "cfg"
    (config_root / "firewall" / "dev1").mkdir(parents=True)
    config_dir(config_root)

    devices = [
        _device(configlet=["fw", "general", "lan", "wan", "dhcp", "autoupdate", "internet", "wg_vpn",
                           "wifi", "netwatch", "radius_server"]),
        _device(name="dev2", configlet=["fw", "wan", "wifi"]),
        _device(name="dev3", clean_config=True, configlet=["fw"]),
        _device(name="ext", role="external_edge", configlet=["wan"]),
    ]
    monkeypatch.setattr(mikro_shared, "load_inventory", lambda: devices)
    monkeypatch.setattr(mikro_shared, "prepare_sdn", lambda device: device)

    def item(resource, comment):
        return {"resource": resource, "comment": comment}

    sources = {
        ("global", "firewall"): [item("/ip/firewall/filter", "global_fw")],
        ("dev1", "firewall"): [item("/ip/firewall/filter", "dev_fw")],
        ("core", "general"): [item("/ip/dns", "general")],
    }
    monkeypatch.setattr(mikro_shared, "load_config", lambda role, resource: list(sources[(role, resource)]))
    monkeypatch.setattr(mikro_shared, "load_config_by_device", lambda *a: [item("/ip/dhcp-server/lease", "lease")])
    monkeypatch.setattr(mikro_main.mikro_wan, "loadWan", lambda inventory: {"dev1": [item("/ipv6/firewall/filter", "wan_fw"),
                                                                                      item("/interface/wireguard", "wg")]})
    monkeypatch.setattr(mikro_main.mikro_lan, "load_config", lambda d, inv: [item("/interface/vlan", "vlan"),
                                                                              item("/interface/vlan", "vlan")])
    monkeypatch.setattr(mikro_main.mikro_autoupdate, "load_config", lambda d: [item("/system/scheduler", "auto")])
    monkeypatch.setattr(mikro_main.mikro_internet, "load_config", lambda d: [item("/ip/firewall/mangle", "mangle")])
    monkeypatch.setattr(mikro_main.mikro_wg, "load_config", lambda d: [item("/ip/firewall/nat", "nat")])
    monkeypatch.setattr(mikro_main.mikro_wifi, "load_config", lambda d, inv: [item("/interface/wireless", "wifi")])
    monkeypatch.setattr(mikro_main.mikro_netwatch, "load_config", lambda d: [item("/ipv6/firewall/mangle", "mangle6")])
    monkeypatch.setattr(mikro_main.mikro_radius_server, "load_config", lambda d: [item("/user-manager", "radius")])
    documented = []
    monkeypatch.setattr(mikro_docs, "createDocs", lambda device: documented.append(device["name"]))

    proposed = secrets_dir / "proposed"
    proposed.mkdir()
    (secrets_dir / "old_proposed").mkdir()
    (proposed / "dev1_fw.json").write_text("[\"previous\"]")
    (proposed / "dev1_global.json").write_text("[\"previous\"]")

    mikro_main.generate_config()

    fw = json.loads((proposed / "dev1_fw.json").read_text())
    general = json.loads((proposed / "dev1_global.json").read_text())
    assert [i["comment"] for i in fw] == ["global_fw", "dev_fw", "wan_fw", "mangle", "nat", "mangle6"]
    assert [i["comment"] for i in general] == ["general", "vlan", "wg", "lease", "auto", "wifi", "radius"]
    assert yaml.safe_load((proposed / "dev1_global.yml").read_text()) == general
    assert yaml.safe_load((proposed / "dev1_fw.yml").read_text()) == fw
    assert json.loads((secrets_dir / "old_proposed" / "dev1_fw.json").read_text()) == ["previous"]
    assert json.loads((secrets_dir / "old_proposed" / "dev1_global.json").read_text()) == ["previous"]

    # dev2: no device firewall folder, not in the wan mesh, wifi needs lan
    assert [i["comment"] for i in json.loads((proposed / "dev2_fw.json").read_text())] == ["global_fw"]
    assert json.loads((proposed / "dev2_global.json").read_text()) == []
    assert documented == ["dev1", "dev2"]


def test_generate_config_reports_the_configlets_of_the_generated_devices(monkeypatch, secrets_dir):
    devices = [_device(configlet=["general", "lan"]), _device(name="dev2", configlet=["general", "wifi"]),
               _device(name="dev3", clean_config=True), _device(name="ext", role="external_edge")]
    monkeypatch.setattr(mikro_shared, "load_inventory", lambda: devices)
    monkeypatch.setattr(mikro_shared, "prepare_sdn", lambda device: device)
    monkeypatch.setattr(mikro_shared, "load_config", lambda role, resource: [])
    monkeypatch.setattr(mikro_main.mikro_wan, "loadWan", lambda inventory: {})
    monkeypatch.setattr(mikro_main.mikro_lan, "load_config", lambda d, inv: [])
    monkeypatch.setattr(mikro_docs, "createDocs", lambda device: None)
    reports = []
    monkeypatch.setattr(mikro_main.mikro_log, "report", lambda *args: reports.append(args))

    mikro_main.generate_config()

    assert reports == [("GENERAL -> Generated config", ["Device", "Role", "general", "lan", "wifi"],
                        [["dev1", "core", "✅", "✅", "·"], ["dev2", "core", "✅", "·", "✅"]])]


def test_generate_config_creates_proposed_folders(monkeypatch, secrets_dir):
    monkeypatch.setattr(mikro_shared, "load_inventory", lambda: [_device(configlet=[])])
    monkeypatch.setattr(mikro_shared, "prepare_sdn", lambda device: device)
    monkeypatch.setattr(mikro_main.mikro_wan, "loadWan", lambda inventory: {})
    monkeypatch.setattr(mikro_docs, "createDocs", lambda device: None)
    mikro_main.generate_config()
    assert (secrets_dir / "proposed" / "dev1_global.json").exists()
    assert (secrets_dir / "old_proposed").is_dir()


# ---------------------------------------------------------------- control_automation

@pytest.fixture
def automation(monkeypatch):
    calls = []
    inventory = [_device(), _device(name="dev2"), _device(name="ext", role="external_edge")]
    monkeypatch.setattr(mikro_shared, "load_inventory", lambda: inventory)
    monkeypatch.setattr(mikro_shared, "create_files", lambda: calls.append("create_files"))
    monkeypatch.setattr(mikro_main, "generate_config", lambda: calls.append("generate"))
    monkeypatch.setattr(mikro_main, "clean_and_push",
                        lambda device, mode, dry_run, aux: calls.append(("push", device["name"], aux)))
    for name in ["create_external", "save_global", "savedry_run"]:
        monkeypatch.setattr(mikro_docs, name, lambda name=name: calls.append(name))
    return calls


@pytest.mark.parametrize("multimode", [True, False])
def test_control_automation_pushes_every_device(monkeypatch, automation, multimode):
    monkeypatch.setattr(mikro_main, "MULTIMODE", multimode)
    monkeypatch.setattr(mikro_main, "WORKERS_MAX", 2)
    mikro_main.control_automation("global", False, False, False)
    pushes = sorted(call[1] for call in automation if isinstance(call, tuple))
    assert pushes == ["dev1", "dev2", "ext"]
    assert automation[:2] == ["create_files", "generate"]
    assert automation[-3:] == ["create_external", "save_global", "savedry_run"]


def test_control_automation_reports_the_push_of_the_managed_devices(monkeypatch, automation):
    reports = []
    monkeypatch.setattr(mikro_main.mikro_log, "device_report", lambda title, names: reports.append((title, names)))
    mikro_main.control_automation("global", False, False, False)
    mikro_main.control_automation("config", False, False, False)
    mikro_main.control_automation("firewall", False, "dev2", False)
    mikro_main.control_automation("firewall", False, "ext", False)
    assert reports == [("GENERAL -> Push result", ["dev1", "dev2"]),
                       ("ONEHOST MODE -> Push result", ["dev2"])]


def test_control_automation_config_mode_does_not_push(automation):
    mikro_main.control_automation("config", True, False, False)
    assert not [call for call in automation if isinstance(call, tuple)]
    assert "generate" in automation and "savedry_run" in automation


def test_control_automation_unknown_mode_does_nothing(automation):
    mikro_main.control_automation("other", True, False, False)
    assert automation == ["create_files", "create_external", "save_global", "savedry_run"]


def test_control_automation_single_device(automation):
    mikro_main.control_automation("firewall", False, "dev2", "aux")
    assert [call for call in automation if isinstance(call, tuple)] == [("push", "dev2", "aux")]
    assert "savedry_run" not in automation


@pytest.mark.parametrize("name, mode", [("ext", "global"), ("dev1", "config"), ("missing", "global")])
def test_control_automation_single_device_not_pushed(automation, name, mode):
    mikro_main.control_automation(mode, False, name, False)
    assert not [call for call in automation if isinstance(call, tuple)]


# ---------------------------------------------------------------- control

def _control_file(tmp_path, monkeypatch, data):
    (tmp_path / "control.yml").write_text(yaml.dump(data))
    monkeypatch.setattr(mikro_main, "pathcontrol", str(tmp_path))


def _capture_automation(monkeypatch):
    runs = []
    monkeypatch.setattr(mikro_main, "control_automation", lambda *args: runs.append(args))
    return runs


def test_control_runs_automation_with_control_file_settings(tmp_path, monkeypatch):
    _control_file(tmp_path, monkeypatch, {"run_1_mikro_auto": True, "mikro_auto_mode": "firewall",
                                          "mikro_auto_dry_run": True})
    runs = _capture_automation(monkeypatch)
    mikro_main.control(False)
    assert runs == [("firewall", True, False, False)]


def test_control_disabled_runs_only_for_specific_device(tmp_path, monkeypatch):
    _control_file(tmp_path, monkeypatch, {"run_1_mikro_auto": False, "mikro_auto_mode": "global",
                                          "mikro_auto_dry_run": False})
    runs = _capture_automation(monkeypatch)
    mikro_main.control(False)
    assert runs == []
    mikro_main.control("dev1", "aux")
    assert runs == [("global", False, "dev1", "aux")]


def test_control_without_key(tmp_path, monkeypatch):
    _control_file(tmp_path, monkeypatch, {"other": True})
    runs = _capture_automation(monkeypatch)
    mikro_main.control("dev1")
    assert runs == []


# ---------------------------------------------------------------- command line

def _main_block():
    source = open(MAIN_PATH).read()
    start = source.index('if __name__ == "__main__":')
    # pad with blank lines so coverage maps the block to its real line numbers
    return compile("\n" * source[:start].count("\n") + source[start:], MAIN_PATH, "exec")


def _run_main(monkeypatch, argv, target=""):
    """Run the command line block with control_automation replaced by a recorder."""
    runs = []
    monkeypatch.setattr(sys, "argv", ["mikro_main.py"] + argv)
    monkeypatch.setenv("TARGET_DEVICE", target)
    # run_path returns a copy of the namespace, the functions keep the original one
    module_globals = runpy.run_path(MAIN_PATH, run_name="not_main")["control"].__globals__
    module_globals["control_automation"] = lambda *args: runs.append(args)
    module_globals["__name__"] = "__main__"
    exec(_main_block(), module_globals)
    return runs


# The shipped control/control.yml is the safe one: mode config (generate only) and dry run

def test_cli_device_argument(monkeypatch):
    assert _run_main(monkeypatch, ["lab-mikro1"]) == [("config", True, "lab-mikro1", False)]


def test_cli_device_and_aux_arguments(monkeypatch):
    assert _run_main(monkeypatch, ["lab-mikro1", "aux"]) == [("config", True, "lab-mikro1", "aux")]


def test_cli_target_device_env(monkeypatch):
    assert _run_main(monkeypatch, [], target="lab-mikro2") == [("config", True, "lab-mikro2", False)]


def test_cli_full_run(monkeypatch):
    assert _run_main(monkeypatch, [], target="  ") == [("config", True, False, False)]


def test_debug_mode_enables_debug_logging(monkeypatch):
    import logging
    monkeypatch.setenv("DEBUGMODE", "1")
    configured = []
    import mikro_log
    monkeypatch.setattr(mikro_log, "setup", lambda **kwargs: configured.append(kwargs["level"]))
    runpy.run_path(MAIN_PATH, run_name="not_main")
    assert configured == [logging.DEBUG]


def test_aux_address_reads_the_old_misspelled_key():
    assert mikro_main.aux_address({"mgmt_aux": "10.79.9.1"}) == "10.79.9.1"
    assert mikro_main.aux_address({"mtmt_aux": "10.79.9.2"}) == "10.79.9.2"
