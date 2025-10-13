# 🔍 Audit Service Patterns (`audit`)

## Client Creation

```python
audit_client = get_client('audit', oci_config)
```

## Common Patterns

### 1. List Audit Events

```python
for compartment in all_compartments:
    try:
        response = audit_client.list_events(compartment_id=compartment.id)
        for event in response.data:
            results.append(to_dict(event))

        while response.has_next_page:
            response = audit_client.list_events(compartment_id=compartment.id, page=response.next_page)
            for event in response.data:
                results.append(to_dict(event))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Audit Events by Time Range

```python
start_time = "2024-01-01T00:00:00Z"  # or from plan parameters
end_time = "2024-01-02T00:00:00Z"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = audit_client.list_events(
            compartment_id=compartment.id,
            start_time=start_time,
            end_time=end_time
        )
        for event in response.data:
            results.append(to_dict(event))

        while response.has_next_page:
            response = audit_client.list_events(
                compartment_id=compartment.id,
                start_time=start_time,
                end_time=end_time,
                page=response.next_page
            )
            for event in response.data:
                results.append(to_dict(event))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Audit Events by Event Type

```python
event_type = "CreateInstance"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = audit_client.list_events(compartment_id=compartment.id)
        for event in response.data:
            if event.event_type == event_type:
                results.append(to_dict(event))

        while response.has_next_page:
            response = audit_client.list_events(compartment_id=compartment.id, page=response.next_page)
            for event in response.data:
                if event.event_type == event_type:
                    results.append(to_dict(event))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Audit Events by User

```python
user_name = "user@example.com"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = audit_client.list_events(compartment_id=compartment.id)
        for event in response.data:
            if event.identity and event.identity.user_name == user_name:
                results.append(to_dict(event))

        while response.has_next_page:
            response = audit_client.list_events(compartment_id=compartment.id, page=response.next_page)
            for event in response.data:
                if event.identity and event.identity.user_name == user_name:
                    results.append(to_dict(event))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Audit Events by Resource

```python
resource_name = "my-instance"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = audit_client.list_events(compartment_id=compartment.id)
        for event in response.data:
            if event.data and event.data.resource_name == resource_name:
                results.append(to_dict(event))

        while response.has_next_page:
            response = audit_client.list_events(compartment_id=compartment.id, page=response.next_page)
            for event in response.data:
                if event.data and event.data.resource_name == resource_name:
                    results.append(to_dict(event))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Time range filtering uses ISO 8601 format
- Event type filtering is done in code, not API
- User and resource filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Audit resources are compartment-scoped


