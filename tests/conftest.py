"""Shared test setup.

The production modules read their environment (paths, credentials, flags) at import time
and call load_dotenv(), so the environment is pinned here, before any of them is imported.
Every variable the project knows is set explicitly: load_dotenv() never overrides a variable
that already exists, so the developer's .env can not leak into the tests (DEBUGMODE in
particular would make errorStop() wait on input() and the web portal start a server).
"""

import copy
import itertools
import json
import os
import sys
import tempfile

import pytest
import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODULE_DIRS = ["1-mikro-auto", "2-mikro-monitoring", "3-mikro-webportal", "4-netbox"]

_SESSION_TMP = tempfile.mkdtemp(prefix="msdn-tests-")

TEST_ENV = {
    "CONFIG": os.path.join(REPO_ROOT, "config"),
    "CONTROLPATH": os.path.join(REPO_ROOT, "control"),
    "SECRETS": os.path.join(_SESSION_TMP, "secrets"),
    "WEB": os.path.join(_SESSION_TMP, "web"),
    "LOCALSTRING": '["local_auto_", "automation_test1_"]',
    "MIKRO_USER": "test_user",
    "MIKRO_PASSWORD": "test_password",
    "MIKRO_READ_USER": "test_read_user",
    "MIKRO_READ_PASSWORD": "test_read_password",
    "RADIUS_SECRET": "test_radius_secret",
    "DEBUGMODE": "",
    "TARGET_DEVICE": "",
    "INVENTORY": os.path.join(REPO_ROOT, "config", "inventory"),
    "INFLUX_ORG": "test_org",
    "INFLUX_BUCKET": "test_bucket",
    "INFLUX_URL": "http://influx.invalid:8086",
    "INFLUX_API_KEY": "test_influx_key",
    "MAIN_AUTO_PY_EXEC": "1-mikro-auto/mikro_main.py",
    "MQTT_USER": "test_mqtt_user",
    "MQTT_PASSWORD": "test_mqtt_password",
    "NETBOX_URL": "http://netbox.invalid:8000",
    "NETBOX_TOKEN": "test_netbox_token",
    "NETBOX_TAG": "MSDN-TEST",
    "ORG_NAME": "lab",
    "PORTAL_HOME_URL": "http://portal.example.int",
    "MQTT_SERVER": "192.0.2.14",
    "MQTT_PORT": "1883",
    "BOOT_UPDATE_URL": "http://192.0.2.200/router_boot_update",
    "MGMT_CHECK_HOSTS": '["192.0.2.1", "192.0.2.2", "192.0.2.3"]',
    "MGMT_HOSTS": '["192.0.2.200", "192.0.2.201"]',
    "RADIUS_CERTIFICATE": "",
}
os.environ.update(TEST_ENV)
os.makedirs(TEST_ENV["SECRETS"], exist_ok=True)
os.makedirs(TEST_ENV["WEB"], exist_ok=True)

for _module_dir in MODULE_DIRS:
    _path = os.path.join(REPO_ROOT, _module_dir)
    if _path not in sys.path:
        sys.path.insert(0, _path)

sys.path.insert(0, os.path.dirname(__file__))

import mikro_docs  # noqa: E402
import mikro_shared  # noqa: E402
import mikro_wan  # noqa: E402
import wgconfig.wgexec as wgexec  # noqa: E402

LAB_CONFIG = os.path.join(REPO_ROOT, "config")

# Modules that keep a copy of the SECRETS / WEB / CONFIG paths taken at import time
_PATH_SECRETS_MODULES = ["mikro_shared", "mikro_docs", "mikro_wan", "mikro_wg", "mikro_main",
                         "mikro_radius_server", "mikro_wifi"]
_PATH_WEB_MODULES = ["mikro_shared", "mikro_docs"]
_PATH_CONFIG_MODULES = {"mikro_shared": "pathconfig", "mikro_docs": "pathconfig",
                        "mikro_main": "pathconfig", "mikro_wg": "pathconfig",
                        "mikro_radius_server": "pathconfig", "mikro_wifi": "pathconfig",
                        "mikro_wan": "my_config", "mikro_fw": "my_config"}


@pytest.fixture(autouse=True)
def _repo_cwd(monkeypatch):
    # Templates are loaded with a path relative to the repository root
    monkeypatch.chdir(REPO_ROOT)


@pytest.fixture(autouse=True)
def _reset_module_state():
    # mikro_wan and mikro_docs accumulate state in module globals across a run
    mikro_wan.core_devices.clear()
    mikro_wan.edge_devices.clear()
    mikro_wan.external_devices.clear()
    mikro_wan.d_config.clear()
    mikro_wan.externalconf = {}
    mikro_docs.globalbind_str_a = ""
    mikro_docs.globalbind_str_ptr = ""
    mikro_docs.global_doc_md = ""
    mikro_docs.global_dry_run_md = "#CHANGES FILE MODE:\n"
    yield


@pytest.fixture(autouse=True)
def fake_wg_keys(monkeypatch):
    """Deterministic wireguard keys, no dependency on the `wg` binary."""
    counter = itertools.count(1)

    def generate_keypair():
        number = next(counter)
        return (f"PRIVATE_KEY_{number}", f"PUBLIC_KEY_{number}")

    def generate_presharedkey():
        return f"PRESHARED_KEY_{next(counter)}"

    monkeypatch.setattr(wgexec, "generate_keypair", generate_keypair)
    monkeypatch.setattr(wgexec, "generate_presharedkey", generate_presharedkey)
    return counter


