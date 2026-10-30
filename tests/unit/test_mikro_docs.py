import json

import mikro_docs


def test_dry_run_add_and_save_masks_secrets(web_dir):
    mikro_docs.dry_run_add("- ADD {'private_key': 'abc', 'password': 'pw', 'secret': 's3', 'name': 'x'}\n")
    mikro_docs.savedry_run()

    markdown = (web_dir / "Changes.md").read_text()
    assert "abc" not in markdown and "pw'" not in markdown and "s3" not in markdown
    assert markdown.count("XXX_KEY_REMOVED_XXX") == 3
    html = (web_dir / "Changes.html").read_text()
    assert "<title>LAB NETWORK AUTOMATION</title>" in html and "XXX_KEY_REMOVED_XXX" in html


def test_bindzone_generator_and_getters():
    config = [
        {"resource": "/ip/address", "interface": "vlan_1", "address": "10.71.1.1/24"},
        {"resource": "/ip/address", "interface": "vlan_1", "address": "10.71.1.2/24"},
        {"resource": "/ipv6/address", "interface": "vlan_1", "address": "2001:db8::1/64"},
    ]
    mikro_docs.bindzoneGenerator(config, {"name": "dev_1", "domain": "example.int"})

    a_records = mikro_docs.get_globalbind_str_a()
    assert a_records.count(" A ") == 1 and "vlan-1-dev-1" in a_records and "10.71.1.1" in a_records
    ptr = mikro_docs.get_globalbind_str_ptr()
    # reverse of the last three octets, for a /8 zone
    assert "1.1.71 \t IN" in ptr and "2.1.71 \t IN" in ptr and "_" not in ptr
    # the PTR names are in the zone of the device domain
    assert "vlan-1-dev-1.example.int." in ptr


def test_save_global_writes_bind_and_docs(web_dir):
    mikro_docs.globalbind_str_a = "a-record"
    mikro_docs.globalbind_str_ptr = "ptr-record"
    mikro_docs.global_doc_md = "# Title\n"
    mikro_docs.save_global()
    assert (web_dir / "bind_A.txt").read_text() == "a-record"
    assert (web_dir / "bind_PTR.txt").read_text() == "ptr-record"
    assert (web_dir / "Global.md").read_text() == "# Title\n"
    assert "<h1>Title</h1>" in (web_dir / "Global.html").read_text()


def test_doc_generator_builds_one_table_per_resource():
    config = [
        {"resource": "/ip/address", "address": "1.1.1.1/32", "comment": "a", "private_key": "hidden"},
        {"resource": "/ip/address", "address": "2.2.2.2/32", "interface": "lo"},
        {"resource": "/system/scheduler", "name": "skipped"},
    ]
    doc = mikro_docs.docGenerator(config, "General", ["resource", "private_key"], False)
    assert doc.startswith("## General")
    assert doc.count("### /ip/address") == 1
    assert "address|comment|interface|" in doc
    assert "|1.1.1.1/32|a| - |" in doc and "|2.2.2.2/32| - |lo|" in doc
    assert "hidden" not in doc and "scheduler" not in doc


def test_doc_generator_external_only_has_title():
    assert mikro_docs.docGenerator([{"resource": "/x"}], "External", [], True) == "## External  \n  \n"


def test_create_docs_writes_device_pages_and_accumulates(secrets_dir, web_dir):
    (secrets_dir / "proposed").mkdir()
    (secrets_dir / "proposed" / "dev1_global.json").write_text(json.dumps([
        {"resource": "/ip/address", "interface": "lo", "address": "10.0.0.1/32", "comment": "lo"}]))
    (secrets_dir / "proposed" / "dev1_fw.json").write_text(json.dumps([
        {"resource": "/ip/firewall/filter", "comment": "fw1", "chain": "input"}]))

    mikro_docs.createDocs({"name": "dev1", "domain": "example.int"})

    markdown = (web_dir / "dev1.md").read_text()
    assert markdown.startswith("#DEVICE: dev1") and "### /ip/firewall/filter" in markdown
    assert "<table>" in (web_dir / "dev1.html").read_text()
    assert mikro_docs.global_doc_md == markdown
    assert "lo-dev1" in mikro_docs.globalbind_str_a


def test_create_external_writes_markdown_and_html(secrets_dir):
    (secrets_dir / "external").mkdir()
    (secrets_dir / "external" / "external.json").write_text("{}")
    mikro_docs.create_external()
    assert (secrets_dir / "external" / "external.md").read_text().startswith("## ExternalConfig")
    assert "<h2>ExternalConfig</h2>" in (secrets_dir / "external" / "external.html").read_text()


def _connection(name, remote4, remote6):
    return {
        "connection": name,
        "wireguard_interface": {"name": f"int_{name}", "listen_port": "51820", "private_key": "PRIV", "mtu": "1280"},
        "ip_address": {"address": "10.0.0.1/30"},
        "ipv6_address": {"address": "fd00::1/127"},
        "wireguard_peer": {"public_key": "PUB", "preshared_key": "PSK", "allowed_address": "0.0.0.0/0,::/0",
                           "endpoint_address": "core.example.com", "endpoint_port": "51821",
                           "persistent_keepalive": "10s"},
        "ipv4_bgp_config": {"as": "65300", "router-id": "10.91.1.1", "remote.address": remote4, "remote.as": "65101"},
        "ipv6_bgp_config": {"remote.address": remote6, "remote.as": "65101"},
    }


def test_external_files_writes_wireguard_and_frr(secrets_dir):
    (secrets_dir / "external_export").mkdir()
    data = {"ext1": {"c1": _connection("c1", "10.0.0.2", "fd00::2"), "c2": _connection("c2", "10.70.1.2", "fd00:1::2")}}

    mikro_docs.external_files(data)

    wg = (secrets_dir / "external_export" / "wg_ext1_c1.conf").read_text()
    assert "Address = 10.0.0.1/30,fd00::1/127" in wg
    assert "Endpoint = core.example.com:51821" in wg and "PersistentKeepalive = 10\n" in wg
    frr = (secrets_dir / "external_export" / "frr_ext1.conf").read_text()
    assert "router bgp 65300" in frr and " bgp router-id 10.91.1.1" in frr
    assert " neighbor 10.70.1.2 remote-as 65101" in frr
    assert "  no neighbor fd00::2 activate" in frr and "  neighbor fd00:1::2 route-map meshv6 out" in frr
