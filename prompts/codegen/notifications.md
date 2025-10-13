# 🔔 Notifications Service Patterns (`notifications`)

## Client Creation

```python
notifications_client = get_client('notifications', oci_config)
```

## Common Patterns

### 1. List Topics

```python
for compartment in all_compartments:
    try:
        response = notifications_client.list_topics(compartment_id=compartment.id)
        for topic in response.data:
            results.append(to_dict(topic))

        while response.has_next_page:
            response = notifications_client.list_topics(compartment_id=compartment.id, page=response.next_page)
            for topic in response.data:
                results.append(to_dict(topic))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Topics by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = notifications_client.list_topics(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for topic in response.data:
            results.append(to_dict(topic))

        while response.has_next_page:
            response = notifications_client.list_topics(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for topic in response.data:
                results.append(to_dict(topic))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Subscriptions

```python
for compartment in all_compartments:
    try:
        response = notifications_client.list_subscriptions(compartment_id=compartment.id)
        for subscription in response.data:
            results.append(to_dict(subscription))

        while response.has_next_page:
            response = notifications_client.list_subscriptions(compartment_id=compartment.id, page=response.next_page)
            for subscription in response.data:
                results.append(to_dict(subscription))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Subscriptions by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = notifications_client.list_subscriptions(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for subscription in response.data:
            results.append(to_dict(subscription))

        while response.has_next_page:
            response = notifications_client.list_subscriptions(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for subscription in response.data:
                results.append(to_dict(subscription))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Subscriptions by Protocol

```python
protocol = "EMAIL"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = notifications_client.list_subscriptions(compartment_id=compartment.id)
        for subscription in response.data:
            if subscription.protocol == protocol:
                results.append(to_dict(subscription))

        while response.has_next_page:
            response = notifications_client.list_subscriptions(compartment_id=compartment.id, page=response.next_page)
            for subscription in response.data:
                if subscription.protocol == protocol:
                    results.append(to_dict(subscription))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Protocol filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Notifications resources are compartment-scoped


