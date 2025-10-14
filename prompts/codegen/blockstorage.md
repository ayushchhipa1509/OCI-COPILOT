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

### 5. Create Action: `create_volume`

When the plan action is `create_volume`, you must generate code to create a Block Volume.

```python
from oci.util import to_dict

# Create Block Storage client
blockstorage_client = get_client('blockstorage', oci_config)

# Extract details from the plan's params
compartment_id = plan['params'].get('compartment_id')
display_name = plan['params'].get('display_name')
availability_domain = plan['params'].get('availability_domain')
size_in_gbs = plan['params'].get('size_in_gbs')

# Define the details for the new volume
create_volume_details = oci.core.models.CreateVolumeDetails(
    compartment_id=compartment_id,
    display_name=display_name,
    availability_domain=availability_domain,
    size_in_gbs=size_in_gbs
    # NOTE: CIS Benchmark 5.2.1 recommends using a Customer-Managed Key (CMK) for encryption.
    # This can be added via the 'kms_key_id' parameter if a key OCID is provided.
)

# Create the volume
created_volume_response = blockstorage_client.create_volume(
    create_volume_details=create_volume_details
)

# Append the created resource details (as a dictionary) to the results
results.append(to_dict(created_volume_response.data))
```
