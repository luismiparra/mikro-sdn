import ipaddress
import logging
from slugify import slugify
import netbox_get
import netbox_shared


#Objects sent per bulk request. NetBox runs each bulk request in one transaction
BULK_CHUNK = 250

#Result of every sync_resources call of the run, for the summary table of netbox_main
sync_results = []

#Key fields that hold IPs, normalised so "2001:db8::0001/64" and "2001:db8::1/64" are the same key
_NETWORK_KEYS = ('prefix',)
_INTERFACE_KEYS = ('address', 'start_address', 'end_address')


def _normalize_key(key_field, value):
    try:
        if key_field in _NETWORK_KEYS:
            return str(ipaddress.ip_network(value, strict=False))
        if key_field in _INTERFACE_KEYS:
            return str(ipaddress.ip_interface(value))
        if key_field == 'asn':
            return int(value)
    except (TypeError, ValueError):
        pass
    return value

def _same_value(current, desired):
    if isinstance(current, list) and isinstance(desired, list):
        try:
            return sorted(current) == sorted(desired)
        except TypeError:
            return current == desired
    #NetBox stores empty text fields as ""
    if current in (None, "") and desired in (None, ""):
        return True
    return current == desired

def _changes(record, desired):
    """Fields of desired that differ from the record. Fields the object does not have are ignored."""
    current = record.serialize()
    return {
        field: value for field, value in desired.items()
        if field in current
        and not _same_value(_normalize_key(field, current[field]), _normalize_key(field, value))
    }

def _tag_slugs(record):
    return [t['slug'] if isinstance(t, dict) else getattr(t, 'slug', None) for t in (record.tags or [])]

def _chunks(items):
    for i in range(0, len(items), BULK_CHUNK):
        yield items[i:i + BULK_CHUNK]

def _run_bulk(label, operation, items, describe):
    """Run operation over items in bulk chunks. If a chunk fails (NetBox rolls back the whole
    request) retry it item by item so one bad object does not block the rest."""
    done = 0
    for chunk in _chunks(items):
        try:
            operation(chunk)
            done += len(chunk)
            continue
        except Exception as e:
            logging.warning(f"Bulk {label} failed for {len(chunk)} items, retrying one by one: {e}")
        for item in chunk:
            try:
                operation([item])
                done += 1
            except Exception as e:
                logging.error(f"Error {label} -> {describe(item)}: {e}")
    return done


##------------generic sync function

