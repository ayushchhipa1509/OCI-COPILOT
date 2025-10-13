# 📊 Analytics Service Patterns (`analytics`)

## Client Creation

```python
analytics_client = get_client('analytics', oci_config)
```

## Common Patterns

### 1. List Analytics Instances

```python
for compartment in all_compartments:
    try:
        response = analytics_client.list_analytics_instances(compartment_id=compartment.id)
        for instance in response.data:
            results.append(to_dict(instance))

        while response.has_next_page:
            response = analytics_client.list_analytics_instances(compartment_id=compartment.id, page=response.next_page)
            for instance in response.data:
                results.append(to_dict(instance))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Analytics Instances by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = analytics_client.list_analytics_instances(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for instance in response.data:
            results.append(to_dict(instance))

        while response.has_next_page:
            response = analytics_client.list_analytics_instances(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for instance in response.data:
                results.append(to_dict(instance))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Analytics Instances by Capacity Type

```python
capacity_type = "OLPU_COUNT"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = analytics_client.list_analytics_instances(compartment_id=compartment.id)
        for instance in response.data:
            if instance.capacity_type == capacity_type:
                results.append(to_dict(instance))

        while response.has_next_page:
            response = analytics_client.list_analytics_instances(compartment_id=compartment.id, page=response.next_page)
            for instance in response.data:
                if instance.capacity_type == capacity_type:
                    results.append(to_dict(instance))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Analytics Instances by License Type

```python
license_type = "ENTERPRISE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = analytics_client.list_analytics_instances(compartment_id=compartment.id)
        for instance in response.data:
            if instance.license_type == license_type:
                results.append(to_dict(instance))

        while response.has_next_page:
            response = analytics_client.list_analytics_instances(compartment_id=compartment.id, page=response.next_page)
            for instance in response.data:
                if instance.license_type == license_type:
                    results.append(to_dict(instance))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Capacity type and license type filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Analytics resources are compartment-scoped


