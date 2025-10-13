# 🏗️ Resource Manager Service Patterns (`resource_manager`)

## Client Creation

```python
resource_manager_client = get_client('resource_manager', oci_config)
```

## Common Patterns

### 1. List Stacks

```python
for compartment in all_compartments:
    try:
        response = resource_manager_client.list_stacks(compartment_id=compartment.id)
        for stack in response.data:
            results.append(to_dict(stack))

        while response.has_next_page:
            response = resource_manager_client.list_stacks(compartment_id=compartment.id, page=response.next_page)
            for stack in response.data:
                results.append(to_dict(stack))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Stacks by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = resource_manager_client.list_stacks(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for stack in response.data:
            results.append(to_dict(stack))

        while response.has_next_page:
            response = resource_manager_client.list_stacks(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for stack in response.data:
                results.append(to_dict(stack))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Jobs

```python
for compartment in all_compartments:
    try:
        response = resource_manager_client.list_jobs(compartment_id=compartment.id)
        for job in response.data:
            results.append(to_dict(job))

        while response.has_next_page:
            response = resource_manager_client.list_jobs(compartment_id=compartment.id, page=response.next_page)
            for job in response.data:
                results.append(to_dict(job))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Jobs by Lifecycle State

```python
lifecycle_state = "SUCCEEDED"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = resource_manager_client.list_jobs(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for job in response.data:
            results.append(to_dict(job))

        while response.has_next_page:
            response = resource_manager_client.list_jobs(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for job in response.data:
                results.append(to_dict(job))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Jobs by Operation

```python
operation = "PLAN"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = resource_manager_client.list_jobs(compartment_id=compartment.id)
        for job in response.data:
            if job.operation == operation:
                results.append(to_dict(job))

        while response.has_next_page:
            response = resource_manager_client.list_jobs(compartment_id=compartment.id, page=response.next_page)
            for job in response.data:
                if job.operation == operation:
                    results.append(to_dict(job))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Operation filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Resource Manager resources are compartment-scoped