def sync_resources(nb, module, resource_type, data_list, key_field, tag_to_check,
                   delete=True, update_untagged=False):
    """Make NetBox match data_list for one endpoint with the minimum number of requests.

    One paginated read of the endpoint, then bulk create / bulk update (only objects with
    changes, only the changed fields) / bulk delete (objects with tag_to_check that are no
    longer in data_list). Objects without tag_to_check are never updated or deleted unless
    update_untagged is set.
    """
    endpoint = getattr(getattr(nb, module), resource_type)
    tag_slug = slugify(tag_to_check)
    where = f"Module: {module} Resource: {resource_type} Key: {key_field}"

    #Desired state, deduplicated by key (last one wins, as consecutive create+update did)
    desired = {}
    for resource_data in data_list:
        desired[_normalize_key(key_field, resource_data.get(key_field))] = resource_data

    existing = {}
    for record in netbox_get.fetch_all(nb, module, resource_type):
        existing.setdefault(_normalize_key(key_field, getattr(record, key_field, None)), record)

    to_create = []
    to_update = []
    unchanged = 0
    for key, resource_data in desired.items():
        record = existing.get(key)
        if record is None:
            to_create.append(resource_data)
            continue
        if not update_untagged and tag_slug not in _tag_slugs(record):
            logging.warning(f"Exist already with another tag No update performed. -> {where} Item: {key} Tag: {tag_to_check}")
            continue
        changes = _changes(record, resource_data)
        if changes:
            to_update.append({'id': record.id, **changes})
            logging.info(f"Update -> {where} Item: {key} Fields: {sorted(changes)}")
        else:
            unchanged += 1

    to_delete = []
    if delete:
        for key, record in existing.items():
            if key not in desired and tag_slug in _tag_slugs(record):
                to_delete.append(record.id)
                logging.info(f"Delete -> {where} Item: {key} Tag: {tag_to_check}")

    for resource_data in to_create:
        logging.info(f"Create -> {where} Item: {resource_data.get(key_field)} Tag: {tag_to_check}")

    if netbox_shared.dry_run:
        logging.info(f"DRY RUN {module}.{resource_type}: create {len(to_create)} update {len(to_update)} delete {len(to_delete)} unchanged {unchanged}")
        result = {'created': 0, 'updated': 0, 'deleted': 0, 'unchanged': unchanged}
        sync_results.append((f"{module}.{resource_type}", result, (len(to_create), len(to_update), len(to_delete)), True))
        return result

    by_id = {record.id: key for key, record in existing.items()}
    result = {
        'created': _run_bulk('creating', endpoint.create, to_create,
                             lambda item: f"{where} Item: {item.get(key_field)}"),
        'updated': _run_bulk('updating', endpoint.update, to_update,
                             lambda item: f"{where} Item: {by_id.get(item['id'])}"),
        'deleted': _run_bulk('deleting', endpoint.delete, to_delete,
                             lambda item: f"{where} Item: {by_id.get(item)}"),
        'unchanged': unchanged,
    }
    if to_create or to_update or to_delete:
        netbox_get.invalidate(nb, module, resource_type)

    logging.info(f"NETBOX -> {module}.{resource_type}: created {result['created']}/{len(to_create)} "
                 f"updated {result['updated']}/{len(to_update)} deleted {result['deleted']}/{len(to_delete)} "
                 f"unchanged {unchanged}")
    sync_results.append((f"{module}.{resource_type}", result, (len(to_create), len(to_update), len(to_delete)), False))
    return result


##------------kept for compatibility, both run through sync_resources

def create_update_resources(nb, module, resource_type, data_list, key_field, tag_to_check):
    return sync_resources(nb, module, resource_type, data_list, key_field, tag_to_check, delete=False)

def remove_resources_not_in_list(nb, module, resource_type, data_list, key_field, tag_to_check):
    #Deletes only: everything that is in data_list is left as it is
    endpoint = getattr(getattr(nb, module), resource_type)
    tag_slug = slugify(tag_to_check)
    keys = {_normalize_key(key_field, item.get(key_field)) for item in data_list}
    to_delete = [record.id for record in netbox_get.fetch_all(nb, module, resource_type)
                 if _normalize_key(key_field, getattr(record, key_field, None)) not in keys
                 and tag_slug in _tag_slugs(record)]
    if netbox_shared.dry_run or not to_delete:
        return 0
    deleted = _run_bulk('deleting', endpoint.delete, to_delete, lambda item: f"{module}.{resource_type} id {item}")
    netbox_get.invalidate(nb, module, resource_type)
    return deleted


#----------- RESOURCES (build the desired objects, then sync them)

def sync_regions(nb, region_list):
    tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_tag)
    regions = [{"name": region, "slug": slugify(region), "tags": [tag.id]} for region in region_list]
    return sync_resources(nb, 'dcim', 'regions', regions, 'slug', netbox_shared.netbox_tag)

def sync_roles(nb, role_list):
    tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_global_tag)
    roles = []
    for role in role_list:
        match role:
            case "core":
                color = "b700ff"
            case "edge":
                color ="026e1f"
            case "external_edge":
                color ="02466e"
            case _:
                color = "9e9e9e"
        roles.append({"name": role, "slug": slugify(role), "tags": [tag.id], "color":color, "vm_role":False, "description": role})
    return sync_resources(nb, 'dcim', 'device_roles', roles, 'slug', netbox_shared.netbox_global_tag)

