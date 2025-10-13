# 💾 Block Storage Service Patterns (`blockstorage`)

## Client Creation

```python
blockstorage_client = get_client('blockstorage', oci_config)
```

## Common Patterns

### 1. List All Volumes

```python
for compartment in all_compartments:
    try:
        response = blockstorage_client.list_volumes(compartment_id=compartment.id)
        for volume in response.data:
            results.append(to_dict(volume))

        while response.has_next_page:
            response = blockstorage_client.list_volumes(compartment_id=compartment.id, page=response.next_page)
            for volume in response.data:
                results.append(to_dict(volume))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Available Volumes (Unattached)

```python
for compartment in all_compartments:
    try:
        response = blockstorage_client.list_volumes(
            compartment_id=compartment.id,
            lifecycle_state='AVAILABLE'
        )
        for volume in response.data:
            results.append(to_dict(volume))

        while response.has_next_page:
            response = blockstorage_client.list_volumes(
                compartment_id=compartment.id,
                lifecycle_state='AVAILABLE',
                page=response.next_page
            )
            for volume in response.data:
                results.append(to_dict(volume))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Volume Backups

```python
for compartment in all_compartments:
    try:
        response = blockstorage_client.list_volume_backups(compartment_id=compartment.id)
        for backup in response.data:
            results.append(to_dict(backup))

        while response.has_next_page:
            response = blockstorage_client.list_volume_backups(compartment_id=compartment.id, page=response.next_page)
            for backup in response.data:
                results.append(to_dict(backup))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Volume Groups

```python
for compartment in all_compartments:
    try:
        response = blockstorage_client.list_volume_groups(compartment_id=compartment.id)
        for volume_group in response.data:
            results.append(to_dict(volume_group))

        while response.has_next_page:
            response = blockstorage_client.list_volume_groups(compartment_id=compartment.id, page=response.next_page)
            for volume_group in response.data:
                results.append(to_dict(volume_group))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Boot Volumes

```python
for compartment in all_compartments:
    try:
        response = blockstorage_client.list_boot_volumes(compartment_id=compartment.id)
        for boot_volume in response.data:
            results.append(to_dict(boot_volume))

        while response.has_next_page:
            response = blockstorage_client.list_boot_volumes(compartment_id=compartment.id, page=response.next_page)
            for boot_volume in response.data:
                results.append(to_dict(boot_volume))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state='AVAILABLE'` for unattached volumes
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Volume backups are separate from volumes
- Boot volumes are different from regular volumes


