# 📝 Logging Service Patterns (`logging`)

## Client Creation

```python
logging_client = get_client('logging', oci_config)
```

## Common Patterns

### 1. List Log Groups

```python
for compartment in all_compartments:
    try:
        response = logging_client.list_log_groups(compartment_id=compartment.id)
        for log_group in response.data:
            results.append(to_dict(log_group))

        while response.has_next_page:
            response = logging_client.list_log_groups(compartment_id=compartment.id, page=response.next_page)
            for log_group in response.data:
                results.append(to_dict(log_group))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Logs

```python
log_group_id = "ocid1.loggroup.oc1..."  # or from plan parameters

try:
    response = logging_client.list_logs(log_group_id=log_group_id)
    for log in response.data:
        results.append(to_dict(log))

    while response.has_next_page:
        response = logging_client.list_logs(log_group_id=log_group_id, page=response.next_page)
        for log in response.data:
            results.append(to_dict(log))
except oci.exceptions.ServiceError:
    pass  # Log group not found or no access
```

### 3. List Logs by Lifecycle State

```python
log_group_id = "ocid1.loggroup.oc1..."  # or from plan parameters
lifecycle_state = "ACTIVE"  # or from plan parameters

try:
    response = logging_client.list_logs(
        log_group_id=log_group_id,
        lifecycle_state=lifecycle_state
    )
    for log in response.data:
        results.append(to_dict(log))

    while response.has_next_page:
        response = logging_client.list_logs(
            log_group_id=log_group_id,
            lifecycle_state=lifecycle_state,
            page=response.next_page
        )
        for log in response.data:
            results.append(to_dict(log))
except oci.exceptions.ServiceError:
    pass  # Log group not found or no access
```

### 4. List Log Entries

```python
log_id = "ocid1.log.oc1..."  # or from plan parameters

try:
    response = logging_client.list_log_entries(log_id=log_id)
    for entry in response.data:
        results.append(to_dict(entry))

    while response.has_next_page:
        response = logging_client.list_log_entries(log_id=log_id, page=response.next_page)
        for entry in response.data:
            results.append(to_dict(entry))
except oci.exceptions.ServiceError:
    pass  # Log not found or no access
```

### 5. List Log Entries with Time Range

```python
log_id = "ocid1.log.oc1..."  # or from plan parameters
start_time = "2024-01-01T00:00:00Z"  # or from plan parameters
end_time = "2024-01-02T00:00:00Z"  # or from plan parameters

try:
    response = logging_client.list_log_entries(
        log_id=log_id,
        time_start=start_time,
        time_end=end_time
    )
    for entry in response.data:
        results.append(to_dict(entry))

    while response.has_next_page:
        response = logging_client.list_log_entries(
            log_id=log_id,
            time_start=start_time,
            time_end=end_time,
            page=response.next_page
        )
        for entry in response.data:
            results.append(to_dict(entry))
except oci.exceptions.ServiceError:
    pass  # Log not found or no access
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Log entries require a specific log ID
- Time range filtering uses ISO 8601 format
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Logging resources are compartment-scoped


