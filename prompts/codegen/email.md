# 📧 Email Service Patterns (`email`)

## Client Creation

```python
email_client = get_client('email', oci_config)
```

## Common Patterns

### 1. List Senders

```python
for compartment in all_compartments:
    try:
        response = email_client.list_senders(compartment_id=compartment.id)
        for sender in response.data:
            results.append(to_dict(sender))

        while response.has_next_page:
            response = email_client.list_senders(compartment_id=compartment.id, page=response.next_page)
            for sender in response.data:
                results.append(to_dict(sender))
    except oci.exceptions.ServiceError:
        continue
```

### 2. List Senders by Lifecycle State

```python
lifecycle_state = "ACTIVE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = email_client.list_senders(
            compartment_id=compartment.id,
            lifecycle_state=lifecycle_state
        )
        for sender in response.data:
            results.append(to_dict(sender))

        while response.has_next_page:
            response = email_client.list_senders(
                compartment_id=compartment.id,
                lifecycle_state=lifecycle_state,
                page=response.next_page
            )
            for sender in response.data:
                results.append(to_dict(sender))
    except oci.exceptions.ServiceError:
        continue
```

### 3. List Suppressions

```python
for compartment in all_compartments:
    try:
        response = email_client.list_suppressions(compartment_id=compartment.id)
        for suppression in response.data:
            results.append(to_dict(suppression))

        while response.has_next_page:
            response = email_client.list_suppressions(compartment_id=compartment.id, page=response.next_page)
            for suppression in response.data:
                results.append(to_dict(suppression))
    except oci.exceptions.ServiceError:
        continue
```

### 4. List Suppressions by Email Address

```python
email_address = "user@example.com"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = email_client.list_suppressions(compartment_id=compartment.id)
        for suppression in response.data:
            if suppression.email_address == email_address:
                results.append(to_dict(suppression))

        while response.has_next_page:
            response = email_client.list_suppressions(compartment_id=compartment.id, page=response.next_page)
            for suppression in response.data:
                if suppression.email_address == email_address:
                    results.append(to_dict(suppression))
    except oci.exceptions.ServiceError:
        continue
```

### 5. List Suppressions by Reason

```python
reason = "BOUNCE"  # or from plan parameters

for compartment in all_compartments:
    try:
        response = email_client.list_suppressions(compartment_id=compartment.id)
        for suppression in response.data:
            if suppression.reason == reason:
                results.append(to_dict(suppression))

        while response.has_next_page:
            response = email_client.list_suppressions(compartment_id=compartment.id, page=response.next_page)
            for suppression in response.data:
                if suppression.reason == reason:
                    results.append(to_dict(suppression))
    except oci.exceptions.ServiceError:
        continue
```

## Key Points

- Use `lifecycle_state` parameter for filtering by state
- Email address and reason filtering is done in code, not API
- Always implement pagination for all list operations
- Handle service errors gracefully with try/except blocks
- Email resources are compartment-scoped