@pytest.fixture
def secrets_dir(tmp_path, monkeypatch):
    """Empty SECRETS and WEB directories wired into every module that caches the paths."""
    secrets = tmp_path / "secrets"
    web = tmp_path / "web"
    secrets.mkdir()
    web.mkdir()

    for name in _PATH_SECRETS_MODULES:
        module = sys.modules.get(name) or __import__(name)
        monkeypatch.setattr(module, "path_secrets", str(secrets))
    for name in _PATH_WEB_MODULES:
        module = sys.modules.get(name) or __import__(name)
        monkeypatch.setattr(module, "pathweb", str(web))

    return secrets


@pytest.fixture
def web_dir(secrets_dir):
    return secrets_dir.parent / "web"


@pytest.fixture
def config_dir(monkeypatch):
    """Point every module that caches CONFIG to a given directory (lab config by default)."""

    def _use(path=LAB_CONFIG):
        for name, attribute in _PATH_CONFIG_MODULES.items():
            module = sys.modules.get(name) or __import__(name)
            monkeypatch.setattr(module, attribute, str(path))
        return path

    _use()
    return _use


@pytest.fixture
def lab_secrets(secrets_dir):
    """SECRETS directory with the files the lab configlets need (radius, wifi)."""
    (secrets_dir / "external").mkdir()
    (secrets_dir / "secrets.json").write_text("{}")
    (secrets_dir / "radius_users.yml").write_text(yaml.dump([
        {"user": "alice", "password": "alice_pass", "shared_users": "2"},
        {"user": "bob", "password": "bob_pass", "shared_users": "1"},
    ]))
    (secrets_dir / "radius_routers.yml").write_text(yaml.dump([
        {"name": "router1", "ip": "10.71.1.1", "secret": "router1_secret"},
    ]))
    (secrets_dir / "wifi.yml").write_text(yaml.dump(wifi_profile()))
    (secrets_dir / "mac_addr.yml").write_text(yaml.dump(["aa:bb:cc:dd:ee:01", "aa:bb:cc:dd:ee:02"]))
    return secrets_dir


def wifi_profile():
    return {
        "radius_server": [
            {"name": "radius_local", "ip": "10.71.2.3", "service": "wireless", "vlan_src": "0", "timeout": "3s"},
            {"name": "radius_vlan", "ip": "10.71.2.4", "service": "wireless", "vlan_src": "1", "timeout": "3s"},
        ],
        "sec_profile": [
            {"comment": "sec_profile_wpa", "name": "wpa", "mode": "dynamic-keys", "use_set": False},
        ],
        "int_wifi": [
            {"comment": "int_wifi_1", "name": "wlan1", "ssid": "rp", "vlan_id": "1", "use_set": False},
        ],
    }


def load_lab_inventory():
    with open(os.path.join(LAB_CONFIG, "inventory", "lab-mikro1.yml")) as file:
        return yaml.safe_load(file)


BASE_DEVICE = {
    "name": "dev1",
    "wan_order": 0,
    "site_id": 1,
    "monitoring": True,
    "wifi_profile": "wifi",
    "enable_vxlan": False,
    "enable_vxlan_to_vlan": False,
    "api_version": 720,
    "description": "test device",
    "role": "core",
    "use_bfd": True,
    "enabled": True,
    "push_config": True,
    "push_clean": True,
    "clean_config": False,
    "mgmt_ext": "dev1.example.int",
    "mgmt_int": "192.168.88.11",
    "external_ddns": False,
    "external_endpoint": "198.51.100.1",
    "as": "65110",
    "backbone_untrusted": False,
    "radius_core": False,
    "core_priority": False,
    "core_internet_transit": False,
    "location": "site1",
    "gateway_number": 1,
    "dhcp_pool_start": 100,
    "dhcp_pool_end": 250,
    "wg_mtu": "1280",
    "domain": "example.int",
    "dns1": "8.8.8.8",
    "dns2": "8.8.4.4",
    "dns1_fallback": "7.7.7.7",
    "dns2_fallback": "6.6.6.6",
    "internet_icmp_check1": "1.1.1.1",
    "internet_icmp_check2": "8.8.8.8",
    "ntp1": "10.21.3.10",
    "lease-time": "1d",
    "disable-ipv6": "no",
    "subnetv4": "10.21.0.0/16",
    "subnetv6": "2001:db8:10:0:10:21:0:0/96",
    "subnetv6slaac": "2001:db8:10:8800::/53",
    "configlet": [],
    "save_wg_files": False,
    "lan": {
        "safe_ports": None,
        "trunk_ports": ["ether3"],
        "isolated_trunk": False,
        "vlans": [
            {"id": 1, "name": "1safe", "ipv6": True, "ipv6slaac": False,
             "ipv4_vip_pool": None, "ipv6_vip_pool": None},
            {"id": 2, "name": "2dmz", "ipv6": False, "ipv6slaac": True,
             "ipv4_vip_pool": None, "ipv6_vip_pool": None},
        ],
    },
}


def make_device(**overrides):
    device = copy.deepcopy(BASE_DEVICE)
    device.update(overrides)
    return device


@pytest.fixture
def device_factory():
    return make_device


def read_json(path):
    with open(path) as file:
        return json.load(file)
