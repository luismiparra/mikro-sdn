"""In-memory test doubles for the external systems the project talks to."""

import copy
import itertools


class FakeRouterOsError(Exception):
    pass


class FakeResource:
    """Behaves like routeros_api RouterOsResource for the calls the project makes.

    Keyword arguments arrive with underscores and are stored with dashes, as RouterOS
    returns them, so the underscore/dash handling of needAnUpdate is exercised.
    """

    def __init__(self, router, path):
        self.router = router
        self.path = path

    @property
    def _items(self):
        return self.router.state.setdefault(self.path, [])

    def _fail_if_configured(self, operation):
        error = self.router.failures.get((self.path, operation)) or self.router.failures.get((self.path, "*"))
        if error:
            raise error

    def get(self, **filters):
        self._fail_if_configured("get")
        self.router.calls.append(("get", self.path, filters))
        items = self._items
        if filters:
            items = [item for item in items if all(item.get(key) == value for key, value in filters.items())]
        return copy.deepcopy(items)

    def add(self, **values):
        self._fail_if_configured("add")
        self.router.calls.append(("add", self.path, dict(values)))
        record = {key.replace("_", "-"): value for key, value in values.items()}
        record["id"] = self.router.next_id()
        self._items.append(record)
        return record["id"]

    def set(self, **values):
        self._fail_if_configured("set")
        self.router.calls.append(("set", self.path, dict(values)))
        values = dict(values)
        target_id = values.pop("id", None)
        changes = {key.replace("_", "-"): value for key, value in values.items()}
        if target_id is None:
            # Singleton menus (/ip/dns, /snmp, ...) are set without an id
            if self._items:
                self._items[0].update(changes)
            else:
                self._items.append(dict(changes, id=self.router.next_id()))
            return
        for item in self._items:
            if item["id"] == target_id:
                item.update(changes)
                return
        self._items.append(dict(changes, id=target_id))

    def remove(self, id):
        self._fail_if_configured("remove")
        self.router.calls.append(("remove", self.path, {"id": id}))
        self.router.state[self.path] = [item for item in self._items if item["id"] != id]

    def call(self, command, arguments):
        self._fail_if_configured("call")
        self.router.calls.append(("call", self.path, {"command": command, **arguments}))
        if command == "move":
            items = self._items
            moving = next(item for item in items if item["id"] == arguments["numbers"])
            items.remove(moving)
            items.insert(int(arguments["destination"]), moving)


class FakeRouterOsApi:
    """A router: resources by path, the calls made to them and optional failures."""

    def __init__(self, state=None, failures=None):
        self.state = copy.deepcopy(state) if state else {}
        self.failures = failures or {}
        self.calls = []
        self._ids = itertools.count(1)

    def next_id(self):
        return f"*{next(self._ids):X}"

    def get_resource(self, path):
        return FakeResource(self, path)

    def writes(self):
        return [call for call in self.calls if call[0] in ("add", "set", "remove", "call")]

    def by_comment(self, path, comment):
        for item in self.state.get(path, []):
            if item.get("comment") == comment:
                return item
        return None


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class FakeTag(dict):
    """pynetbox exposes tags as dicts with name/slug."""


class FakeRecord:
    """A pynetbox record: attributes, tags, update() and delete()."""

    def __init__(self, endpoint, **fields):
        self._endpoint = endpoint
        self.tags = fields.pop("tags", [])
        self.__dict__.update(fields)
        self.updated_with = None
        self.deleted = False

    def serialize(self):
        """Flat view as pynetbox gives it: nested objects (tags) by id."""
        data = {key: value for key, value in self.__dict__.items()
                if not key.startswith("_") and key not in ("updated_with", "deleted")}
        data["tags"] = [t.get("id") for t in self.tags]
        return data

    def update(self, data):
        if self._endpoint.fail_on.get("update"):
            raise RuntimeError("update failed")
        self.updated_with = data
        self.__dict__.update({key: value for key, value in data.items() if key != "tags"})
        return True

    def delete(self):
        if self._endpoint.fail_on.get("delete"):
            raise RuntimeError("delete failed")
        self.deleted = True
        self._endpoint.records.remove(self)
        return True


class FakeEndpoint:
    def __init__(self, nb=None):
        self.records = []
        self.created = []
        self.fail_on = {}
        self.calls = []
        self._nb = nb
        self._ids = itertools.count(1)

    def add(self, **fields):
        fields.setdefault("id", next(self._ids))
        record = FakeRecord(self, **fields)
        self.records.append(record)
        return record

    def get(self, **filters):
        if self.fail_on.get("get"):
            raise RuntimeError("get failed")
        for record in self.records:
            if all(getattr(record, key, None) == value for key, value in filters.items()):
                return record
        return None

    def all(self, limit=None):
        self.calls.append(("all", None))
        return list(self.records)

    def create(self, data):
        if isinstance(data, list):
            self.calls.append(("create", len(data)))
            fail = self.fail_on.get("create")
            if fail is True or (callable(fail) and any(fail(item) for item in data)):
                raise RuntimeError("create failed")
            return [self._create_one(item) for item in data]
        self.calls.append(("create", 1))
        if self.fail_on.get("create"):
            raise RuntimeError("create failed")
        return self._create_one(data)

    def _create_one(self, data):
        self.created.append(data)
        fields = {key: value for key, value in data.items() if key != "tags"}
        fields["tags"] = [self._resolve_tag(t) for t in data.get("tags", [])]
        return self.add(**fields)

    def _resolve_tag(self, tag_id):
        # NetBox answers tag ids with the tag object (name/slug)
        for record in (self._nb.extras.tags.records if self._nb else []):
            if record.id == tag_id:
                return FakeTag(id=record.id, name=record.name, slug=record.slug)
        return FakeTag(id=tag_id)

    def update(self, objects):
        """Bulk update: list of dicts with id."""
        self.calls.append(("update", len(objects)))
        if self.fail_on.get("update"):
            raise RuntimeError("update failed")
        by_id = {record.id: record for record in self.records}
        for item in objects:
            record = by_id[item["id"]]
            record.updated_with = item
            record.__dict__.update({key: value for key, value in item.items() if key != "tags"})
        return True

    def delete(self, objects):
        """Bulk delete: list of ids."""
        self.calls.append(("delete", len(objects)))
        if self.fail_on.get("delete"):
            raise RuntimeError("delete failed")
        ids = set(objects)
        for record in [r for r in self.records if r.id in ids]:
            record.deleted = True
            self.records.remove(record)
        return True


class FakeApp:
    def __init__(self, nb=None):
        self._endpoints = {}
        self._nb = nb

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._endpoints.setdefault(name, FakeEndpoint(self._nb))


class FakeNetbox:
    """Enough of pynetbox.api for the project: nb.<app>.<endpoint>.get/all/create."""

    def __init__(self):
        self.dcim = FakeApp(self)
        self.ipam = FakeApp(self)
        self.extras = FakeApp(self)


def tag(name, slug=None, id=None):
    from slugify import slugify
    return FakeTag(name=name, slug=slug or slugify(name), id=id)
