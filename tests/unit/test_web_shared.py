import pytest
import yaml

import web_shared
from fakes import FakeResponse

DEVICE = {"name": "dev1", "mgmt_int": "10.0.0.1"}


def test_load_control_reads_control_file():
    control = web_shared.loadControl()
    assert control["mgmt_allow_subnet"] == "10.21.100.0/24"


def test_load_inventory_sets_role_and_skips_other_files(tmp_path, monkeypatch):
    (tmp_path / "inventory").mkdir()
    (tmp_path / "inventory" / "b.yml").write_text(yaml.dump({"edge": [{"name": "e1"}]}))
    (tmp_path / "inventory" / "a.yml").write_text(yaml.dump({"core": [{"name": "c1"}]}))
    (tmp_path / "inventory" / ".DS_Store").write_text("x")
    monkeypatch.setattr(web_shared, "pathconfig", str(tmp_path))
    assert [(d["name"], d["role"]) for d in web_shared.load_inventory()] == [("c1", "core"), ("e1", "edge")]


def test_get_item(monkeypatch):
    seen = {}

    def get(url, auth, verify):
        seen.update(url=url, auth=auth)
        return FakeResponse(200, [{"x": 1}])

    monkeypatch.setattr(web_shared.requests, "get", get)
    assert web_shared.getItem(DEVICE, "/ip/address") == [{"x": 1}]
    assert seen["url"] == "https://10.0.0.1/rest/ip/address"
    assert seen["auth"] == (web_shared.micro_user, web_shared.micro_pass)


def _boom(*args, **kwargs):
    raise ConnectionError("unreachable")


@pytest.mark.parametrize("method, call", [
    ("post", lambda: web_shared.postItem(DEVICE, "/r", {"a": 1})),
    ("patch", lambda: web_shared.patchItem(DEVICE, "/r", {"a": 1}, "*1")),
    ("put", lambda: web_shared.putItem(DEVICE, "/r", {"a": 1})),
    ("delete", lambda: web_shared.deleteItem(DEVICE, "/r", "*1")),
])
def test_write_methods(monkeypatch, method, call):
    seen = {}

    def fake(url, **kwargs):
        seen.update(url=url, **kwargs)
        return FakeResponse(200, {"ok": True})

    monkeypatch.setattr(web_shared.requests, method, fake)
    assert call() == {"ok": True}
    assert seen["url"].startswith("https://10.0.0.1/rest/r")
    assert seen["headers"] == {"content-type": "application/json"} and seen["verify"] is False
    if method in ("patch", "delete"):
        assert seen["url"].endswith("/*1")
    if method != "delete":
        assert seen["data"] == '{"a": 1}'

    monkeypatch.setattr(web_shared.requests, method, lambda *a, **k: FakeResponse(400, {"error": "bad"}))
    assert call() is False

    monkeypatch.setattr(web_shared.requests, method, _boom)
    assert call() is False


def test_get_item_errors(monkeypatch):
    monkeypatch.setattr(web_shared.requests, "get", lambda *a, **k: FakeResponse(404))
    assert web_shared.getItem(DEVICE, "/r") is False
    monkeypatch.setattr(web_shared.requests, "get", _boom)
    assert web_shared.getItem(DEVICE, "/r") is False
