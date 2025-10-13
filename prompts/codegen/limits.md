# 📊 Limits Service Patterns (`limits`)

## Client Creation

```python
limits_client = get_client('limits', oci_config)
```

## Common Patterns

### 1. List Service Limits

```python
for compartment in all_compartments:
    try:
        response = limits_client.list_limits(compartment_id=compartment.id)
        for limit in response.data:
            results.append(to_dict(limit))

        while response.has_next_page:
            response = limits_client.list_limits(compartment_id=compartment.id, page=response.next_page)
            for limit in response.data:
                results.append(to_dict(limit))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Service Limits by Service Name

```python
service_name = "compute"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = limits_client.list_limits(compartment_id=compartment.id)
        for limit in response.data:
            if limit.service_name == service_name:
                results.append(to_dict(limit))

        while response.has_next_page:
            response = limits_client.list_limits(compartment_id=compartment.id, page=response.next_page)
            for limit in response.data:
                if limit.service_name == service_name:
                    results.append(to_dict(limit))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Quotas

```python
for compartment in all_compartments:
    try:
        response = limits_client.list_quotas(compartment_id=compartment.id)
        for quota in response.data:
            results.append(to_dict(quota))

        while response.has_next_page:
            response = limits_client.list_quotas(compartment_id=compartment.id, page=response.next_page)
            for quota in response.data:
                results.append(to_dict(quota))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Quotas by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = limits_client.list_quotas(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for quota in response.data:
            results.append(to_dict(quota))

        while response.has_next_page:
            response = limits_client.list_quotas(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for quota in response.data:
                results.append(to_dict(quota))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Resource Availability

```python
for compartment in all_compartments:
    try:
        response = limits_client.list_resource_availability(compartment_id=compartment.id)
        for availability in response.data:
            results.append(to_dict(availability))

        while response.has_next_page:
            response = limits_client.list_resource_availability(compartment_id=compartment.id, page=response.next_page)
            for availability in response.data:
                results.append(to_dict(availability))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Service name filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Limits resources are compartment-scoped


