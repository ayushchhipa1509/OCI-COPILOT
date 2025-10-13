# 📅 Events Service Patterns (`events`)

## Client Creation

```python
events_client = get_client('events', oci_config)
```

## Common Patterns

### 1. List Rules

```python
for compartment in all_compartments:
    try:
        response = events_client.list_rules(compartment_id=compartment.id)
        for rule in response.data:
            results.append(to_dict(rule))

        while response.has_next_page:
            response = events_client.list_rules(compartment_id=compartment.id, page=response.next_page)
            for rule in response.data:
                results.append(to_dict(rule))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Rules by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = events_client.list_rules(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for rule in response.data:
            results.append(to_dict(rule))

        while response.has_next_page:
            response = events_client.list_rules(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for rule in response.data:
                results.append(to_dict(rule))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Rules by Event Type

```python
event_type = "com.oraclecloud.computeapi.launchinstance.end"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = events_client.list_rules(compartment_id=compartment.id)
        for rule in response.data:
            if rule.condition and rule.condition.event_type == event_type:
                results.append(to_dict(rule))

        while response.has_next_page:
            response = events_client.list_rules(compartment_id=compartment.id, page=response.next_page)
            for rule in response.data:
                if rule.condition and rule.condition.event_type == event_type:
                    results.append(to_dict(rule))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Rules by Action Type

```python
action_type = "FAAS"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = events_client.list_rules(compartment_id=compartment.id)
        for rule in response.data:
            if rule.actions and any(action.action_type == action_type for action in rule.actions):
                results.append(to_dict(rule))

        while response.has_next_page:
            response = events_client.list_rules(compartment_id=compartment.id, page=response.next_page)
            for rule in response.data:
                if rule.actions and any(action.action_type == action_type for action in rule.actions):
                    results.append(to_dict(rule))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Work Requests

```python
for compartment in all_compartments:
    try:
        response = events_client.list_work_requests(compartment_id=compartment.id)
        for work_request in response.data:
            results.append(to_dict(work_request))

        while response.has_next_page:
            response = events_client.list_work_requests(compartment_id=compartment.id, page=response.next_page)
            for work_request in response.data:
                results.append(to_dict(work_request))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Event type and action type filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Events resources are compartment-scoped


