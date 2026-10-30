import logging
from slugify import slugify

netbox_tag='rp-network-automation'

#Page size used when reading full endpoints (NetBox MAX_PAGE_SIZE defaults to 1000)
PAGE_SIZE = 1000

#-----------CACHE
#Each endpoint is read once with a single paginated .all() and indexed in memory, so the
#lookups below do not hit the API for every item. netbox_api.sync_resources invalidates
#the endpoint after writing to it.

_cache = {}
_indexes = {}


def fetch_all(nb, module, resource_type):
    key = (id(nb), module, resource_type)
    if key not in _cache:
        endpoint = getattr(getattr(nb, module), resource_type)
        _cache[key] = list(endpoint.all(limit=PAGE_SIZE))
    return _cache[key]

def invalidate(nb, module, resource_type):
    key = (id(nb), module, resource_type)
    _cache.pop(key, None)
    for index_key in [k for k in _indexes if k[:3] == key]:
        del _indexes[index_key]

def clear_cache():
    _cache.clear()
    _indexes.clear()

def _find(nb, module, resource_type, field, value):
    key = (id(nb), module, resource_type, field)
    if key not in _indexes:
        index = {}
        for record in fetch_all(nb, module, resource_type):
            #First match wins, as .get() would return it
            index.setdefault(getattr(record, field, None), record)
        _indexes[key] = index
    return _indexes[key].get(value)


#-----------NETBOX

def get_interface_id_from_name(nb, interface_name):
    interface = _find(nb, 'dcim', 'interfaces', 'name', interface_name)

    if interface:
        return interface.id
    else:
        logging.debug(f"interface with name '{interface_name}' not found.")
        return None

def get_vlan_vid_from_name(nb, vlan_name):
    vlan = _find(nb, 'ipam', 'vlans', 'name', vlan_name)

    if vlan:
        return vlan.id
    else:
        logging.info(f"vlan with name '{vlan_name}' not found.")
        return None

def get_device_from_name(nb, device_name):
    device = _find(nb, 'dcim', 'devices', 'name', device_name)

    if device:
        return device.id
    else:
        logging.info(f"device with name '{device_name}' not found.")
        return None

def get_device_role_id_from_slug(nb, device_role_slug):
    device_role = _find(nb, 'dcim', 'device_roles', 'slug', device_role_slug)

    if device_role:
        return device_role.id
    else:
        logging.info(f"device_role with slug '{device_role_slug}' not found.")
        return None

def get_device_type_id_from_slug(nb, device_type_slug):
    device_type = _find(nb, 'dcim', 'device_types', 'slug', device_type_slug)

    if device_type:
        return device_type.id
    else:
        logging.info(f"device_type_id with slug '{device_type_slug}' not found.")
        return None

def get_region_id_from_name(nb, region_name):
    if not region_name:
        return None
    region_slug =slugify(region_name)
    region = _find(nb, 'dcim', 'regions', 'slug', region_slug)

    if region:
        return region.id
    else:
        logging.info(f"Region with slug '{region_slug}' not found.")
        return None

def get_role_id_from_name(nb, role_name):
    if not role_name:
        return None
    role_slug =slugify(role_name)
    role = _find(nb, 'dcim', 'device_roles', 'slug', role_slug)

    if role:
        return role.id
    else:
        logging.info(f"role with slug '{role_slug}' not found.")
        return None

def get_asn_id_from_number(nb, asn_number):
    try:
        asn_number = int(asn_number)
    except (TypeError, ValueError):
        pass
    asn = _find(nb, 'ipam', 'asns', 'asn', asn_number)

    if asn:
        return asn.id
    else:
        logging.info(f"ASN with number '{asn_number}' not found.")
        return None

def get_rir_id_from_slug(nb, my_slug):
    rir = _find(nb, 'ipam', 'rirs', 'slug', my_slug)
    if rir:
        return rir.id
    else:
        logging.info(f"RIR with slug '{my_slug}' not found.")
        return None

def get_site_id_from_slug(nb, my_slug):
    site = _find(nb, 'dcim', 'sites', 'slug', my_slug)
    if site:
        return site.id
    else:
        logging.info(f"Site with slug '{my_slug}' not found.")
        return None

def get_site_groups_id_from_slug(nb, my_slug):
    site_group = _find(nb, 'dcim', 'site_groups', 'slug', my_slug)
    if site_group:
        return site_group.id
    else:
        logging.info(f"Site group with slug '{my_slug}' not found.")
        return None

def get_tag_by_slug(nb, tag_slug):
    tag = _find(nb, 'extras', 'tags', 'slug', slugify(tag_slug))

    if tag:
        logging.debug(f"Tag found: {tag.name} (ID: {tag.id})")
        return tag
    else:
        logging.warning(f"No tag found with slug '{tag_slug}'.")
        return None
