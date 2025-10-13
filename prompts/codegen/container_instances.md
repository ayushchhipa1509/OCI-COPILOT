# 🐳 Container Instances Service Patterns (`container_instances`)

## Client Creation

```python
container_instances_client = get_client('container_instances', oci_config)
```

## Common Patterns

### 1. List Container Instances

```python
for compartment in all_compartments:
    try:
        response = container_instances_client.list_container_instances(compartment_id=compartment.id)
        for instance in response.data:
            results.append(to_dict(instance))

        while response.has_next_page:
            response = container_instances_client.list_container_instances(compartment_id=compartment.id, page=response.next_page)
            for instance in response.data:
                results.append(to_dict(instance))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Container Instances by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = container_instances_client.list_container_instances(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for instance in response.data:
            results.append(to_dict(instance))

        while response.has_next_page:
            response = container_instances_client.list_container_instances(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for instance in response.data:
                results.append(to_dict(instance))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Containers

```python
container_instance_id = "ocid1.containerinstance.oc1..."  # or from plan parameters

try:
    response = container_instances_client.list_containers(container_instance_id=container_instance_id)
    for container in response.data:
        results.append(to_dict(container))

    while response.has_next_page:
        response = container_instances_client.list_containers(container_instance_id=container_instance_id, page=response.next_page)
        for container in response.data:
            results.append(to_dict(container))
except oci.exceptions.ServiceError:
    pass  # Container instance not found or no access
```

### 4. List Containers by Lifecycle State

```python
container_instance_id = "ocid1.containerinstance.oc1..."  # or from plan parameters
lifecycle_state = "RUNNING"  # or from plan parameters

try:
    response = container_instances_client.list_containers(container_instance_id=container_instance_id)
    for container in response.data:
        if container.lifecycle_state == lifecycle_state:
            results.append(to_dict(container))

    while response.has_next_page:
        response = container_instances_client.list_containers(container_instance_id=container_instance_id, page=response.next_page)
        for container in response.data:
            if container.lifecycle_state == lifecycle_state:
                results.append(to_dict(container))
except oci.exceptions.ServiceError:
    pass  # Container instance not found or no access
```

### 5. List Container Instance Shapes

```python
for compartment in all_compartments:
    try:
        response = container_instances_client.list_container_instance_shapes(compartment_id=compartment.id)
        for shape in response.data:
            results.append(to_dict(shape))

        while response.has_next_page:
            response = container_instances_client.list_container_instance_shapes(compartment_id=compartment.id, page=response.next_page)
            for shape in response.data:
                results.append(to_dict(shape))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Containers require a specific container instance ID
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Container Instances resources are compartment-scoped


