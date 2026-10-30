import os
import runpy
import sys

import pytest

import mikro_ports

PORTS_PATH = os.path.join(os.path.dirname(mikro_ports.__file__), "mikro_ports.py")


def _inventory(device_factory):
    return [
        device_factory(name="core1", role="core", wan_order=0, subnetv4="10.81.0.0/16"),
        device_factory(name="core2", role="core", wan_order=1, subnetv4="10.82.0.0/16"),
        device_factory(name="edge1", role="edge", wan_order=2, subnetv4="10.83.0.0/16"),
        device_factory(name="off", role="edge", wan_order=3, enabled=False),
        device_factory(name="lonely", role="other", wan_order=4),
    ]


def test_collect_one_row_per_link_end(device_factory):
    rows = mikro_ports.collect(_inventory(device_factory))

    assert len(rows) == 6
    core_link = [r for r in rows if {r["device"], r["peer"]} == {"core1", "core2"}]
    assert {r["transit_ip"] for r in core_link} == {"10.81.250.1/30", "10.81.250.2/30"}
    edge_side = next(r for r in rows if r["device"] == "edge1" and r["peer"] == "core2")
    assert edge_side == {"device": "edge1", "peer": "core2", "slot": 1, "listen_port": 51821,
                         "peer_port": 51821, "transit_ip": "10.83.250.5/30"}


def test_report_lists_devices_in_wan_order(device_factory, capsys):
    inventory = _inventory(device_factory)
    mikro_ports.report(mikro_ports.collect(inventory), inventory, None)
    out = capsys.readouterr().out
    assert out.index("core1  (wan_order 0)") < out.index("core2  (wan_order 1)") < out.index("edge1  (wan_order 2)")
    assert "lonely" not in out


def test_report_single_device_and_unknown_device(device_factory, capsys):
    inventory = _inventory(device_factory)
    rows = mikro_ports.collect(inventory)
    mikro_ports.report(rows, inventory, "edge1")
    out = capsys.readouterr().out
    assert "edge1" in out and "core1  (wan_order" not in out

    mikro_ports.report(rows, inventory, "ghost")
    assert "Device not found in inventory -> ghost" in capsys.readouterr().out


def test_report_csv_sorted(device_factory, capsys):
    mikro_ports.report_csv(mikro_ports.collect(_inventory(device_factory)))
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "device,peer,slot,listen_port,peer_port,transit_v4"
    assert lines[1].startswith("core1,core2,0,51820,51820,")
    assert len(lines) == 7


# ---------------------------------------------------------------- command line over the lab config

def _run(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["mikro_ports.py", *args])
    runpy.run_path(PORTS_PATH, run_name="__main__")


def test_cli_text_report(monkeypatch, capsys, config_dir):
    _run(monkeypatch, "lab-mikro4")
    out = capsys.readouterr().out
    assert "lab-mikro4  (wan_order 3)" in out and "lab-mikro1" in out


def test_cli_csv_report(monkeypatch, capsys, config_dir):
    _run(monkeypatch, "csv")
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("device,peer") and len(lines) > 10


def test_cli_requires_config(monkeypatch):
    monkeypatch.delenv("CONFIG")
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    with pytest.raises(SystemExit, match="CONFIG not set"):
        _run(monkeypatch)
