import json

import pytest

import mikro_shared
import mikro_wg


def _tunnel(**overrides):
    tunnel = {"id": 1, "name": "user_vpn", "admin": False, "mgmt_vpn": False,
              "persistent_keepalive_enable": False, "persistent_keepalive_seconds": "25",
              "allowed_ips": "0.0.0.0/0, ::/0", "disabled_peers": [3], "subnet": 100,
              "number_client": 4, "port": 30001}
    tunnel.update(overrides)
    return tunnel


def _device(device_factory, tunnels, **extra):
    device = device_factory(**{"wg-vpn": tunnels}, **extra)
    mikro_shared.prepare_sdn(device)
    return device


def _by_comment(config, comment):
    matches = [item for item in config if item.get("comment") == comment]
    assert matches, f"{comment} not generated"
    return matches[0]


def test_user_tunnel_generates_interface_peers_and_addresses(device_factory, secrets_dir):
    (secrets_dir / "secrets.json").write_text("{}")
    device = _device(device_factory, [_tunnel()], api_version=716)

    config = mikro_wg.load_config(device)

    assert [i["comment"] for i in config[:2]] == ["list_wg_vpn_admins", "list_wg_vpn_default"]
    interface = _by_comment(config, "int_w_vpn_user_vpn")
    assert interface["listen_port"] == "30001" and interface["mtu"] == "1280"
    assert _by_comment(config, "list_item_int_w_vpn_user_vpn")["list"] == "list_wg_vpn_default"
    assert _by_comment(config, "fw_in_w_vpn_user_vpn")["dst_port"] == "30001"
    _by_comment(config, "fwg6_in_w_vpn_user_vpn")
    assert not [i for i in config if "vpn_admin_in" in i["comment"]]

    peers = [i for i in config if i["resource"] == "/interface/wireguard/peers"]
    assert [p["name"] for p in peers] == ["peer_wgvpn_user_vpn_2", "peer_wgvpn_user_vpn_3"]
    assert peers[0]["allowed_address"] == "10.21.100.2/32,2001:db8:10:0:10:21:64:2/128"
    assert peers[0]["is_responder"] == "true" and "responder" not in peers[0]
    assert (peers[0]["disabled"], peers[1]["disabled"]) == ("false", "true")
    assert "persistent_keepalive" not in peers[0]

    assert _by_comment(config, "ip_wgvpn_user_vpn_10.21.100.1")["address"] == "10.21.100.1/24"
    assert _by_comment(config, "ipv6_wgvpn_user_vpn_2001:db8:10:0:10:21:64:1")["address"].endswith("/112")

    secrets = json.loads((secrets_dir / "secrets.json").read_text())
    tunnel_secrets = secrets["dev1_wgvpn_1"]
    assert set(tunnel_secrets) == {"server_private", "server_public", "preshared_key", "client_private_2",
                                   "client_public_2", "client_private_3", "client_public_3"}
    assert peers[1]["public_key"] == tunnel_secrets["client_public_3"]
    assert (secrets_dir / "vpnconfig" / "dev1_user_vpn").is_dir()
    assert not list((secrets_dir / "vpnconfig" / "dev1_user_vpn").iterdir())


def test_secrets_are_reused_between_runs(device_factory, secrets_dir):
    (secrets_dir / "secrets.json").write_text("{}")
    device = _device(device_factory, [_tunnel()])
    first = mikro_wg.load_config(device)
    second = mikro_wg.load_config(device)
    assert _by_comment(first, "int_w_vpn_user_vpn")["private_key"] == _by_comment(second, "int_w_vpn_user_vpn")["private_key"]


def test_admin_tunnel_files_and_qr(device_factory, secrets_dir):
    (secrets_dir / "secrets.json").write_text("{}")
    tunnel = _tunnel(name="admin_vpn", admin=True, persistent_keepalive_enable=True, number_client=3)
    device = _device(device_factory, [tunnel], save_wg_files=True, api_version=720)

    config = mikro_wg.load_config(device)

    for comment in ["fw_v4_forward_vpn_admin_in_admin_vpn", "fw_v4_input_vpn_admin_in_admin_vpn",
                    "fw_v6_forward_vpn_admin_in_admin_vpn", "fw_v6_input_vpn_admin_in_admin_vpn"]:
        _by_comment(config, comment)
    assert _by_comment(config, "list_item_int_w_vpn_admin_vpn")["list"] == "list_wg_vpn_admins"
    peer = _by_comment(config, "peer_wgvpn_admin_vpn_2")
    assert peer["responder"] == "true" and peer["persistent_keepalive"] == "25s"

    folder = secrets_dir / "vpnconfig" / "dev1_admin_vpn"
    client = (folder / "ADM_site1_2.conf").read_text()
    assert "Address = 10.21.100.2/24,2001:db8:10:0:10:21:64:2/112" in client
    assert "Endpoint = 198.51.100.1:30001" in client and "PersistentKeepalive = 25" in client
    assert (folder / "ADM_site1_2.png").stat().st_size > 0


