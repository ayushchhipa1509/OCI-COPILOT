# 🖥️ Compute Service Patterns (`compute`)

## Client Creation

```python
compute_client = get_client('compute', oci_config)
# For network-related tasks, also create:
network_client = get_client('virtualnetwork', oci_config)
```

## Common Patterns

### 1. List All Instances

```python
for compartment in all_compartments:
    try:
        response = compute_client.list_instances(compartment_id=compartment.id)
        for instance in response.data:
            results.append(to_dict(instance))

        while response.has_next_page:
            response = compute_client.list_instances(compartment_id=compartment.id, page=response.next_page)
            for instance in response.data:
                results.append(to_dict(instance))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Instances with Public IP (Multi-step)

```python
for compartment in all_compartments:
    try:
        # Get all instances
        response = compute_client.list_instances(compartment_id=compartment.id)
        all_instances = response.data
        while response.has_next_page:
            response = compute_client.list_instances(compartment_id=compartment.id, page=response.next_page)
            all_instances.extend(response.data)

        # Check each instance for public IP
        for instance in all_instances:
            vnic_attachments = compute_client.list_vnic_attachments(
                compartment_id=instance.compartment_id,
                instance_id=instance.id
            ).data

            public_ips = []
            for vnic_attachment in vnic_attachments:
                vnic = network_client.get_vnic(vnic_attachment.vnic_id).data
                if vnic and vnic.public_ip:
                    public_ips.append(vnic.public_ip)

            if public_ips:
                instance_dict = to_dict(instance)
                instance_dict['public_ips'] = public_ips
                results.append(instance_dict)

    except oci.exceptions.ServiceError:
        continue
```

### 3. List Running Instances

```python
for compartment in all_compartments:
    try:
        response = compute_client.list_instances(
            compartment_id=compartment.id,
            lifecycle_state='RUNNING'
        )
        for instance in response.data:
            results.append(to_dict(instance))

        while response.has_next_page:
            response = compute_client.list_instances(
                compartment_id=compartment.id,
                lifecycle_state='RUNNING',
                page=response.next_page
            )
            for instance in response.data:
                results.append(to_dict(instance))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Instance Shapes

```python
for compartment in all_compartments:
    try:
        response = compute_client.list_shapes(compartment_id=compartment.id)
        for shape in response.data:
            results.append(to_dict(shape))

        while response.has_next_page:
            response = compute_client.list_shapes(compartment_id=compartment.id, page=response.next_page)
            for shape in response.data:
                results.append(to_dict(shape))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Images

```python
for compartment in all_compartments:
    try:
        response = compute_client.list_images(compartment_id=compartment.id)
        for image in response.data:
            results.append(to_dict(image))

        while response.has_next_page:
            response = compute_client.list_images(compartment_id=compartment.id, page=response.next_page)
            for image in response.data:
                results.append(to_dict(image))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- For public IP detection, always use the VNIC attachment approach
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks


