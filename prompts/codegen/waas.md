# 🛡️ WAAS Service Patterns (`waas`)

## Client Creation

```python
waas_client = get_client('waas', oci_config)
```

## Common Patterns

### 1. List WAAS Policies

```python
for compartment in all_compartments:
    try:
        response = waas_client.list_waas_policies(compartment_id=compartment.id)
        for policy in response.data:
            results.append(to_dict(policy))

        while response.has_next_page:
            response = waas_client.list_waas_policies(compartment_id=compartment.id, page=response.next_page)
            for policy in response.data:
                results.append(to_dict(policy))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List WAAS Policies by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = waas_client.list_waas_policies(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for policy in response.data:
            results.append(to_dict(policy))

        while response.has_next_page:
            response = waas_client.list_waas_policies(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for policy in response.data:
                results.append(to_dict(policy))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List WAAS Policies by Domain

```python
domain = "example.com"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = waas_client.list_waas_policies(compartment_id=compartment.id)
        for policy in response.data:
            if policy.domain == domain:
                results.append(to_dict(policy))

        while response.has_next_page:
            response = waas_client.list_waas_policies(compartment_id=compartment.id, page=response.next_page)
            for policy in response.data:
                if policy.domain == domain:
                    results.append(to_dict(policy))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List WAAS Policies by Protection Mode

```python
protection_mode = "DETECTION"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = waas_client.list_waas_policies(compartment_id=compartment.id)
        for policy in response.data:
            if policy.protection_mode == protection_mode:
                results.append(to_dict(policy))

        while response.has_next_page:
            response = waas_client.list_waas_policies(compartment_id=compartment.id, page=response.next_page)
            for policy in response.data:
                if policy.protection_mode == protection_mode:
                    results.append(to_dict(policy))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Domain and protection mode filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- WAAS resources are compartment-scoped