def test_user_tunnel_files(device_factory, secrets_dir):
    (secrets_dir / "secrets.json").write_text("{}")
    device = _device(device_factory, [_tunnel(number_client=3)], save_wg_files=True)
    mikro_wg.load_config(device)
    assert (secrets_dir / "vpnconfig" / "dev1_user_vpn" / "USR_site1_2.conf").exists()


def test_mgmt_tunnel_uses_local_prefix_and_onboarding(device_factory, secrets_dir):
    (secrets_dir / "secrets.json").write_text("{}")
    (secrets_dir / "mgmt_export").mkdir()
    tunnel = _tunnel(name="mgmt_vpn", admin=True, mgmt_vpn=True, persistent_keepalive_enable=True, number_client=3)
    device = _device(device_factory, [tunnel], save_wg_files=True)

    config = mikro_wg.load_config(device)

    for comment in ["local_auto__int_w_vpn_mgmt_vpn", "fw_v4_input_vpn_mgmt_in_mgmt_vpn", "fw_v6_input_vpn_mgmt_in_mgmt_vpn",
                    "local_auto__list_item_int_w_vpn_mgmt_vpn", "local_auto__fw_in_w_vpn_mgmt_vpn",
                    "local_auto__fwv6_in_w_vpn_mgmt_vpn", "local_auto__peer_wgvpn_mgmt_vpn_2",
                    "local_auto__ip_wgvpn_mgmt_vpn_10.21.100.1",
                    "local_auto__ipv6_wgvpn_mgmt_vpn_2001:db8:10:0:10:21:64:1"]:
        _by_comment(config, comment)

    assert (secrets_dir / "vpnconfig" / "dev1_mgmt_vpn" / "MGMT_site1_2.conf").exists()
    onboarding = (secrets_dir / "mgmt_export" / "mikro_mgmt_2.txt").read_text()
    assert "int_w_vpn_mgmt_vpn" in onboarding and "10.21.100.2/24" in onboarding
    # the certificates of the device domain and the management hosts of MGMT_HOSTS
    assert "certificate/import file-name=radius.example.int.crt" in onboarding
    assert "add address=192.0.2.200 comment=local_auto_ACL4_ONBOARD_MGMT" in onboarding
    assert "add address=192.0.2.201 comment=local_auto_ACL4_ONBOARD_MGMT" in onboarding
    # every object of the new router carries the protected prefix, so a later push keeps the tunnel
    for comment in ["comment=local_auto_mgmt_vpn_mgmt_vpn", "comment=local_auto_peer_wgvpn_mgmt_vpn_2",
                    "comment=local_auto_ip_wgvpn_mgmt_vpn_2", "comment=local_auto_script_PORT_RANDOM_WG_MGMT_2"]:
        assert comment in onboarding
    assert "allowed-address=0.0.0.0/0,::/0 " in onboarding


def test_onboarding_uses_the_configured_local_prefix(device_factory, secrets_dir, monkeypatch):
    monkeypatch.setattr(mikro_wg, "list_localstring", ["local_custom_"])
    (secrets_dir / "secrets.json").write_text("{}")
    (secrets_dir / "mgmt_export").mkdir()
    tunnel = _tunnel(name="mgmt_vpn", admin=True, mgmt_vpn=True, persistent_keepalive_enable=True, number_client=3)
    mikro_wg.load_config(_device(device_factory, [tunnel], save_wg_files=True))
    onboarding = (secrets_dir / "mgmt_export" / "mikro_mgmt_2.txt").read_text()
    assert "local_auto_" not in onboarding
    assert "comment=local_custom_peer_wgvpn_mgmt_vpn_2" in onboarding


def test_missing_secrets_file_is_created_empty_and_fails_to_parse(device_factory, secrets_dir):
    # The file is created empty, which is not valid json. In the real flow create_files()
    # writes "{}" first, so this only happens when the configlet is used on its own.
    device = _device(device_factory, [_tunnel()])
    with pytest.raises(json.JSONDecodeError):
        mikro_wg.load_config(device)
    assert (secrets_dir / "secrets.json").read_text() == ""