def sync_devices(nb, device_list):
    tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_tag)
    devices = []
    for device in device_list:
        if device.get('enabled'):
            status = "active"
        else:
            status = "staging"
        devices.append({
            "name": device.get('name'),
            "tags": [tag.id],
            "description": device.get('description'),
            "role": netbox_get.get_device_role_id_from_slug(nb, slugify(device.get('role'))),
            "device_type": netbox_get.get_device_type_id_from_slug(nb, device.get("netbox", {}).get("device", {}).get("device_model")),
            "site": netbox_get.get_site_id_from_slug(nb, slugify(device.get('location'))),
            'status': status,
            'serial': device.get('serial'),
        })
    return sync_resources(nb, 'dcim', 'devices', devices, 'name', netbox_shared.netbox_tag)

def sync_vlans(nb, vlan_list):
    tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_global_tag)
    vlans = [{"vid": vlan.get('id'), "name": vlan.get('name'), "tags": [tag.id], "status": "active",
              "description": f"{vlan.get('name')} - id - {vlan.get('id')}"} for vlan in vlan_list]
    return sync_resources(nb, 'ipam', 'vlans', vlans, 'name', netbox_shared.netbox_global_tag)

def sync_asns(nb, asn_list):
    return sync_resources(nb, 'ipam', 'asns', asn_list, 'asn', netbox_shared.netbox_tag)

def sync_sites(nb, site_list):
    #Sites are updated whatever their tag and never deleted
    return sync_resources(nb, 'dcim', 'sites', site_list, 'slug', netbox_shared.netbox_tag,
                          delete=False, update_untagged=True)


#----------- STATIC OBJECTS

def create_or_update_tag(nb, tag_name):
    tag_slug = slugify(tag_name)

    # First, check if the tag exists by slug
    existing_tag = netbox_get.get_tag_by_slug(nb, tag_name)

    if existing_tag:
        logging.debug(f"Tag '{tag_name}' already exists with ID {existing_tag.id}.")
        return existing_tag
    else:
        # Create a new tag if it doesn't exist
        new_tag_data = {
            "name": tag_name,
            "slug": tag_slug,
        }
        new_tag = nb.extras.tags.create(new_tag_data)
        netbox_get.invalidate(nb, 'extras', 'tags')
        logging.info(f"Tag '{tag_name}' created with ID {new_tag.id}.")
        return new_tag

def create_private_rir(nb):
    tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_global_tag)
    private_rir = {"name": "Private", "slug": "private", "is_private": True, "tags": [tag.id] }
    try:
        # Create the RIR in NetBox
        if not netbox_get.get_rir_id_from_slug(nb, private_rir["slug"]):
            private_rir = nb.ipam.rirs.create(private_rir)
            netbox_get.invalidate(nb, 'ipam', 'rirs')
            logging.info(f"Created private RIR: {private_rir}")
        else:
            logging.debug(f"Already exist private RIR: {private_rir}")

    except Exception as e:
        logging.info(f"Error creating private RIR: {e}")

def create_site_groups(nb):
    tag = netbox_get.get_tag_by_slug(nb, netbox_shared.netbox_global_tag)
    groups = [
        {"name": "site_prod", "slug": "site_prod", "description": "Production network", "tags": [tag.id] },
        {"name": "site_lab", "slug": "site_lab", "description": "Lab network", "tags": [tag.id] },
    ]
    missing = [group for group in groups if not netbox_get.get_site_groups_id_from_slug(nb, group['slug'])]
    if not missing:
        return
    try:
        nb.dcim.site_groups.create(missing)
        netbox_get.invalidate(nb, 'dcim', 'site_groups')
        logging.info(f"Created site groups: {[group['slug'] for group in missing]}")
    except Exception as e:
        logging.info(f"Error creating site group: {e}")
